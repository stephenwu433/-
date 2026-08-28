#!/usr/bin/env python3
"""PART 04 × 3 — Entry point decision + aesthetic forecast + lock."""
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
        "title": ImageFont.truetype(s, 56, index=2),
        "h2": ImageFont.truetype(s, 34, index=2),
        "h3": ImageFont.truetype(b, 26, index=2),
        "body": ImageFont.truetype(n, 24, index=2),
        "small": ImageFont.truetype(n, 20, index=2),
        "tiny": ImageFont.truetype(n, 16, index=2),
        "sub": ImageFont.truetype(n, 26, index=2),
        "label": ImageFont.truetype(b, 18, index=2),
        "num": ImageFont.truetype(ib, 42),
        "num_sm": ImageFont.truetype(ib, 30),
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
    d.text((MX, 40), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED)
    d.text((W - MX - 200, 40), "LVMH BEAUTY", font=F["brand"], fill=MUTED)
    d.text((MX, 88), code, font=F["label"], fill=RED)
    d.text((MX, 120), title, font=F["title"], fill=INK)
    d.rectangle([MX, 200, MX + 100, 206], fill=GOLD)
    d.text((MX, 222), question, font=F["sub"], fill=MUTED)


def footer(d, src):
    d.line([(MX, FY - 16), (W - MX, FY - 16)], fill=LINE, width=2)
    d.text((MX, FY), src, font=F["tiny"], fill=MUTED)
    d.text((W - MX - 380, FY), "MFK Brand Strategy  |  PART 04  |  CONFIDENTIAL", font=F["tiny"], fill=MUTED)


def save(img, name):
    img.save(OUT / name, "PNG")
    img.resize((1920, 1080), Image.Resampling.LANCZOS).save(
        OUT / name.replace(".png", "_1920.png"), "PNG"
    )
    img.save(ART / name, "PNG")
    print("saved", name)


# Scores: 缺口×蓝海×可改×杠杆 (1-5) from Part 01 logic, refined for entry
# 词语 / 场景 / 资产 / 体验
ENTRY = [
    ("词语层", 2, 1, 4, 2),   # red ocean
    ("场景层", 5, 4, 4, 5),   # main
    ("资产层", 4, 3, 3, 5),   # support
    ("体验层", 5, 4, 3, 4),   # co-entry with scene
]


def chart_entry_scores():
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    labels = [e[0] for e in ENTRY]
    totals = [sum(e[1:]) for e in ENTRY]
    colors = ["#B06030", "#9B2433", "#22646C", "#B8945A"]
    bars = ax.bar(labels, totals, color=colors, width=0.6)
    for b, t in zip(bars, totals):
        ax.text(b.get_x() + b.get_width() / 2, t + 0.3, str(t), ha="center", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 22)
    ax.set_ylabel("综合分（缺口×蓝海×可改×杠杆）")
    ax.axhline(15, color="#D2CDC4", linestyle=":", linewidth=1)
    style_ax(ax, "进入点四层打分（满分 20）")
    # annotate
    ax.annotate("主切", xy=(1, 18), xytext=(1.35, 20),
                fontsize=9, color="#9B2433", fontproperties=FP,
                arrowprops=dict(arrowstyle="->", color="#9B2433"))
    ax.annotate("配套入口", xy=(3, 16), xytext=(2.4, 19),
                fontsize=9, color="#B8945A", fontproperties=FP,
                arrowprops=dict(arrowstyle="->", color="#B8945A"))
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_radar_aesthetic():
    """Simple grouped bars as aesthetic code intensity vs competitors."""
    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    dims = ["克制精准", "署名判断", "时刻可编", "情绪形容词", "仪式个性"]
    mfk = [5, 5, 5, 1, 2]
    byredo = [2, 1, 2, 5, 3]
    lelabo = [3, 2, 2, 2, 5]
    x = np.arange(len(dims))
    w = 0.25
    ax.bar(x - w, mfk, w, color="#9B2433", label="MFK 目标位")
    ax.bar(x, byredo, w, color="#22646C", label="Byredo")
    ax.bar(x + w, lelabo, w, color="#B8945A", label="Le Labo")
    ax.set_xticks(x)
    ax.set_xticklabels(dims, fontsize=8)
    ax.set_ylim(0, 6)
    ax.set_ylabel("占位强度 (1-5)")
    ax.legend(fontsize=8, frameon=False, loc="upper right")
    style_ax(ax, "未来美学占位：MFK vs 对照竞品")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_entry_sequence():
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    stages = ["主切\n场景剧本", "配套\n试香→签名", "资产\n衣橱分工", "词语\n仅作锚点"]
    vals = [1, 2, 3, 4]  # sequence order as visual
    # show as timeline bars of "启动优先级" inverse
    priority = [5, 4, 3, 1]
    colors = ["#9B2433", "#B8945A", "#22646C", "#D2CDC4"]
    bars = ax.bar(stages, priority, color=colors, width=0.55)
    for b, p, s in zip(bars, priority, ["立刻", "并行", "随后", "禁止主攻"]):
        ax.text(b.get_x() + b.get_width() / 2, p + 0.15, s, ha="center", fontsize=8, fontweight="bold")
    ax.set_ylim(0, 6.5)
    ax.set_ylabel("启动优先级")
    style_ax(ax, "进入顺序（不是四选一，是主次编排）")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


