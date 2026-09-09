#!/usr/bin/env python3
"""Smoke test for AI schedule analysis parsing (mocks the HTTP call)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["OPENAI_API_KEY"] = "test-key-not-real"

from app.ai_schedule import (  # noqa: E402
    analyze_requirements_to_schedule,
    ai_configured,
)
from app.schemas import DEFAULT_PHASE_NAMES  # noqa: E402


def _fake_response(content: dict) -> MagicMock:
    res = MagicMock()
    res.status_code = 200
    res.json.return_value = {
        "choices": [{"message": {"content": json.dumps(content, ensure_ascii=False)}}]
    }
    res.text = "ok"
    return res


def test_maps_five_phases_and_jobs() -> None:
    payload = {
        "analysis": "需求覆盖登录与看板，按五阶段推进。",
        "phases": [
            {
                "name": name,
                "work_items": [
                    {
                        "title": f"{name}-任务A",
                        "estimated_hours": 4,
                        "suggested_job": "pm",
                    },
                    {
                        "title": f"{name}-任务B",
                        "estimated_hours": 2.5,
                        "suggested_job": "designer",
                    },
                ],
            }
            for name in DEFAULT_PHASE_NAMES
        ],
    }
    with patch("app.ai_schedule.httpx.Client") as client_cls:
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.post.return_value = _fake_response(payload)
        client_cls.return_value = client

        plan = analyze_requirements_to_schedule(
            project_name="试用项目",
            objective="做中台",
            requirements=["邮箱登录", "项目看板"],
            planned_start="2026-09-01",
            planned_end="2026-10-15",
            member_daily_hours=6.0,
            available_jobs=["pm", "designer", "ops"],
        )

    assert ai_configured() is True
    assert "登录" in plan.analysis or "看板" in plan.analysis or plan.analysis
    assert len(plan.phases) == len(DEFAULT_PHASE_NAMES)
    for phase, expected_name in zip(plan.phases, DEFAULT_PHASE_NAMES):
        assert phase.name == expected_name
        assert len(phase.work_items) >= 1
        assert phase.work_items[0].title
        assert 0.5 <= phase.work_items[0].estimated_hours <= 40


def test_fills_missing_phase_with_placeholder() -> None:
    payload = {
        "analysis": "部分阶段缺失时补默认项。",
        "phases": [
            {
                "name": DEFAULT_PHASE_NAMES[0],
                "work_items": [
                    {
                        "title": "启动会",
                        "estimated_hours": 1,
                        "suggested_job": None,
                    }
                ],
            }
        ],
    }
    with patch("app.ai_schedule.httpx.Client") as client_cls:
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.post.return_value = _fake_response(payload)
        client_cls.return_value = client
        plan = analyze_requirements_to_schedule(
            project_name="P",
            objective=None,
            requirements=[],
            planned_start="2026-09-01",
            planned_end="2026-09-30",
            member_daily_hours=6.0,
            available_jobs=[],
        )
    assert len(plan.phases) == len(DEFAULT_PHASE_NAMES)
    assert plan.phases[0].work_items[0].title == "启动会"
    assert any("关键推进" in p.work_items[0].title for p in plan.phases[1:])


def main() -> int:
    test_maps_five_phases_and_jobs()
    test_fills_missing_phase_with_placeholder()
    print("ai_schedule smoke tests: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
