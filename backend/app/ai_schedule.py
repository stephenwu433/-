"""AI-assisted cycle schedule analysis (OpenAI-compatible Chat Completions).

Env:
  OPENAI_API_KEY or PLANFLOW_AI_API_KEY  — required for AI mode
  PLANFLOW_AI_BASE_URL — default https://api.openai.com/v1
  PLANFLOW_AI_MODEL — default gpt-4o-mini
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.schemas import DEFAULT_PHASE_NAMES, JOB_TITLES


@dataclass
class AIWorkItem:
    title: str
    estimated_hours: float
    suggested_job: str | None = None


@dataclass
class AIPhasePlan:
    name: str
    work_items: list[AIWorkItem]


@dataclass
class AISchedulePlan:
    analysis: str
    phases: list[AIPhasePlan]


def ai_configured() -> bool:
    return bool(_api_key())


def _api_key() -> str | None:
    key = (
        os.getenv("PLANFLOW_AI_API_KEY", "").strip()
        or os.getenv("OPENAI_API_KEY", "").strip()
    )
    return key or None


def _base_url() -> str:
    raw = os.getenv("PLANFLOW_AI_BASE_URL", "").strip()
    return (raw or "https://api.openai.com/v1").rstrip("/")


def _model() -> str:
    return os.getenv("PLANFLOW_AI_MODEL", "").strip() or "gpt-4o-mini"


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def analyze_requirements_to_schedule(
    *,
    project_name: str,
    objective: str | None,
    requirements: list[str],
    planned_start: str,
    planned_end: str,
    member_daily_hours: float,
    available_jobs: list[str],
) -> AISchedulePlan:
    """Call an OpenAI-compatible model and return a structured schedule plan."""
    key = _api_key()
    if not key:
        raise RuntimeError("AI API key is not configured")

    jobs = [j for j in available_jobs if j in JOB_TITLES] or list(JOB_TITLES)
    phase_names = list(DEFAULT_PHASE_NAMES)
    req_block = "\n".join(f"- {r}" for r in requirements) or "- （未提供细分需求，请根据项目目标拆解）"

    system = (
        "你是资深项目经理与排期顾问。根据项目信息，分析需求并输出可执行的全周期排期。"
        "必须严格输出 JSON（不要 Markdown），结构如下：\n"
        "{"
        '"analysis":"一两句中文分析",'
        '"phases":[{"name":"阶段名","work_items":[{"title":"任务标题",'
        '"estimated_hours":数字,"suggested_job":"岗位英文key或null"}]}]'
        "}\n"
        f"phases 必须正好 {len(phase_names)} 个，且 name 依次为：{phase_names}。"
        f"suggested_job 只能是这些之一或 null：{jobs}。"
        "每个阶段 2～6 个 work_items；title 用中文、具体可执行；"
        "estimated_hours 为合理工时（0.5～40）。"
        "总工时要大致匹配项目周期与每日可用工时，不要空话。"
    )
    user = (
        f"项目名称：{project_name}\n"
        f"项目目标：{objective or '（未填写）'}\n"
        f"计划开始：{planned_start}\n"
        f"计划结束：{planned_end}\n"
        f"成员每日可用工时：{member_daily_hours}\n"
        f"可用岗位：{', '.join(jobs)}\n"
        f"需求条目：\n{req_block}\n"
        "请分析并生成排期 JSON。"
    )

    url = f"{_base_url()}/chat/completions"
    payload = {
        "model": _model(),
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=90.0) as client:
        res = client.post(url, headers=headers, json=payload)
        if res.status_code >= 400:
            raise RuntimeError(f"AI API error {res.status_code}: {res.text[:400]}")
        data = res.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"AI API returned unexpected payload: {data!r}") from exc

    parsed = _extract_json(content)
    analysis = str(parsed.get("analysis") or "").strip() or "已根据需求生成排期。"
    raw_phases = parsed.get("phases") or []
    if not isinstance(raw_phases, list) or not raw_phases:
        raise RuntimeError("AI response missing phases")

    by_name: dict[str, list[AIWorkItem]] = {n: [] for n in phase_names}
    for raw in raw_phases:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or "").strip()
        if name not in by_name:
            # Map unknown phase names onto fixed list by order if possible
            continue
        items_raw = raw.get("work_items") or []
        if not isinstance(items_raw, list):
            continue
        for item in items_raw:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            try:
                hours = float(item.get("estimated_hours") or 2.0)
            except (TypeError, ValueError):
                hours = 2.0
            hours = max(0.5, min(hours, 40.0))
            job = item.get("suggested_job")
            job_s = str(job).strip().lower() if job else None
            if job_s and job_s not in JOB_TITLES:
                job_s = None
            by_name[name].append(
                AIWorkItem(title=title[:200], estimated_hours=hours, suggested_job=job_s)
            )

    phases: list[AIPhasePlan] = []
    for name in phase_names:
        items = by_name.get(name) or []
        if not items:
            items = [
                AIWorkItem(
                    title=f"{name} · 关键推进",
                    estimated_hours=2.0,
                    suggested_job=None,
                )
            ]
        phases.append(AIPhasePlan(name=name, work_items=items[:8]))

    return AISchedulePlan(analysis=analysis[:1000], phases=phases)
