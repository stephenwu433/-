#!/usr/bin/env python3
"""Part 01 core problem — data-backed market case for direction building."""
from pathlib import Path
import io
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/workspace/mfk-slides")
ART = Path("/opt/cursor/artifacts")
W, H = 3840, 2160
MX = 130
GAP = 28
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

_CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(_CJK)
FP = fm.FontProperties(fname=_CJK)
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [fm.FontProperties(fname=_CJK).get_name(), "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def fonts():
    s = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
    n = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    b = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
    i = "/usr/share/fonts/truetype/inter/Inter-Regular.ttf"
    ib = "/usr/share/fonts/truetype/inter/Inter-Bold.ttf"
    return {
        "title": ImageFont.truetype(s, 54, index=2),
        "h2": ImageFont.truetype(s, 32, index=2),
        "h3": ImageFont.truetype(b, 24, index=2),
        "body": ImageFont.truetype(n, 22, index=2),
        "small": ImageFont.truetype(n, 18, index=2),
        "tiny": ImageFont.truetype(n, 15, index=2),
        "sub": ImageFont.truetype(n, 24, index=2),
        "label": ImageFont.truetype(ib, 17),
        "num": ImageFont.truetype(ib, 40),
        "num_sm": ImageFont.truetype(ib, 30),
        "brand": ImageFont.truetype(i, 17),
    }


F = fonts()


def fig_to_pil(fig, dpi=170):
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
    fig.savefig(buf, format="png", dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGBA")


def style_ax(ax, title=None):
    ax.set_facecolor("#F5F2EB")
    for sp in ax.spines.values():
        sp.set_color("#D2CDC4")
    ax.tick_params(colors="#1C1C1C", labelsize=8)
    if title:
        ax.set_title(title, fontsize=10, color="#1C1C1C", pad=6, fontweight="bold", fontproperties=FP)


def paste(img, pil_chart, box):
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    ch = pil_chart.copy()
    ch.thumbnail((bw, bh), Image.Resampling.LANCZOS)
    img.paste(ch, (x0 + (bw - ch.width) // 2, y0 + (bh - ch.height) // 2), ch)


def rr(d, box, fill, r=12):
    d.rounded_rectangle(box, radius=r, fill=fill)


def wrap(d, text, xy, font, fill, max_w, lh=30):
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


# ── charts ────────────────────────────────────────────────

def chart_group_pc():
    """Perfumes & Cosmetics revenue + organic 0% annotation."""
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    years = ["2023", "2024", "2025"]
    rev = [8.271, 8.418, 8.174]
    ax.plot(years, rev, color="#22646C", marker="o", linewidth=2.5, markersize=8)
    for x, y in zip(years, rev):
        ax.text(x, y + 0.05, f"{y:.2f}", ha="center", fontsize=8, fontweight="bold", color="#22646C")
    ax.axhline(8.271, color="#D2CDC4", linestyle=":", linewidth=1)
    ax.set_ylabel("€bn")
    ax.set_ylim(7.8, 8.6)
    # annotate organic 0%
    ax.annotate("有机增长 0%\n(2025 & H1'26)", xy=(2, 8.174), xytext=(1.15, 7.95),
                fontsize=8, color="#9B2433", fontproperties=FP,
                arrowprops=dict(arrowstyle="->", color="#9B2433"))
    style_ax(ax, "LVMH 香水美妆收入（连续零增长）")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_wardrobe_shift():
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    labels = ["Gen Z", "Boomers"]
    vals = [10, 2.5]  # midpoint of 8-12 and 2-3
    colors = ["#9B2433", "#B8945A"]
    bars = ax.bar(labels, vals, color=colors, width=0.55)
    for b, v, t in zip(bars, vals, ["8–12 支", "2–3 支"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.3, t, ha="center", fontsize=8, fontweight="bold")
    ax.set_ylabel("人均持有（支）")
    ax.set_ylim(0, 14)
    style_ax(ax, "香氛衣柜代际结构")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_search_heat():
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    labels = ["层叠搜索\n+社媒", "层叠组合", "小众香\n收藏"]
    vals = [63.9, 125, 200]  # cap visual for 500 with annotation
    real = [63.9, 125, 500]
    colors = ["#9B2433", "#B06030", "#22646C"]
    bars = ax.barh(labels[::-1], vals[::-1], color=colors[::-1], height=0.55)
    for b, r in zip(bars, real[::-1]):
        ax.text(b.get_width() + 3, b.get_y() + b.get_height() / 2, f"+{r:g}%",
                va="center", fontsize=8, fontweight="bold")
    ax.set_xlim(0, 260)
    ax.set_xlabel("YoY %（收藏柱为示意截断，实值 +500%）")
    style_ax(ax, "行为热度加速（2025 YoY）")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_share():
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    brands = ["Byredo", "Le Labo", "Jo Malone", "Diptyque", "Tom Ford", "MFK"]
    share = [8.5, 7.5, 7.0, 6.5, 6.0, 5.5]
    colors = ["#22646C"] * 5 + ["#9B2433"]
    y = np.arange(len(brands))
    ax.barh(y, share, color=colors, height=0.55)
    ax.set_yticks(y)
    ax.set_yticklabels(brands)
    for yi, v in zip(y, share):
        ax.text(v + 0.1, yi, f"{v}%", va="center", fontsize=8, fontweight="bold")
    ax.set_xlim(0, 11)
    ax.invert_yaxis()
    style_ax(ax, "Niche 头部份额：MFK 5.5%（选择效率战场）")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_conversion():
    fig, ax = plt.subplots(figsize=(4.4, 3.0))
    labels = ["优化样品链", "平台伙伴\n样品均线"]
    vals = [25, 4]
    colors = ["#22646C", "#B8945A"]
    bars = ax.bar(labels, vals, color=colors, width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.8, f"{v}%", ha="center", fontsize=10, fontweight="bold")
    ax.set_ylabel("样品→正装转化率")
    ax.set_ylim(0, 32)
    ax.annotate("试香后再购正装\n复购意愿 3.2×", xy=(0, 25), xytext=(0.55, 18),
                fontsize=8, color="#9B2433", fontproperties=FP,
                arrowprops=dict(arrowstyle="->", color="#9B2433"))
    style_ax(ax, "转化缺口：路径决定结果")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_layer_donut():
    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    ax.pie(
        [67, 33],
        labels=["会层叠 67%", "单一用法 33%"],
        colors=["#22646C", "#D2CDC4"],
        autopct="%1.0f%%",
        startangle=90,
        pctdistance=0.7,
        wedgeprops=dict(width=0.42, edgecolor="#F5F2EB", linewidth=3),
    )
    ax.text(0, 0, "层叠\n渗透", ha="center", va="center", fontsize=10, fontweight="bold")
    style_ax(ax, "西欧香氛用户层叠渗透")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def build():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)

    # header
    d.text((MX, 36), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED)
    d.text((W - MX - 200, 36), "LVMH BEAUTY", font=F["brand"], fill=MUTED)
    d.text((MX, 78), "01 / CORE PROBLEM + MARKET CASE", font=F["label"], fill=RED)
    d.text((MX, 108), "核心问题，与一次方向构建的市场依据", font=F["title"], fill=INK)
    d.rectangle([MX, 182, MX + 100, 188], fill=GOLD)
    d.text(
        (MX, 205),
        "不是先宣布要重构，再用数据圆场——先看集团压力与市场结构，再推出「必须建决策系统」。",
        font=F["sub"],
        fill=MUTED,
    )

    # Core problem compact
    rr(d, [MX, 260, W - MX, 430], SOFT_R, 10)
    d.text((MX + 24, 278), "核心问题", font=F["label"], fill=RED)
    wrap(
        d,
        "在高端香水选择过载、情绪叙事同质化的环境下，MFK 如何把对调香水准与高级感的欣赏，"
        "转化为「哪一支适合我、为什么适合我」的确定选择，并形成竞品难以替代的拥有理由？",
        (MX + 24, 318),
        F["body"],
        INK,
        W - 2 * MX - 60,
        34,
    )
    d.text(
        (MX + 24, 390),
        "缺口链：欣赏 → 确定选择（仍停在「感觉不错」） → 拥有理由（缺不可平移的 Why MFK）",
        font=F["small"],
        fill=MUTED,
    )

    # Section: market evidence
    d.text((MX, 460), "市场与集团证据（为何现在必须构建方向）", font=F["h2"], fill=INK)
    d.rectangle([MX, 505, MX + 90, 510], fill=GOLD)

    # 6 charts in 2×3
    paste(img, chart_group_pc(), (MX, 525, MX + 1200, 1020))
    paste(img, chart_wardrobe_shift(), (MX + 1220, 525, MX + 2300, 1020))
    paste(img, chart_search_heat(), (MX + 2320, 525, W - MX, 1020))

    paste(img, chart_share(), (MX, 1030, MX + 1200, 1500))
    paste(img, chart_conversion(), (MX + 1220, 1030, MX + 2400, 1500))
    paste(img, chart_layer_donut(), (MX + 2420, 1030, W - MX, 1500))

    # Data → necessity mapping table
    d.text((MX, 1520), "从数据推出「必须构建」——四条因果，不是口号", font=F["h2"], fill=INK)
    headers = ["证据", "计量", "结构含义", "对 MFK 的行动含义"]
    widths = [520, 700, 1000, 1220]
    y = 1570
    rr(d, [MX, y, W - MX, y + 40], SOFT, 4)
    x = MX + 12
    for h, w in zip(headers, widths):
        d.text((x, y + 10), h, font=F["tiny"], fill=MUTED)
        x += w

    rows = [
        ("集团零增长", "P&C 有机 0%×2 期；收入 8.17€bn", "增长不能靠品类自然放量", "必须提升选择效率×转化"),
        ("衣柜行为崛起", "Gen Z 8–12支；层叠搜索 +63.9%", "单香口号接不住结构变迁", "主战场转向时刻/场景系统"),
        ("竞争占位拥挤", "Byredo 8.5% / Le Labo 7.5% / MFK 5.5%", "头部差的是被选效率", "补统一选择逻辑，而非再加形容词"),
        ("转化路径落差", "优化样品链 25% vs 均线 4%；3.2×", "路径设计决定正装转化", "把咨询/试香编成可运营决策系统"),
    ]
    for i, row in enumerate(rows):
        yy = 1618 + i * 78
        bg = WHITE if i % 2 == 0 else SOFT_T
        rr(d, [MX, yy, W - MX, yy + 72], bg, 4)
        x = MX + 12
        for j, (cell, w) in enumerate(zip(row, widths)):
            col = RED if j == 0 else INK
            d.text((x, yy + 22), cell, font=F["small"], fill=col)
            x += w

    # footer conclusion strip - slightly overlapping? check space
    # rows end ~1618+4*78=1930, tight. Shrink row height or move.
    # Actually 1618+312=1930, footer at 2055 - OK with thin footer note

    d.line([(MX, FY - 16), (W - MX, FY - 16)], fill=LINE, width=2)
    d.text(
        (MX, FY),
        "Source: LVMH FY2025 / H1 2026 · Scento 2026 · Spate 2026 · Circana · WWD/Phiur sampling  ·  结论：方向构建 = 建决策系统，不是换口号",
        font=F["tiny"],
        fill=MUTED,
    )
    d.text((W - MX - 380, FY), "MFK Brand Strategy  |  CONFIDENTIAL", font=F["tiny"], fill=MUTED)

    save(img, "mfk_01_core_problem.png")


if __name__ == "__main__":
    build()
