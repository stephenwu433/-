#!/usr/bin/env python3
"""PART 06 × 3 — 90-day pilot and evaluation."""
from pathlib import Path
import io
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/workspace/mfk-slides")
ART = Path("/opt/cursor/artifacts")
W, H = 3840, 2160
MX = 140
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
GREEN = (46, 125, 90)
ORANGE = (176, 96, 48)

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
        "h2": ImageFont.truetype(s, 34, index=2),
        "h3": ImageFont.truetype(b, 26, index=2),
        "body": ImageFont.truetype(n, 24, index=2),
        "small": ImageFont.truetype(n, 20, index=2),
        "tiny": ImageFont.truetype(n, 16, index=2),
        "sub": ImageFont.truetype(n, 25, index=2),
        "label": ImageFont.truetype(b, 18, index=2),
        "num": ImageFont.truetype(ib, 40),
        "num_sm": ImageFont.truetype(ib, 28),
        "brand": ImageFont.truetype(i, 18),
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
    fig.savefig(
        buf, format="png", dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=0.04
    )
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGBA")


def style_ax(ax, title=None):
    ax.set_facecolor("#F5F2EB")
    for sp in ax.spines.values():
        sp.set_color("#D2CDC4")
    ax.tick_params(colors="#1C1C1C", labelsize=8)
    if title:
        ax.set_title(
            title, fontsize=10, color="#1C1C1C", pad=6, fontweight="bold", fontproperties=FP
        )


