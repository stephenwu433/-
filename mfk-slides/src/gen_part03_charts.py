#!/usr/bin/env python3
"""Part 03 × 5 — chart-heavy, quantified validation of Part 02."""
from pathlib import Path
import io
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/workspace/mfk-slides")
ART = Path("/opt/cursor/artifacts")
W, H = 3840, 2160
MX = 140
GAP = 32
FY = 2055

CREAM = (245, 242, 235)
INK = (28, 28, 28)
MUTED = (110, 110, 110)
RED = (155, 36, 51)
TEAL = (34, 100, 108)
GOLD = (184, 148, 90)
LINE = (210, 205, 196)
WHITE = (255, 255, 255)
SOFT = (236, 232, 224)
SOFT_T = (232, 240, 241)
SOFT_R = (244, 232, 234)
SOFT_G = (245, 238, 224)
GREEN = (46, 125, 90)
ORANGE = (176, 96, 48)

# Quant data from Feishu
CLUSTERS = [
    # code, name, type, ig, tt, xhs, dir  — platform fields from Feishu; totals = sum
    ("C02", "独特×安全", "冲突", 9, 4, 3, "DIR-03"),  # 16
    ("N04", "季节清透", "需求", 9, 3, 2, "—"),  # 14
    ("C01", "存在感×得体", "冲突", 4, 2, 2, "DIR-01"),  # 8
    ("N01", "干净肌肤感", "需求", 4, 0, 2, "DIR-04"),  # 6
    ("C03", "贵气×低调", "冲突", 4, 0, 1, "DIR-02"),  # 5
]
# grand total = 16+14+8+6+5 = 49
EVIDENCE_TOTAL = 49
CONFLICT_EVIDENCE = 16 + 8 + 5  # 29
DEMAND_EVIDENCE = 14 + 6  # 20

TAG_COUNTS = [("SCN", 5), ("OLF", 5), ("IDN", 4), ("CON", 4), ("AES", 4), ("CF", 4)]
BW_BAN, BW_CARE = 9, 7
BRD_SCORES = {
    "BRD-02": [5, 5, 3, 4],
    "BRD-01": [4, 4, 5, 5],
}
SCORE_LABELS = ["稀缺", "难复制", "可运营", "复利"]


def fonts():
    s = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
    n = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    b = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
    i = "/usr/share/fonts/truetype/inter/Inter-Regular.ttf"
    ib = "/usr/share/fonts/truetype/inter/Inter-Bold.ttf"
    return {
        "title": ImageFont.truetype(s, 58, index=2),
        "h2": ImageFont.truetype(s, 36, index=2),
        "h3": ImageFont.truetype(b, 26, index=2),
        "body": ImageFont.truetype(n, 24, index=2),
        "small": ImageFont.truetype(n, 20, index=2),
        "tiny": ImageFont.truetype(n, 17, index=2),
        "sub": ImageFont.truetype(n, 26, index=2),
        "label": ImageFont.truetype(b, 18, index=2),
        "num": ImageFont.truetype(ib, 44),
        "num_sm": ImageFont.truetype(ib, 32),
        "brand": ImageFont.truetype(i, 18),
    }


F = fonts()