# ═══════════════════════════════════════════════════════════
# SLIDE 1 — Entry decision
# ═══════════════════════════════════════════════════════════
def slide1():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "04 / ENTRY DECISION  ·  1 of 3",
        "进入点裁定：主切场景剧本，体验作配套入口",
        "前三章约束已定：避开词语红海；场景层有冲突证据；BRD 给出哲学+旅程。本章只做切入选择。",
    )

    # Constraint strip
    rr(d, [MX, 290, W - MX, 420], SOFT_T, 10)
    d.text((MX + 28, 310), "决策约束（不可回退）", font=F["label"], fill=TEAL)
    d.text(
        (MX + 28, 355),
        "PART01 场景主攻 · PART02 时刻衣柜命题 · PART03 BRD-02「精准的感性」主推 + BRD-01「试香到签名」确认  →  进入点必须同时服务「此刻怎么选」与「如何确定选择」。",
        font=F["body"],
        fill=INK,
    )

    paste(img, chart_entry_scores(), (MX, 450, MX + 1650, 1180))
    paste(img, chart_entry_sequence(), (MX + 1680, 450, W - MX, 1180))

    # Scoring table
    d.text((MX, 1210), "四层打分表（1–5）与裁定", font=F["h2"], fill=INK)
    headers = ["进入层", "缺口", "蓝海", "可改", "杠杆", "合计", "裁定"]
    widths = [420, 280, 280, 280, 280, 320, 1200]
    y = 1270
    rr(d, [MX, y, W - MX, y + 44], SOFT, 4)
    x = MX + 16
    for h, w in zip(headers, widths):
        d.text((x, y + 10), h, font=F["tiny"], fill=MUTED)
        x += w

    rulings = [
        ("词语层", 2, 1, 4, 2, 9, "淘汰：空话闸已杀；红海不可主切"),
        ("场景层", 5, 4, 4, 5, 18, "主切：时刻选择剧本 / 衣橱导航"),
        ("资产层", 4, 3, 3, 5, 15, "配套：540 等产品重新分工进衣橱"),
        ("体验层", 5, 4, 3, 4, 16, "配套入口：试香→签名咨询路径"),
    ]
    for i, row in enumerate(rulings):
        yy = 1322 + i * 100
        bg = SOFT_R if i == 0 else (SOFT_G if i == 1 else (SOFT_T if i == 3 else WHITE))
        rr(d, [MX, yy, W - MX, yy + 92], bg, 6)
        cells = [row[0], str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), row[6]]
        x = MX + 16
        for j, (cell, w) in enumerate(zip(cells, widths)):
            col = RED if i == 1 and j in (0, 5) else INK
            if i == 0 and j == 0:
                col = ORANGE
            d.text((x, yy + 30), cell, font=F["body"], fill=col)
            x += w

    # Decision line
    rr(d, [MX, 1750, W - MX, 1920], SOFT_R, 10)
    d.text((MX + 28, 1785), "本页裁定", font=F["label"], fill=RED)
    wrap(
        d,
        "主切入口 = 场景层「此刻该用哪一支」的选择剧本；配套入口 = 体验层「从试香到签名」。"
        "资产层随后重组产品角色；词语层只作最小锚点，禁止当主攻。下一页定义配这套入口的未来美学。",
        (MX + 28, 1830),
        F["body"],
        INK,
        W - 2 * MX - 60,
        36,
    )

    footer(d, "Source: PART01 分层评分逻辑延续；PART02/03 命题与 BRD 约束")
    save(img, "mfk_04_01_entry_decision.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 2 — Aesthetic forecast
# ═══════════════════════════════════════════════════════════
def slide2():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "04 / AESTHETIC FORECAST  ·  2 of 3",
        "美学预判：未来香氛美学 =「精准的感性」可感知化",
        "美学不是 moodboard 堆砌；要从 BRD-02 推出可执行的嗅觉 / 视觉 / 仪式码。",
    )

    # Definition
    rr(d, [MX, 290, W - MX, 480], SOFT_R, 10)
    d.text((MX + 28, 315), "美学定义（一句话）", font=F["label"], fill=RED)
    d.text(
        (MX + 28, 365),
        "多一分则腻，少一分则寡——未来 MFK 美学追求可感知的精准克制，而不是更浓的奢华表演。",
        font=F["h2"],
        fill=INK,
    )
    d.text(
        (MX + 28, 430),
        "来源：BRD-02「精准的感性」· 拒绝空话词（高级感/氛围感/松弛奢华）· 对齐场景层「此刻刚好」",
        font=F["body"],
        fill=MUTED,
    )

    paste(img, chart_radar_aesthetic(), (MX, 510, MX + 1700, 1200))

    # Three aesthetic codes
    codes = [
        (
            "嗅觉码",
            TEAL,
            SOFT_T,
            [
                "签名清晰，但不压迫公共场合",
                "甜感可控 / 干净可进职场",
                "层叠友好：可按时刻加减",
                "反例：过量甜腻、撞香大众调",
            ],
        ),
        (
            "视觉码",
            RED,
            SOFT_R,
            [
                "留白与比例优先于装饰",
                "金/乳白点缀，拒绝紫雾光效",
                "瓶身与版式传达「准」而非「炫」",
                "反例：贴纸感促销、情绪拼贴",
            ],
        ),
        (
            "仪式码",
            GOLD,
            SOFT_G,
            [
                "咨询=判断过程，不是销售话术",
                "试香有记录，形成个人香气档案",
                "从样品到正装有可复述理由",
                "反例：只发小样无选择闭环",
            ],
        ),
    ]
    cw = (W - MX - 1740 - 2 * GAP) // 1
    # place codes to the right of chart in 3 stacked cards - better 3 columns below chart right
    # Actually put three cards on right of chart
    card_w = W - MX - 1740 - GAP
    for i, (t, accent, bg, lines) in enumerate(codes):
        x = MX + 1740
        y = 510 + i * 230
        rr(d, [x, y, W - MX, y + 210], bg, 10)
        d.rectangle([x, y, x + 10, y + 210], fill=accent)
        d.text((x + 36, y + 24), t, font=F["h3"], fill=accent)
        for j, line in enumerate(lines):
            d.text((x + 36, y + 70 + j * 32), "·  " + line, font=F["small"], fill=INK)

    # Competitor contrast table
    d.text((MX, 1240), "美学差位表：MFK 不跟谁抢同一套感受语言", font=F["h2"], fill=INK)
    headers = ["品牌", "强势美学", "MFK 不跟进的原因", "MFK 差分"]
    widths = [420, 800, 1100, 1100]
    y = 1300
    rr(d, [MX, y, W - MX, y + 44], SOFT, 4)
    x = MX + 16
    for h, w in zip(headers, widths):
        d.text((x, y + 10), h, font=F["tiny"], fill=MUTED)
        x += w

    rows = [
        ("Byredo", "情绪记忆 / 生活方式诗意", "情绪形容词红海；可替换性高", "用精准判断替代情绪形容词"),
        ("Le Labo", "个性化调香仪式", "仪式强但选择标准仍偏定制神秘", "把仪式收成可记录的选择逻辑"),
        ("病毒单香", "爆款气味记忆", "一支代名词，衣橱无法编排", "时刻衣柜：多支可编、单支有位"),
    ]
    for i, row in enumerate(rows):
        yy = 1352 + i * 110
        rr(d, [MX, yy, W - MX, yy + 100], WHITE if i % 2 == 0 else SOFT, 6)
        x = MX + 16
        for j, (cell, w) in enumerate(zip(row, widths)):
            d.text((x, yy + 34), cell, font=F["body"], fill=RED if j == 0 else INK)
            x += w

    rr(d, [MX, 1720, W - MX, 1920], SOFT_G, 10)
    d.text((MX + 28, 1760), "本页结论", font=F["label"], fill=GOLD)
    wrap(
        d,
        "未来美学预判锁定为「精准克制的可感知奢华」：嗅觉准、视觉净、仪式可记录。"
        "它服务场景进入点——让「此刻选哪一支」有美学标准，而不是再发明一套生活方式形容词。",
        (MX + 28, 1810),
        F["body"],
        INK,
        W - 2 * MX - 60,
        36,
    )

    footer(d, "Source: BRD-02；PART02 竞品深潜；BW 空话禁用约束美学用语")
    save(img, "mfk_04_02_aesthetic_forecast.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 3 — Lock + handoff
# ═══════════════════════════════════════════════════════════
def slide3():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "04 / LOCK & HANDOFF  ·  3 of 3",
        "进入×美学锁定，并移交品牌主张编排",
        "第四章收束：主入口、美学码、禁止项一次钉死，作为 PART05 的唯一输入。",
    )

    # Two lock cards
    rr(d, [MX, 290, MX + 1750, 900], WHITE, 12)
    d.rectangle([MX, 290, MX + 1750, 302], fill=RED)
    d.text((MX + 36, 330), "锁定 A · 进入点", font=F["h2"], fill=RED)
    d.text((MX + 36, 400), "主切：场景层选择剧本", font=F["h3"], fill=INK)
    for i, line in enumerate(
        [
            "交付物：时刻选香导航（通勤/约会/正式/独处…）",
            "用户感知：三秒内知道「此刻用哪一支」",
            "配套入口：试香→签名（BRD-01）并行启动",
            "资产随后：产品线按衣橱角色重新分工",
            "成功计量：样品→正装转化、咨询档案完成率",
        ]
    ):
        d.text((MX + 36, 470 + i * 55), "▸  " + line, font=F["body"], fill=INK)

    rr(d, [MX + 1790, 290, W - MX, 900], WHITE, 12)
    d.rectangle([MX + 1790, 290, W - MX, 302], fill=TEAL)
    d.text((MX + 1826, 330), "锁定 B · 美学码", font=F["h2"], fill=TEAL)
    d.text((MX + 1826, 400), "精准的感性 · 可感知克制", font=F["h3"], fill=INK)
    for i, line in enumerate(
        [
            "嗅觉：准、可控甜、可层叠、公共得体",
            "视觉：比例与留白 > 装饰与光效",
            "仪式：咨询可记录，理由可复述",
            "语言：禁用高级感/氛围感/松弛奢华…",
            "成功计量：主张可被复述且竞品不可替换",
        ]
    ):
        d.text((MX + 1826, 470 + i * 55), "▸  " + line, font=F["body"], fill=INK)

    # Do / Don't
    d.text((MX, 940), "硬边界：做什么 / 不做什么", font=F["h2"], fill=INK)
    rr(d, [MX, 1000, MX + 1750, 1380], SOFT_T, 10)
    d.text((MX + 36, 1030), "做", font=F["label"], fill=TEAL)
    for i, line in enumerate(
        [
            "用场景剧本承接「时刻衣柜」命题",
            "用精准感性做选择标准（BRD-02）",
            "用试香到签名闭环转化（BRD-01）",
            "小步试点验证转化与可运营性",
        ]
    ):
        d.text((MX + 36, 1090 + i * 55), "✓  " + line, font=F["body"], fill=INK)

    rr(d, [MX + 1790, 1000, W - MX, 1380], SOFT_R, 10)
    d.text((MX + 1826, 1030), "不做", font=F["label"], fill=RED)
    for i, line in enumerate(
        [
            "不以「小众/高级感」当主主张",
            "不以单支爆款叙事覆盖衣橱系统",
            "不先做大传播再补选择逻辑",
            "不把身体护理延伸当主战场（DIR-04 已淘汰）",
        ]
    ):
        d.text((MX + 1826, 1090 + i * 55), "✗  " + line, font=F["body"], fill=INK)

    # Handoff to Part 05
    rr(d, [MX, 1430, W - MX, 1920], SOFT_G, 12)
    d.text((MX + 36, 1470), "移交 PART 05 · 品牌主张与现实编排（输入清单）", font=F["h2"], fill=INK)
    handoff = [
        ("输入 1", "战略定位", "私人香气表达的精准权威（唯一）"),
        ("输入 2", "品牌母题", "精准的感性——要的不是更浓，是更准的克制"),
        ("输入 3", "体验机制", "从试香到签名——欣赏转化为确定选择"),
        ("输入 4", "产品系统", "时刻衣柜——场景剧本 × 衣橱角色 × 咨询档案"),
    ]
    hw = (W - 2 * MX - 3 * GAP - 72) // 4
    for i, (a, b, c) in enumerate(handoff):
        x = MX + 36 + i * (hw + GAP)
        rr(d, [x, 1560, x + hw, 1840], WHITE, 8)
        d.text((x + 20, 1590), a, font=F["label"], fill=GOLD)
        d.text((x + 20, 1650), b, font=F["h3"], fill=INK)
        wrap(d, c, (x + 20, 1720), F["small"], MUTED, hw - 40, 28)

    footer(d, "Source: PART04 裁定页；对齐 PART03 验证记分卡与 PART02 时刻衣柜命题")
    save(img, "mfk_04_03_lock_handoff.png")


if __name__ == "__main__":
    slide1()
    slide2()
    slide3()
    print("DONE: PART 04 × 3")