def paste(img, pil_chart, box):
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    ch = pil_chart.copy()
    ch.thumbnail((bw, bh), Image.Resampling.LANCZOS)
    img.paste(ch, (x0 + (bw - ch.width) // 2, y0 + (bh - ch.height) // 2), ch)


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


def header(d, code, title, question):
    d.text((MX, 38), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED)
    d.text((W - MX - 200, 38), "LVMH BEAUTY", font=F["brand"], fill=MUTED)
    d.text((MX, 84), code, font=F["label"], fill=RED)
    d.text((MX, 114), title, font=F["title"], fill=INK)
    d.rectangle([MX, 192, MX + 100, 198], fill=GOLD)
    d.text((MX, 214), question, font=F["sub"], fill=MUTED)


def footer(d, src):
    d.line([(MX, FY - 16), (W - MX, FY - 16)], fill=LINE, width=2)
    d.text((MX, FY), src, font=F["tiny"], fill=MUTED)
    d.text(
        (W - MX - 400, FY),
        "MFK Brand Strategy  |  PART 06  |  CONFIDENTIAL",
        font=F["tiny"],
        fill=MUTED,
    )


def save(img, name):
    img.save(OUT / name, "PNG")
    img.resize((1920, 1080), Image.Resampling.LANCZOS).save(
        OUT / name.replace(".png", "_1920.png"), "PNG"
    )
    img.save(ART / name, "PNG")
    print("saved", name)


def chart_loop():
    """Simple funnel of minimum closed loop steps as horizontal flow values."""
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    stages = ["进店/\n触达", "此刻\n三问", "试香+\n建档", "正装/\n回访"]
    # expected conversion chain index 100 base
    vals = [100, 70, 45, 18]
    colors = ["#22646C", "#22646C", "#B8945A", "#9B2433"]
    bars = ax.bar(stages, vals, color=colors, width=0.55)
    for b, v in zip(bars, vals):
        ax.text(
            b.get_x() + b.get_width() / 2,
            v + 2,
            str(v),
            ha="center",
            fontsize=10,
            fontweight="bold",
        )
    ax.set_ylim(0, 120)
    ax.set_ylabel("示意流量指数")
    style_ax(ax, "最小闭环流量示意（指数，非正式预测）")
    ax.annotate(
        "验证焦点\n样品→正装",
        xy=(3, 18),
        xytext=(2.2, 55),
        fontsize=8,
        color="#9B2433",
        fontproperties=FP,
        arrowprops=dict(arrowstyle="->", color="#9B2433"),
    )
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_90d_timeline():
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    phases = ["D0–30\n建闭环", "D31–60\n跑转化", "D61–90\n复盘裁决"]
    # intensity of activity
    build = [5, 2, 1]
    run = [2, 5, 3]
    decide = [1, 2, 5]
    x = np.arange(len(phases))
    w = 0.25
    ax.bar(x - w, build, w, color="#22646C", label="搭建")
    ax.bar(x, run, w, color="#B8945A", label="运营转化")
    ax.bar(x + w, decide, w, color="#9B2433", label="评估裁决")
    ax.set_xticks(x)
    ax.set_xticklabels(phases)
    ax.set_ylim(0, 6.5)
    ax.set_ylabel("工作强度 (1-5)")
    ax.legend(fontsize=8, frameon=False, loc="upper right")
    style_ax(ax, "90天三段工作重心")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_kpi_targets():
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    labels = ["样品→正装\n转化", "三秒命中", "建档率", "主张复述"]
    baseline = [8, 25, 20, 15]  # illustrative baseline %
    target = [18, 45, 60, 50]
    x = np.arange(len(labels))
    w = 0.35
    ax.bar(x - w / 2, baseline, w, color="#D2CDC4", label="对照/基线")
    ax.bar(x + w / 2, target, w, color="#9B2433", label="90天目标")
    for i, (b, t) in enumerate(zip(baseline, target)):
        ax.text(i - w / 2, b + 1.5, f"{b}%", ha="center", fontsize=8)
        ax.text(i + w / 2, t + 1.5, f"{t}%", ha="center", fontsize=8, fontweight="bold", color="#9B2433")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 75)
    ax.set_ylabel("%")
    ax.legend(fontsize=8, frameon=False)
    style_ax(ax, "核心KPI：基线 vs 90天目标（试点口径）")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


# ═══════════════════════════════════════════════════════════
# SLIDE 1 — Minimum closed loop
# ═══════════════════════════════════════════════════════════
def slide1():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "06 / MINIMUM LOOP  ·  1 of 3",
        "最小商业闭环：只验证「导航+档案」能否抬升转化",
        "第五章已交试点输入。本章用最小触点集验证时刻衣柜是否可运营，不扩全国。",
    )

    # Hypothesis
    rr(d, [MX, 280, W - MX, 480], SOFT_R, 12)
    d.text((MX + 32, 305), "试点命题（唯一）", font=F["label"], fill=RED)
    d.text(
        (MX + 32, 355),
        "在单点零售触点上，场景导航 + 试香档案，能否显著提升样品→正装转化，并让顾客复述「为何适合我」。",
        font=F["h3"],
        fill=INK,
    )
    d.text(
        (MX + 32, 430),
        "不验证：全国铺开、大传播声量、身体护理延伸、词语层主主张。",
        font=F["body"],
        fill=MUTED,
    )

    paste(img, chart_loop(), (MX, 520, MX + 1700, 1100))

    # Scope cards
    d.text((MX + 1740, 520), "闭环最小集（缺一不算验）", font=F["h3"], fill=INK)
    musts = [
        ("柜台", "1 个试点柜/渠道", "此刻三问 + 衣橱推荐"),
        ("档案", "试香绑定档案ID", "冲突/忌口/推荐理由"),
        ("产品", "四柱角色清晰陈列", "签名/日间/层叠/探索"),
        ("内容", "时刻选香短内容条", "示范精准，不空话"),
        ("追踪", "样品→正装可归因", "无ID转化不计入优化"),
    ]
    for i, (t, a, b) in enumerate(musts):
        y = 580 + i * 100
        rr(d, [MX + 1740, y, W - MX, y + 88], WHITE, 8)
        d.text((MX + 1764, y + 18), t, font=F["label"], fill=TEAL)
        d.text((MX + 1900, y + 16), a, font=F["body"], fill=INK)
        d.text((MX + 1900, y + 50), b, font=F["small"], fill=MUTED)

    # In / Out table
    d.text((MX, 1140), "范围边界", font=F["h2"], fill=INK)
    rr(d, [MX, 1200, MX + 1750, 1920], SOFT_T, 12)
    d.text((MX + 36, 1240), "做（In Scope）", font=F["h3"], fill=TEAL)
    for i, line in enumerate(
        [
            "1 试点柜 + 最小内容条 + 档案系统",
            "培训顾问执行「三问→推荐→试香→建档」",
            "540 等按衣橱角色陈列，不单堆爆款",
            "每周看转化/命中/建档三张表",
            "收集空话回潮与履约成本预警",
        ]
    ):
        d.text((MX + 36, 1320 + i * 90), "✓  " + line, font=F["body"], fill=INK)

    rr(d, [MX + 1790, 1200, W - MX, 1920], SOFT_R, 12)
    d.text((MX + 1826, 1240), "不做（Out of Scope）", font=F["h3"], fill=RED)
    for i, line in enumerate(
        [
            "多城同步大铺开 / 旗舰改造工程",
            "先投放大传播再补选择逻辑",
            "以「小众高级感」当主KPI话术",
            "DIR-04 身体护理当主战场",
            "无档案的促销转化算试点成功",
        ]
    ):
        d.text((MX + 1826, 1320 + i * 90), "✗  " + line, font=F["body"], fill=INK)

    footer(d, "Source: PART05 移交清单；PART04 进入锁定；对照转化路径 25% vs 4%")
    save(img, "mfk_06_01_minimum_loop.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 2 — 90-day plan
# ═══════════════════════════════════════════════════════════
def slide2():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "06 / 90-DAY PLAN  ·  2 of 3",
        "90天编排：建闭环 → 跑转化 → 复盘裁决",
        "三段节奏不可并行冒进：先能计量，再追求抬升，最后才决定扩面。",
    )

    paste(img, chart_90d_timeline(), (MX, 280, MX + 1700, 820))

    rr(d, [MX + 1740, 280, W - MX, 820], SOFT_G, 10)
    d.text((MX + 1776, 320), "节奏原则", font=F["h3"], fill=GOLD)
    for i, line in enumerate(
        [
            "D0–30：闭环能跑通比好看重要",
            "D31–60：只优化可归因转化",
            "D61–90：用阈值表做裁决",
            "",
            "每周例会三问：",
            "1. 数据是否可归因？",
            "2. 空话是否回潮？",
            "3. 履约成本是否可控？",
            "",
            "任一红灯连续2周 → 冻结扩面",
        ]
    ):
        d.text((MX + 1776, 390 + i * 36), line, font=F["body"], fill=INK)

    # Three phase detail
    phases = [
        (
            "D0–30 建闭环",
            TEAL,
            SOFT_T,
            [
                "选定试点柜与顾问编制",
                "上线三问话术+衣橱陈列分区",
                "档案字段上线（冲突/忌口/推荐）",
                "内容条：3条时刻选香示范",
                "打通样品ID→正装归因",
                "验收：无断点走通 20 单",
            ],
        ),
        (
            "D31–60 跑转化",
            GOLD,
            SOFT_G,
            [
                "按周优化首推命中与话术",
                "A/B：有导航 vs 常规推香",
                "回访试香与补档机制启动",
                "内容只放量已验证话术",
                "监控履约时效与成本",
                "验收：转化周环比连续↑",
            ],
        ),
        (
            "D61–90 复盘裁决",
            RED,
            SOFT_R,
            [
                "对照基线完成四项KPI读数",
                "质检：主张复述抽样",
                "成本账：单次咨询全成本",
                "输出 Go / Iterate / Kill",
                "若 Go：定义下一扩面单元",
                "若 Kill：沉淀反例进资产库",
            ],
        ),
    ]
    pw = (W - 2 * MX - 2 * GAP) // 3
    for i, (t, accent, bg, lines) in enumerate(phases):
        x = MX + i * (pw + GAP)
        rr(d, [x, 880, x + pw, 1920], bg, 12)
        d.rectangle([x, 880, x + pw, 892], fill=accent)
        d.text((x + 28, 930), t, font=F["h3"], fill=accent)
        for j, line in enumerate(lines):
            d.text((x + 28, 1020 + j * 120), f"{j+1}.  {line}", font=F["body"], fill=INK)

    footer(d, "Source: PART05 试点触点；运营节奏按最小闭环验收节点设计")
    save(img, "mfk_06_02_ninety_day_plan.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 3 — Evaluation + decision
# ═══════════════════════════════════════════════════════════
def slide3():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "06 / EVALUATE & DECIDE  ·  3 of 3",
        "评估与裁决：用预设阈值决定 Go / Iterate / Kill",
        "先定阈值再跑试点，避免事后改标准。全案以可复核闭环收束。",
    )

    paste(img, chart_kpi_targets(), (MX, 280, MX + 1650, 1000))

    # Threshold cards
    rr(d, [MX + 1690, 280, W - MX, 1000], WHITE, 12)
    d.text((MX + 1726, 320), "裁决阈值（D90）", font=F["h3"], fill=INK)
    rules = [
        (GREEN, "GO 扩面", "四项KPI≥目标且成本可控\n空话抽检违规 < 5%"),
        (GOLD, "ITERATE", "1–2项未达标但方向正确\n收紧范围再跑 1 个30天"),
        (RED, "KILL / 停扩", "转化无归因提升，或空话回潮\n或履约成本失控连续2周"),
    ]
    for i, (col, t, b) in enumerate(rules):
        y = 400 + i * 180
        rr(d, [MX + 1726, y, W - MX - 36, y + 160], SOFT if i == 1 else (SOFT_G if i == 0 else SOFT_R), 8)
        d.text((MX + 1760, y + 24), t, font=F["h3"], fill=col)
        for j, line in enumerate(b.split("\n")):
            d.text((MX + 1760, y + 80 + j * 32), line, font=F["small"], fill=INK)

    # KPI table
    d.text((MX, 1040), "KPI 定义表（试点口径）", font=F["h2"], fill=INK)
    headers = ["指标", "定义", "基线", "目标", "数据来源"]
    widths = [480, 1100, 360, 360, 1000]
    y = 1100
    rr(d, [MX, y, W - MX, y + 48], SOFT, 4)
    x = MX + 16
    for h, w in zip(headers, widths):
        d.text((x, y + 12), h, font=F["tiny"], fill=MUTED)
        x += w

    rows = [
        ("样品→正装转化", "有档案ID的试香中，90天内转正装占比", "8%", "18%", "POS + 档案系统"),
        ("三秒命中", "导航后首推被试香的比例", "25%", "45%", "柜台记录表"),
        ("建档率", "试香顾客完成必填字段占比", "20%", "60%", "档案系统"),
        ("主张复述", "抽访能正确复述主句要点占比", "15%", "50%", "出店/回访问卷"),
    ]
    for i, row in enumerate(rows):
        yy = 1160 + i * 100
        rr(d, [MX, yy, W - MX, yy + 92], WHITE if i % 2 == 0 else SOFT_T, 6)
        x = MX + 16
        for j, (cell, w) in enumerate(zip(row, widths)):
            col = RED if j in (0, 3) else INK
            d.text((x, yy + 30), cell, font=F["body"], fill=col)
            x += w

    # Closing of whole deck
    rr(d, [MX, 1600, W - MX, 1920], SOFT_R, 12)
    d.text((MX + 32, 1640), "全案收束", font=F["label"], fill=RED)
    wrap(
        d,
        "战场在场景层，命题是时刻衣柜，资产是精准感性 + 试香到签名。"
        "进入点已锁定，主张已编排进四线。90天只用最小闭环验证转化与可运营性——"
        "过闸则扩面，不过则迭代或止损。方向成立不等于规模成立；验证之后才有资格放大。",
        (MX + 32, 1700),
        F["body"],
        INK,
        W - 2 * MX - 64,
        40,
    )

    footer(d, "Source: PART05 KPI；PART01 转化路径差；试点目标为管理阈值，落地前需用本地基线校准")
    save(img, "mfk_06_03_evaluate_decide.png")


if __name__ == "__main__":
    slide1()
    slide2()
    slide3()
    print("DONE: PART 06 × 3")