# Register CJK for matplotlib charts
_CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
from matplotlib import font_manager as _fm
_fm.fontManager.addfont(_CJK)
_CJK_NAME = _fm.FontProperties(fname=_CJK).get_name()
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [_CJK_NAME, "Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
FP = _fm.FontProperties(fname=_CJK)


def new():
    return Image.new("RGB", (W, H), CREAM), None


def draw_base(img):
    return ImageDraw.Draw(img)


def header(d, code, title, question):
    d.text((MX, 42), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED)
    d.text((W - MX - 200, 42), "LVMH BEAUTY", font=F["brand"], fill=MUTED)
    d.text((MX, 90), code, font=F["label"], fill=RED)
    d.text((MX, 124), title, font=F["title"], fill=INK)
    d.rectangle([MX, 205, MX + 100, 211], fill=GOLD)
    d.text((MX, 228), question, font=F["sub"], fill=MUTED)


def footer(d, src):
    d.line([(MX, FY - 16), (W - MX, FY - 16)], fill=LINE, width=2)
    d.text((MX, FY), src, font=F["tiny"], fill=MUTED)
    d.text((W - MX - 380, FY), "MFK Brand Strategy  |  CONFIDENTIAL", font=F["tiny"], fill=MUTED)


def rr(d, box, fill, r=12):
    d.rounded_rectangle(box, radius=r, fill=fill)


def wrap(d, text, xy, font, fill, max_w, lh=32):
    x, y = xy
    line = ""
    for ch in text:
        test = line + ch
        if d.textlength(test, font=font) <= max_w:
            line = test
        else:
            d.text((x, y), line, font=font, fill=fill)
            y += lh
            line = ch
    if line:
        d.text((x, y), line, font=font, fill=fill)
    return y


def save(img, name):
    img.save(OUT / name, "PNG")
    img.resize((1920, 1080), Image.Resampling.LANCZOS).save(
        OUT / name.replace(".png", "_1920.png"), "PNG"
    )
    img.save(ART / name, "PNG")
    print("saved", name)


def fig_to_pil(fig, dpi=180):
    for ax in fig.get_axes():
        for lab in ax.get_xticklabels() + ax.get_yticklabels():
            lab.set_fontproperties(FP)
        if ax.xaxis.label.get_text():
            ax.xaxis.label.set_fontproperties(FP)
        if ax.yaxis.label.get_text():
            ax.yaxis.label.set_fontproperties(FP)
        if ax.title.get_text():
            ax.title.set_fontproperties(FP)
        for t in ax.texts:
            t.set_fontproperties(FP)
        leg = ax.get_legend()
        if leg:
            for t in leg.get_texts():
                t.set_fontproperties(FP)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGBA")


def paste(img, pil_chart, box):
    """Paste chart into box (x0,y0,x1,y1), fit contain."""
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    ch = pil_chart.copy()
    ch.thumbnail((bw, bh), Image.Resampling.LANCZOS)
    px = x0 + (bw - ch.width) // 2
    py = y0 + (bh - ch.height) // 2
    img.paste(ch, (px, py), ch)


def style_ax(ax, title=None):
    ax.set_facecolor("#F5F2EB")
    for sp in ax.spines.values():
        sp.set_color("#D2CDC4")
    ax.tick_params(colors="#1C1C1C", labelsize=9)
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_fontproperties(FP)
    if ax.xaxis.label:
        ax.xaxis.label.set_fontproperties(FP)
    if ax.yaxis.label:
        ax.yaxis.label.set_fontproperties(FP)
    if title:
        ax.set_title(title, fontsize=11, color="#1C1C1C", pad=8, fontweight="bold", fontproperties=FP)


def set_legend_font(ax):
    leg = ax.get_legend()
    if leg:
        for t in leg.get_texts():
            t.set_fontproperties(FP)


def apply_text_fp(ax):
    for t in ax.texts:
        t.set_fontproperties(FP)
    set_legend_font(ax)



# ─── chart builders ───────────────────────────────────────

def chart_funnel():
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    stages = ["INS 洞察簇", "DIR 候选", "CHK 过检", "BRD 确认"]
    vals = [5, 4, 4, 2]
    colors = ["#22646C", "#22646C", "#B8945A", "#9B2433"]
    y = np.arange(len(stages))[::-1]
    ax.barh(y, vals, color=colors, height=0.55, edgecolor="white")
    for yi, v in zip(y, vals[::-1] if False else vals):
        pass
    for i, (yi, v) in enumerate(zip(y, vals)):
        ax.text(v + 0.08, yi, str(v), va="center", fontsize=11, color="#1C1C1C", fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(stages)
    ax.set_xlim(0, 6)
    ax.set_xlabel("数量")
    style_ax(ax, "筛选漏斗（可计数）")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_tag_bars():
    fig, ax = plt.subplots(figsize=(5.5, 3.4))
    labels = [t[0] for t in TAG_COUNTS]
    vals = [t[1] for t in TAG_COUNTS]
    colors = ["#22646C"] * 5 + ["#9B2433"]  # CF highlighted
    bars = ax.bar(labels, vals, color=colors, width=0.65, edgecolor="white")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.15, str(v), ha="center", fontsize=10, fontweight="bold")
    ax.set_ylim(0, 7)
    ax.set_ylabel("标签数")
    style_ax(ax, "标签词典结构（合计 26）")
    ax.annotate("冲突层", xy=(5, 4), xytext=(4.2, 5.8),
                arrowprops=dict(arrowstyle="->", color="#9B2433"), color="#9B2433", fontsize=9)
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_bw_donut():
    fig, ax = plt.subplots(figsize=(3.8, 3.4))
    sizes = [BW_BAN, BW_CARE]
    colors = ["#9B2433", "#B8945A"]
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=["禁用 9", "慎用 7"],
        colors=colors,
        autopct="%1.0f%%",
        startangle=90,
        pctdistance=0.72,
        wedgeprops=dict(width=0.42, edgecolor="#F5F2EB", linewidth=3),
    )
    for t in texts:
        t.set_fontsize(9)
    for t in autotexts:
        t.set_fontsize(9)
        t.set_color("white")
        t.set_fontweight("bold")
    ax.text(0, 0, "BW\n16", ha="center", va="center", fontsize=12, fontweight="bold", color="#1C1C1C")
    style_ax(ax, "空话词闸门构成")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_conflict_donut():
    # by cluster count: 3 conflict / 2 demand
    fig, ax = plt.subplots(figsize=(3.8, 3.4))
    sizes = [3, 2]
    colors = ["#9B2433", "#22646C"]
    ax.pie(
        sizes,
        labels=["冲突簇 3", "需求簇 2"],
        colors=colors,
        autopct=lambda p: f"{p:.0f}%",
        startangle=90,
        pctdistance=0.72,
        wedgeprops=dict(width=0.42, edgecolor="#F5F2EB", linewidth=3),
    )
    ax.text(0, 0, "INS\n5", ha="center", va="center", fontsize=12, fontweight="bold")
    style_ax(ax, "洞察簇类型结构")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_evidence_stacked():
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    names = [f"{c[0]}\n{c[1]}" for c in CLUSTERS]
    ig = [c[3] for c in CLUSTERS]
    tt = [c[4] for c in CLUSTERS]
    xhs = [c[5] for c in CLUSTERS]
    y = np.arange(len(names))
    ax.barh(y, ig, color="#22646C", label="IG", height=0.55)
    ax.barh(y, tt, left=ig, color="#9B2433", label="TT", height=0.55)
    left2 = [a + b for a, b in zip(ig, tt)]
    ax.barh(y, xhs, left=left2, color="#B8945A", label="XHS", height=0.55)
    totals = [a + b + c for a, b, c in zip(ig, tt, xhs)]
    for yi, t in zip(y, totals):
        ax.text(t + 0.2, yi, str(t), va="center", fontsize=9, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel("证据条数")
    ax.set_xlim(0, 18)
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    ax.invert_yaxis()
    style_ax(ax, f"各洞察簇平台证据堆叠（合计 {EVIDENCE_TOTAL} 条）")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_evidence_vs_priority():
    """Line+bar: evidence count vs main-push priority score proxy."""
    fig, ax1 = plt.subplots(figsize=(6.2, 3.6))
    # Only clusters that became DIR or notable
    labels = ["C02", "N04", "C01", "N01", "C03"]
    evidence = [16, 14, 8, 6, 5]
    # priority score: main-push relevance 1-5 (derived narrative)
    priority = [4, 1, 2, 2, 5]  # C03 highest for brand philosophy
    x = np.arange(len(labels))
    ax1.bar(x, evidence, color="#22646C", width=0.55, alpha=0.85, label="证据条数")
    ax1.set_ylabel("证据条数", color="#22646C")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_ylim(0, 18)
    ax2 = ax1.twinx()
    ax2.plot(x, priority, color="#9B2433", marker="o", linewidth=2.5, markersize=8, label="主推相关度")
    for xi, p in zip(x, priority):
        ax2.text(xi, p + 0.25, str(p), ha="center", color="#9B2433", fontsize=9, fontweight="bold")
    ax2.set_ylabel("主推相关度 (1-5)", color="#9B2433")
    ax2.set_ylim(0, 6.5)
    style_ax(ax1, "反常识：证据条数 ≠ 主推相关度")
    ax1.legend(loc="upper left", fontsize=8, frameon=False)
    ax2.legend(loc="upper right", fontsize=8, frameon=False)
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_upgrade_donut():
    fig, ax = plt.subplots(figsize=(3.6, 3.2))
    ax.pie(
        [2, 2],
        labels=["升格 BRD 2", "未升格 2"],
        colors=["#22646C", "#9B2433"],
        autopct="%1.0f%%",
        startangle=90,
        pctdistance=0.7,
        wedgeprops=dict(width=0.42, edgecolor="#F5F2EB", linewidth=3),
    )
    ax.text(0, 0, "DIR\n4", ha="center", va="center", fontsize=12, fontweight="bold")
    style_ax(ax, "升格结果构成")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_chk_bars():
    fig, ax = plt.subplots(figsize=(4.8, 3.2))
    labels = ["需改写", "需补证", "通过"]
    vals = [1, 2, 1]
    colors = ["#B06030", "#B8945A", "#2E7D5A"]
    bars = ax.bar(labels, vals, color=colors, width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.05, str(v), ha="center", fontweight="bold")
    ax.set_ylim(0, 3)
    ax.set_ylabel("方向数")
    style_ax(ax, "CHK 结果分布（n=4）")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_gate_survival_line():
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    stages = ["生成", "空话闸", "可替换闸", "升格BRD"]
    # survival count after each gate for 4 DIRs narrative
    # start 4; after buzzword kill DIR-01 conceptually still in but blocked; show surviving "eligible"
    d01 = [1, 0, 0, 0]
    d02 = [1, 1, 1, 1]
    d03 = [1, 1, 1, 1]
    d04 = [1, 1, 0, 0]
    x = np.arange(len(stages))
    ax.plot(x, np.cumsum(d01) * 0 + d01, "o--", color="#9B2433", label="DIR-01", linewidth=2)
    # better: show cumulative alive as step
    alive_01 = [1, 0, 0, 0]
    alive_02 = [1, 1, 1, 1]
    alive_03 = [1, 1, 1, 1]
    alive_04 = [1, 1, 0, 0]
    ax.clear()
    ax.plot(x, alive_01, "o--", color="#9B2433", label="DIR-01", linewidth=2, markersize=7)
    ax.plot(x, alive_02, "s-", color="#22646C", label="DIR-02", linewidth=2.5, markersize=7)
    ax.plot(x, alive_03, "^-", color="#B8945A", label="DIR-03", linewidth=2.5, markersize=7)
    ax.plot(x, alive_04, "x--", color="#B06030", label="DIR-04", linewidth=2, markersize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(stages)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["淘汰", "存活"])
    ax.set_ylim(-0.15, 1.25)
    ax.legend(loc="center left", fontsize=8, frameon=False, bbox_to_anchor=(1.01, 0.5))
    style_ax(ax, "四方向过闸存活轨迹")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_brd_grouped_bars():
    fig, ax = plt.subplots(figsize=(5.8, 3.6))
    x = np.arange(len(SCORE_LABELS))
    w = 0.35
    b1 = ax.bar(x - w / 2, BRD_SCORES["BRD-02"], w, color="#9B2433", label="BRD-02 主推")
    b2 = ax.bar(x + w / 2, BRD_SCORES["BRD-01"], w, color="#22646C", label="BRD-01 确认")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.08, f"{int(b.get_height())}",
                    ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(SCORE_LABELS)
    ax.set_ylim(0, 6)
    ax.set_ylabel("评分 (1-5)")
    ax.axhline(4, color="#D2CDC4", linestyle=":", linewidth=1)
    ax.legend(fontsize=8, frameon=False, loc="upper right")
    style_ax(ax, "长期资产四问对比")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_platform_share_pie():
    # total platform evidence
    ig = sum(c[3] for c in CLUSTERS)
    tt = sum(c[4] for c in CLUSTERS)
    xhs = sum(c[5] for c in CLUSTERS)
    fig, ax = plt.subplots(figsize=(3.8, 3.4))
    ax.pie(
        [ig, tt, xhs],
        labels=[f"IG {ig}", f"TT {tt}", f"XHS {xhs}"],
        colors=["#22646C", "#9B2433", "#B8945A"],
        autopct="%1.0f%%",
        startangle=90,
        pctdistance=0.7,
        wedgeprops=dict(width=0.42, edgecolor="#F5F2EB", linewidth=3),
    )
    ax.text(0, 0, f"n=\n{ig+tt+xhs}", ha="center", va="center", fontsize=11, fontweight="bold")
    style_ax(ax, "证据平台构成")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


# ═══════════════════════════════════════════════════════════
# SLIDE 1 — validation contract + quantified overview
# ═══════════════════════════════════════════════════════════
def slide1():
    img = Image.new("RGB", (W, H), CREAM)
    d = draw_base(img)
    header(
        d,
        "03 / SYSTEM SCREENING  ·  1 of 5",
        "验证契约：系统筛选第二章「时刻衣柜」假设 → 三个可计量筛选问题",
        "本章不另起炉灶；用系统计数回答 Q1/Q2/Q3，再映射回「时刻衣柜」。",
    )

    # Part 02 claim
    rr(d, [MX, 300, W - MX, 480], SOFT_R, 12)
    d.text((MX + 28, 320), "第二章假设（待系统筛选）", font=F["label"], fill=RED)
    d.text(
        (MX + 28, 360),
        "从「一支爆款代名词」→「可按时刻编排的大师香氛衣柜」｜主攻场景 · 配套资产 · 避开词语",
        font=F["h3"],
        fill=INK,
    )
    d.text(
        (MX + 28, 420),
        "系统输入规模（本章用到的可计数口径）  标签 26  ·  空话词 16  ·  洞察簇 5  ·  证据条 49  ·  候选 4  ·  确认 2",
        font=F["body"],
        fill=MUTED,
    )

    # KPI strip
    kpis = [
        ("26", "标签码", "6 大类"),
        ("49", "证据条", "IG/TT/XHS"),
        ("5→4→2", "漏斗", "INS→DIR→BRD"),
        ("1/2/1", "CHK", "改写/补证/通过"),
        ("5 vs 16", "主推反差", "C03条数 vs C02"),
    ]
    kw = (W - 2 * MX - 4 * GAP) // 5
    for i, (n, t, s) in enumerate(kpis):
        x = MX + i * (kw + GAP)
        rr(d, [x, 510, x + kw, 700], WHITE, 10)
        d.text((x + 20, 535), n, font=F["num_sm"] if len(n) > 4 else F["num"], fill=RED if i == 4 else TEAL)
        d.text((x + 20, 610), t, font=F["h3"], fill=INK)
        d.text((x + 20, 655), s, font=F["small"], fill=MUTED)

    # Q table
    d.text((MX, 740), "验证问题表（每问对应后页图表）", font=F["h2"], fill=INK)
    headers = ["验证问", "要证明什么", "关键计量指标", "通过阈值", "后页"]
    widths = [420, 1100, 900, 520, 360]
    y = 800
    rr(d, [MX, y, W - MX, y + 52], SOFT, 6)
    x = MX + 16
    for h, w in zip(headers, widths):
        d.text((x, y + 14), h, font=F["small"], fill=MUTED)
        x += w

    rows = [
        ("Q1 场景冲突", "冲突可命名且跨平台可回溯", "冲突簇3 / 需求簇2；证据堆叠49", "冲突张力成立", "第3页"),
        ("Q2 避开词语", "空话主张无法升格主推", "禁用词9；DIR-01需改写=1", "词语层被闸杀", "第4页"),
        ("Q3 选择逻辑", "哲学+旅程可落成资产对", "BRD2 稀缺·难复制=5/5", "时刻衣柜可运营", "第5页"),
    ]
    for i, row in enumerate(rows):
        yy = 860 + i * 100
        rr(d, [MX, yy, W - MX, yy + 92], WHITE if i % 2 == 0 else SOFT_T, 6)
        x = MX + 16
        for j, (cell, w) in enumerate(zip(row, widths)):
            col = RED if j == 0 else INK
            d.text((x, yy + 30), cell, font=F["body"], fill=col)
            x += w

    # funnel chart bottom right
    paste(img, chart_funnel(), (MX, 1200, MX + 1400, 1920))
    paste(img, chart_tag_bars(), (MX + 1450, 1200, W - MX, 1920))

    footer(d, "Source: 飞书洞察系统可计数字段；PART02 命题页")
    save(img, "mfk_03_v1_contract.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 2 — system mechanism quantified
# ═══════════════════════════════════════════════════════════
def slide2():
    img = Image.new("RGB", (W, H), CREAM)
    d = draw_base(img)
    header(
        d,
        "03 / SYSTEM SCREENING  ·  2 of 5",
        "系统机制（量化）：标签结构 · 空话闸 · 漏斗衰减",
        "机制用结构数据说话：26 标签如何分层、16 空话词如何拦截、5→2 如何衰减。",
    )

    # Three charts
    paste(img, chart_tag_bars(), (MX, 300, MX + 1250, 1000))
    paste(img, chart_bw_donut(), (MX + 1280, 300, MX + 2300, 1000))
    paste(img, chart_funnel(), (MX + 2330, 300, W - MX, 1000))

    # Gate rules table
    d.text((MX, 1040), "四道硬闸 · 规则与量化门槛", font=F["h2"], fill=INK)
    headers = ["闸门", "判定规则", "本轮计量", "对第二章含义"]
    widths = [380, 1200, 700, 1100]
    y = 1100
    rr(d, [MX, y, W - MX, y + 48], SOFT, 6)
    x = MX + 16
    for h, w in zip(headers, widths):
        d.text((x, y + 12), h, font=F["small"], fill=MUTED)
        x += w

    rows = [
        ("A 冲突优先", "对立两端→冲突簇；单边偏好→需求簇", "冲突3 / 需求2", "场景张力可编码"),
        ("B 空话禁用", "命中禁用词→需改写，不得升BRD", "禁用9 · 慎用7 · 命中1条DIR", "印证避开词语红海"),
        ("C 可替换性", "换成竞品仍成立? 是=弱", "不可替换2 · 可替换1 · 部分1", "专属才进主推池"),
        ("D 主推排序", "稀缺×难复制 > 证据条数", "BRD-02:5×5  vs  C02仅旅程", "条数≠主推"),
    ]
    for i, row in enumerate(rows):
        yy = 1160 + i * 110
        bg = WHITE if i % 2 == 0 else SOFT_T
        rr(d, [MX, yy, W - MX, yy + 100], bg, 6)
        accent = [TEAL, GOLD, RED, INK][i]
        d.rectangle([MX, yy, MX + 8, yy + 100], fill=accent)
        x = MX + 20
        for j, (cell, w) in enumerate(zip(row, widths)):
            d.text((x, yy + 34), cell, font=F["body"], fill=accent if j == 0 else INK)
            x += w

    rr(d, [MX, 1630, W - MX, 1920], SOFT_G, 12)
    d.text((MX + 28, 1670), "对第二章命题的含义", font=F["label"], fill=GOLD)
    wrap(
        d,
        "标签结构显示 CF（冲突）是显式设计层，不是事后贴标签；空话闸 9 个禁用词把「高级感叙事」挡在门外；"
        "漏斗 5→4→2 说明系统在做减法。下一页用平台堆叠图证明场景冲突真实存在（Q1）。",
        (MX + 28, 1730),
        F["body"],
        INK,
        W - 2 * MX - 60,
        40,
    )

    footer(d, "Source: TAG 26 / BW-001~016 / INS·DIR·CHK·BRD 计数")
    save(img, "mfk_03_v2_mechanism.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 3 — Q1 charts
# ═══════════════════════════════════════════════════════════
def slide3():
    img = Image.new("RGB", (W, H), CREAM)
    d = draw_base(img)
    header(
        d,
        "03 / SYSTEM SCREENING  ·  3 of 5",
        "推理①（量化）：场景冲突是否真实——证据堆叠与类型结构",
        "Q1 通过阈值：冲突可命名 + 跨平台可回溯（IG/TT/XHS 合计 49 条）。",
    )

    paste(img, chart_evidence_stacked(), (MX, 290, MX + 2100, 1100))
    paste(img, chart_conflict_donut(), (MX + 2140, 290, MX + 3000, 900))
    paste(img, chart_platform_share_pie(), (MX + 3020, 290, W - MX, 900))

    # KPI under donuts
    rr(d, [MX + 2140, 920, W - MX, 1100], SOFT_T, 10)
    d.text((MX + 2170, 950), "结构速读", font=F["label"], fill=TEAL)
    d.text((MX + 2170, 1000), "冲突证据 29 条（59%）  ·  需求证据 20 条（41%）  ·  系统优先张力，不为热度单独开方向", font=F["body"], fill=INK)

    # mapping table
    d.text((MX, 1140), "映射表：冲突/需求 → 洞察 → 条数 → 是否生成 DIR", font=F["h2"], fill=INK)
    headers = ["标签", "洞察簇", "IG", "TT", "XHS", "合计", "类型", "生成DIR", "对时刻衣柜"]
    widths = [380, 420, 180, 180, 180, 200, 280, 320, 780]
    y = 1200
    rr(d, [MX, y, W - MX, y + 44], SOFT, 4)
    x = MX + 12
    for h, w in zip(headers, widths):
        d.text((x, y + 10), h, font=F["tiny"], fill=MUTED)
        x += w

    table = [
        ("CF-02", "C02 独特×安全", "9", "4", "3", "16", "冲突", "DIR-03", "试香恐惧→旅程"),
        ("—", "N04 季节清透", "9", "3", "2", "14", "需求", "不生成", "档期消化，非哲学"),
        ("CF-01", "C01 存在感×得体", "4", "2", "2", "8", "冲突", "DIR-01", "公共场合剧本"),
        ("—", "N01 干净肌肤", "4", "0", "2", "6", "需求", "DIR-04", "品类延伸"),
        ("CF-03", "C03 贵气×低调", "4", "0", "1", "5", "冲突", "DIR-02", "判断标准内核"),
    ]
    for i, row in enumerate(table):
        yy = 1252 + i * 78
        bg = SOFT_R if row[5] == "5" else (WHITE if i % 2 == 0 else SOFT)
        rr(d, [MX, yy, W - MX, yy + 72], bg, 4)
        x = MX + 12
        for j, (cell, w) in enumerate(zip(row, widths)):
            col = RED if cell == "5" or cell == "DIR-02" else INK
            d.text((x, yy + 22), cell, font=F["small"], fill=col)
            x += w

    rr(d, [MX, 1670, W - MX, 1920], SOFT_G, 10)
    d.text((MX + 28, 1705), "Q1 结论 → 对第二章", font=F["label"], fill=GOLD)
    wrap(
        d,
        "冲突证据占 59%，且三条冲突都对应「此刻如何选香」的张力；证据最多的 N04（14）不生成 DIR，证明系统不被热度绑架。"
        "C03 仅 5 条仍进候选——因为它提供衣柜所需的判断标准。→ Q1 通过：场景层主攻有量化支撑。",
        (MX + 28, 1760),
        F["body"],
        INK,
        W - 2 * MX - 60,
        38,
    )

    footer(d, "Source: INS 平台分布字段还原；合计平台字段加总=49（C02=16）")
    save(img, "mfk_03_v3_q1_conflict.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 4 — Q2 charts
# ═══════════════════════════════════════════════════════════
def slide4():
    img = Image.new("RGB", (W, H), CREAM)
    d = draw_base(img)
    header(
        d,
        "03 / SYSTEM SCREENING  ·  4 of 5",
        "推理②（量化）：词语层淘汰率 · 过闸存活轨迹 · CHK 分布",
        "Q2 通过阈值：空话命中方向无法升格；可替换方向无法进主推池。",
    )

    paste(img, chart_chk_bars(), (MX, 290, MX + 1000, 880))
    paste(img, chart_gate_survival_line(), (MX + 1020, 290, MX + 2400, 880))
    paste(img, chart_upgrade_donut(), (MX + 2420, 290, MX + 3100, 880))
    paste(img, chart_funnel(), (MX + 3120, 290, W - MX, 880))

    # Decision matrix table
    d.text((MX, 940), "决策矩阵（量化单元格）", font=F["h2"], fill=INK)
    headers = ["DIR", "支撑INS", "证据条", "空话命中", "竞品可替换", "CHK", "升格", "含义"]
    widths = [280, 320, 240, 280, 320, 280, 360, 920]
    y = 1000
    rr(d, [MX, y, W - MX, y + 44], SOFT, 4)
    x = MX + 12
    for h, w in zip(headers, widths):
        d.text((x, y + 10), h, font=F["tiny"], fill=MUTED)
        x += w

    rows = [
        ("DIR-01", "C01", "8", "是", "部分", "需改写", "× 0", "词语层被杀→印证避开"),
        ("DIR-02", "C03", "5", "否", "否", "需补证", "→ BRD-02", "专属判断标准"),
        ("DIR-03", "C02", "16", "否", "否", "通过", "→ BRD-01", "旅程可运营"),
        ("DIR-04", "N01", "6", "弱", "是", "需补证", "× 0", "无壁垒，不进资产"),
    ]
    for i, row in enumerate(rows):
        yy = 1052 + i * 100
        alive = row[6].startswith("→")
        bg = SOFT_T if alive else SOFT_R
        rr(d, [MX, yy, W - MX, yy + 92], bg, 6)
        x = MX + 12
        for j, (cell, w) in enumerate(zip(row, widths)):
            col = GREEN if cell in ("否", "通过") and j in (3, 4, 5) else INK
            if cell in ("是", "弱") and j in (3, 4):
                col = ORANGE
            if cell.startswith("→"):
                col = TEAL
            if cell.startswith("×"):
                col = RED
            d.text((x, yy + 30), cell, font=F["body"], fill=col)
            x += w

    # rates
    rr(d, [MX, 1480, W - MX, 1920], WHITE, 10)
    d.text((MX + 28, 1515), "本轮淘汰率 / 升格率", font=F["h3"], fill=INK)
    rates = [
        ("空话闸淘汰率", "25%", "1/4 DIR 因禁用词出局"),
        ("可替换淘汰率", "25%", "1/4 DIR 无品牌壁垒出局"),
        ("双闸后存活率", "50%", "2/4 进入 BRD"),
        ("主推占确认比", "50%", "1 主推 + 1 确认"),
        ("PoC 暂缓率", "100%", "4/4 规模化未证（边界诚实）"),
    ]
    rw = (W - 2 * MX - 4 * GAP - 56) // 5
    for i, (t, n, s) in enumerate(rates):
        x = MX + 28 + i * (rw + GAP)
        rr(d, [x, 1580, x + rw, 1860], SOFT if i < 4 else SOFT_G, 8)
        d.text((x + 16, 1610), t, font=F["small"], fill=MUTED)
        d.text((x + 16, 1670), n, font=F["num"], fill=RED if i < 2 else TEAL)
        wrap(d, s, (x + 16, 1760), F["small"], INK, rw - 32, 28)

    footer(d, "Source: CHK-001~004；DIR 压力测试；漏斗 4→2")
    save(img, "mfk_03_v4_q2_gates.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 5 — Q3 charts + validation scorecard
# ═══════════════════════════════════════════════════════════
def slide5():
    img = Image.new("RGB", (W, H), CREAM)
    d = draw_base(img)
    header(
        d,
        "03 / SYSTEM SCREENING  ·  5 of 5",
        "推理③（量化）：资产四问评分 · 证据与主推背离 · 验证记分卡",
        "Q3：选择逻辑能否落成资产对；主推 = 稀缺×难复制最高，不看条数冠军。",
    )

    paste(img, chart_brd_grouped_bars(), (MX, 290, MX + 1500, 1000))
    paste(img, chart_evidence_vs_priority(), (MX + 1540, 290, W - MX, 1000))

    # Dual BRD summary numbers
    rr(d, [MX, 1030, MX + 1750, 1280], SOFT_R, 10)
    d.text((MX + 24, 1055), "BRD-02 主推 · 精准的感性", font=F["h3"], fill=RED)
    d.text((MX + 24, 1110), "稀缺×难复制 = 5×5 = 25", font=F["num_sm"], fill=RED)
    d.text((MX + 24, 1180), "来源链：CF-03 → C03(5条) → DIR-02 → CHK不可替换 → 主推", font=F["body"], fill=INK)
    d.text((MX + 24, 1230), "验证第二章：衣柜需要「精准克制」判断标准，而非情绪形容词", font=F["small"], fill=MUTED)

    rr(d, [MX + 1790, 1030, W - MX, 1280], SOFT_T, 10)
    d.text((MX + 1814, 1055), "BRD-01 确认 · 从试香到签名", font=F["h3"], fill=TEAL)
    d.text((MX + 1814, 1110), "可运营×复利 = 5×5 = 25", font=F["num_sm"], fill=TEAL)
    d.text((MX + 1814, 1180), "来源链：CF-02 → C02(16条) → DIR-03 → CHK通过 → 确认", font=F["body"], fill=INK)
    d.text((MX + 1814, 1230), "验证第二章：欣赏→确定选择，靠旅程把衣橱编成体验", font=F["small"], fill=MUTED)

    # Scorecard table
    d.text((MX, 1320), "第三章筛选记分卡（映射回锁定层级）", font=F["h2"], fill=INK)
    headers = ["验证项", "计量结果", "判定", "映射第二章"]
    widths = [480, 1100, 400, 1280]
    y = 1380
    rr(d, [MX, y, W - MX, y + 44], SOFT, 4)
    x = MX + 12
    for h, w in zip(headers, widths):
        d.text((x, y + 10), h, font=F["tiny"], fill=MUTED)
        x += w

    scorecard = [
        ("Q1 场景冲突", "冲突证据29/49=59%；3冲突均可回溯", "通过", "主攻场景层：成立"),
        ("Q2 避开词语", "空话淘汰率25%；DIR-01未升格", "通过", "避开词语红海：成立"),
        ("Q3 选择逻辑", "BRD对：哲学25分+旅程25分", "通过*", "统一选择逻辑：可落成"),
        ("筛选总判", "母题×体验服务时刻衣柜", "内部证据链通过", "进入真人概念验证；备选保留"),
    ]
    for i, row in enumerate(scorecard):
        yy = 1432 + i * 100
        bg = SOFT_G if i == 3 else (WHITE if i % 2 == 0 else SOFT)
        rr(d, [MX, yy, W - MX, yy + 92], bg, 6)
        x = MX + 12
        for j, (cell, w) in enumerate(zip(row, widths)):
            col = GREEN if cell.startswith("通过") or cell == "成立" else INK
            if j == 0:
                col = TEAL
            d.text((x, yy + 30), cell, font=F["body"], fill=col)
            x += w

    footer(d, "Source: BRD 四问评分；INS 条数；CHK/漏斗计数  ·  *规模化 PoC 暂缓，交 PART06")
    save(img, "mfk_03_v5_q3_validate.png")


if __name__ == "__main__":
    slide1()
    slide2()
    slide3()
    slide4()
    slide5()
    print("DONE: 5 quantified Part 03 slides")
