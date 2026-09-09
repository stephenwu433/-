#!/usr/bin/env python3
"""PART 05 × 4 — Brand proposition + reality orchestration."""
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
        "MFK Brand Strategy  |  PART 05  |  CONFIDENTIAL",
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


def chart_claim_roles():
    fig, ax = plt.subplots(figsize=(5.8, 3.4))
    labels = ["可理解", "可记录", "可运营", "难替换"]
    phil = [4, 3, 3, 5]  # BRD-02
    journey = [5, 5, 5, 4]  # BRD-01
    x = np.arange(len(labels))
    w = 0.35
    ax.bar(x - w / 2, phil, w, color="#9B2433", label="哲学主张 BRD-02")
    ax.bar(x + w / 2, journey, w, color="#22646C", label="旅程主张 BRD-01")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 6)
    ax.set_ylabel("强度 (1-5)")
    ax.legend(fontsize=8, frameon=False)
    style_ax(ax, "双主张分工：哲学难抄，旅程可运营")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


def chart_channel_load():
    """Relative orchestration weight across 4 channels for pilot."""
    fig, ax = plt.subplots(figsize=(5.5, 3.4))
    ch = ["产品", "零售", "内容", "关系"]
    # weights for first 90d emphasis
    vals = [5, 5, 3, 4]
    colors = ["#9B2433", "#22646C", "#B8945A", "#B06030"]
    bars = ax.bar(ch, vals, color=colors, width=0.55)
    for b, v, note in zip(bars, vals, ["衣橱角色", "试香闭环", "标准语言", "香气档案"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.15, str(v), ha="center", fontweight="bold", fontsize=10)
        ax.text(b.get_x() + b.get_width() / 2, 0.35, note, ha="center", fontsize=7, color="#6E6E6E")
    ax.set_ylim(0, 6.5)
    ax.set_ylabel("编排权重 (试点期)")
    style_ax(ax, "四线权重：先产品×零售，再内容放大，关系沉淀")
    fig.patch.set_alpha(0)
    return fig_to_pil(fig)


# ═══════════════════════════════════════════════════════════
# SLIDE 1 — Proposition system
# ═══════════════════════════════════════════════════════════
def slide1():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "05 / PROPOSITION  ·  1 of 4",
        "主张锁定：一套系统，两个声部",
        "第四章已定进入点与美学；本章先把方向写成可检验主张，再拆进四条运营线。",
    )

    # Master line
    rr(d, [MX, 280, W - MX, 520], SOFT_R, 12)
    d.text((MX + 32, 305), "主句（对外可复述）", font=F["label"], fill=RED)
    d.text(
        (MX + 32, 355),
        "MFK：以精准的感性，陪你把欣赏变成签名——按时刻编排你的大师香氛衣柜。",
        font=F["h2"],
        fill=INK,
    )
    d.text(
        (MX + 32, 430),
        "检验：换成 Byredo / Le Labo 是否仍成立？→ 否（署名判断 + 衣橱导航 + 咨询档案三者绑死）",
        font=F["body"],
        fill=MUTED,
    )
    d.text(
        (MX + 32, 475),
        "禁用改写：不用「小众/高级感/氛围感/松弛奢华」撑主张；落到机制表述。",
        font=F["body"],
        fill=MUTED,
    )

    # Two voice cards
    rr(d, [MX, 560, MX + 1750, 1280], WHITE, 12)
    d.rectangle([MX, 560, MX + 1750, 572], fill=RED)
    d.text((MX + 36, 600), "声部 A · 哲学主张（BRD-02 主推）", font=F["h3"], fill=RED)
    d.text((MX + 36, 670), "精准的感性", font=F["h2"], fill=INK)
    for i, line in enumerate(
        [
            "要的不是更浓，是更准的克制",
            "多一分则腻，少一分则寡",
            "角色：选择标准 / 判断语言",
            "资产：Francis 署名 + 精准美学码",
            "主要服务：场景剧本「此刻刚好」",
            "风险：抽象 → 需内容与柜台示范补感知",
        ]
    ):
        d.text((MX + 36, 760 + i * 70), "·  " + line, font=F["body"], fill=INK)

    rr(d, [MX + 1790, 560, W - MX, 1280], WHITE, 12)
    d.rectangle([MX + 1790, 560, W - MX, 572], fill=TEAL)
    d.text((MX + 1826, 600), "声部 B · 旅程主张（BRD-01 确认）", font=F["h3"], fill=TEAL)
    d.text((MX + 1826, 670), "从试香到签名", font=F["h2"], fill=INK)
    for i, line in enumerate(
        [
            "先在肌肤上认识它，再拥有它",
            "把欣赏闭环成确定选择",
            "角色：转化路径 / 可运营机制",
            "资产：嗅觉咨询 + 个人香气档案",
            "主要服务：样品→正装转化",
            "风险：履约成本 → 用试点控规模",
        ]
    ):
        d.text((MX + 1826, 760 + i * 70), "·  " + line, font=F["body"], fill=INK)

    paste(img, chart_claim_roles(), (MX, 1320, MX + 1600, 1920))

    rr(d, [MX + 1640, 1320, W - MX, 1920], SOFT_G, 12)
    d.text((MX + 1676, 1360), "编排原则（进入四线前）", font=F["h3"], fill=GOLD)
    for i, line in enumerate(
        [
            "1. 任何触点必须同时听到两个声部：",
            "   标准（准）+ 路径（如何选到）",
            "2. 产品说话用衣橱角色，不用空话词",
            "3. 零售先完成选择，再完成成交",
            "4. 内容示范「精准」，不抒情堆砌",
            "5. 关系把每次咨询沉淀为档案复利",
            "",
            "下一页：四线编排总图",
        ]
    ):
        d.text((MX + 1676, 1430 + i * 48), line, font=F["body"], fill=INK)

    footer(d, "Source: PART04 锁定输入；BRD-01/02；竞品替换检验")
    save(img, "mfk_05_01_proposition.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 2 — Orchestration matrix
# ═══════════════════════════════════════════════════════════
def slide2():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "05 / ORCHESTRATION MAP  ·  2 of 4",
        "编排总图：同一方向如何进入产品、内容、零售、关系",
        "矩阵横轴=四条运营线；纵轴=三条编排主轴。每格只放一个主交付物，避免四线各说各话。",
    )

    paste(img, chart_channel_load(), (MX, 280, MX + 1400, 780))

    rr(d, [MX + 1440, 280, W - MX, 780], SOFT_T, 10)
    d.text((MX + 1476, 320), "读图规则", font=F["h3"], fill=TEAL)
    for i, line in enumerate(
        [
            "场景剧本：回答「此刻用哪支」",
            "衣橱角色：回答「这支在系统里是什么」",
            "咨询档案：回答「为何适合我」可复述",
            "",
            "试点期权重：产品=零售 > 关系 > 内容",
            "内容不领先开炮；先有可演示的选择闭环",
            "",
            "成功总计量：",
            "· 三秒选对率（零售）",
            "· 样品→正装转化（零售/关系）",
            "· 档案建档率（关系）",
            "· 主张复述正确率（内容）",
        ]
    ):
        d.text((MX + 1476, 380 + i * 28), line, font=F["small"], fill=INK)

    # Matrix
    d.text((MX, 820), "四线 × 三主轴 编排矩阵", font=F["h2"], fill=INK)
    cols = ["主轴 \\ 运营线", "产品", "零售", "内容", "关系运营"]
    col_w = [520, 720, 720, 720, 720]
    y = 880
    rr(d, [MX, y, W - MX, y + 52], SOFT, 4)
    x = MX + 12
    for h, w in zip(cols, col_w):
        d.text((x, y + 14), h, font=F["small"], fill=MUTED)
        x += w

    matrix = [
        (
            "场景剧本",
            "按时刻的香型组合包\n（通勤/约会/正式…）",
            "柜台「此刻导航」\n3问选香流程",
            "时刻选香短内容\n示范精准加减",
            "按场景推送补香\n与再试香提醒",
        ),
        (
            "衣橱角色",
            "540等重定角色：\n签名柱/日间柱/层叠柱",
            "陈列按衣橱分区\n非按爆款堆头",
            "产品故事写角色\n不写空话形容词",
            "会员衣橱可视化\n持有结构回顾",
        ),
        (
            "咨询档案",
            "试香装绑定档案ID\n可追到正装SKU",
            "咨询台记录偏好\n冲突与推荐理由",
            "咨询过程透明化\n内容（非剧透销售）",
            "个人香气档案沉淀\n复购与层叠建议",
        ),
    ]
    for i, row in enumerate(matrix):
        yy = 944 + i * 280
        bg = WHITE if i % 2 == 0 else SOFT
        rr(d, [MX, yy, W - MX, yy + 268], bg, 6)
        x = MX + 12
        for j, (cell, w) in enumerate(zip(row, col_w)):
            lines = cell.split("\n")
            col = RED if j == 0 else INK
            for k, line in enumerate(lines):
                d.text((x, yy + 40 + k * 40), line, font=F["body"] if j == 0 else F["small"], fill=col)
            x += w

    footer(d, "Source: PART04 编排主轴；PART02 时刻衣柜；PART03 BRD 双方向")
    save(img, "mfk_05_02_orchestration_map.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 3 — Product × Retail
# ═══════════════════════════════════════════════════════════
def slide3():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "05 / PRODUCT × RETAIL  ·  3 of 4",
        "产品×零售：让「三秒选对」在货架与柜台上发生",
        "产品负责衣橱角色清晰；零售负责把精准感性变成可走完的选择路径。",
    )

    # Product wardrobe roles
    d.text((MX, 280), "产品：衣橱角色重定（示意分工，非全量SKU表）", font=F["h2"], fill=INK)
    roles = [
        ("签名柱", "BR 540 等", "被记住的核心", "正式/高记忆时刻", RED, SOFT_R),
        ("日间柱", "Petit Matin 等", "干净得体在场", "通勤/职场", TEAL, SOFT_T),
        ("层叠柱", "轻盈/透明调", "按时刻加减", "约会前/换场", GOLD, SOFT_G),
        ("探索柱", "试香/旅行装", "低风险认识", "旅程入口", ORANGE, SOFT),
    ]
    rw = (W - 2 * MX - 3 * GAP) // 4
    for i, (role, ex, mean, scene, accent, bg) in enumerate(roles):
        x = MX + i * (rw + GAP)
        rr(d, [x, 340, x + rw, 780], bg, 10)
        d.rectangle([x, 340, x + rw, 352], fill=accent)
        d.text((x + 24, 380), role, font=F["h3"], fill=accent)
        d.text((x + 24, 450), ex, font=F["body"], fill=MUTED)
        d.text((x + 24, 520), mean, font=F["h3"], fill=INK)
        d.text((x + 24, 600), "主场景", font=F["label"], fill=MUTED)
        d.text((x + 24, 650), scene, font=F["body"], fill=INK)
        d.text((x + 24, 710), "禁止：一香万能叙事", font=F["small"], fill=ORANGE)

    # Retail path
    d.text((MX, 820), "零售：从进店到签名的选择闭环（配套入口）", font=F["h2"], fill=INK)
    steps = [
        ("01", "此刻三问", "场合 / 想被如何记得 / 忌口", "场景剧本启动"),
        ("02", "衣橱推荐", "给出 2–3 支角色清晰选项", "精准克制示范"),
        ("03", "肌肤试香", "记录反应与偏好冲突", "档案开始建档"),
        ("04", "签名决定", "正装或试香装带走+回访", "转化与复利"),
    ]
    sw = (W - 2 * MX - 3 * GAP) // 4
    for i, (n, t, b, note) in enumerate(steps):
        x = MX + i * (sw + GAP)
        rr(d, [x, 880, x + sw, 1280], WHITE, 10)
        d.text((x + 24, 910), n, font=F["num_sm"], fill=RED)
        d.text((x + 24, 980), t, font=F["h3"], fill=INK)
        wrap(d, b, (x + 24, 1060), F["body"], INK, sw - 48, 34)
        d.line([(x + 24, 1160), (x + sw - 24, 1160)], fill=LINE, width=1)
        d.text((x + 24, 1190), note, font=F["small"], fill=TEAL)
        if i < 3:
            d.polygon(
                [(x + sw + 4, 1050), (x + sw + GAP - 8, 1070), (x + sw + 4, 1090)],
                fill=LINE,
            )

    # Metrics + rules
    rr(d, [MX, 1340, W - MX, 1920], SOFT, 12)
    d.text((MX + 32, 1380), "产品×零售成功计量与硬规则", font=F["h3"], fill=INK)
    left = [
        "计量",
        "· 三秒初选命中率（导航后首推被试比例）",
        "· 样品→正装转化率（目标对照 25% 路径）",
        "· 衣橱角色识别率（顾客能说出柱位）",
        "· 咨询记录完整率（冲突+理由+推荐）",
    ]
    right = [
        "硬规则",
        "· 陈列按衣橱分区，禁止只堆 540",
        "· 话术先问场景，禁止先推爆款",
        "· 每支上柜必须标注衣橱角色",
        "· 无档案ID的试香不计入优化转化",
    ]
    for i, line in enumerate(left):
        d.text((MX + 32, 1450 + i * 70), line, font=F["body"], fill=TEAL if i == 0 else INK)
    for i, line in enumerate(right):
        d.text((MX + 1900, 1450 + i * 70), line, font=F["body"], fill=RED if i == 0 else INK)

    footer(d, "Source: PART04 场景主切+体验配套；PART01 转化 25% vs 4% 路径差")
    save(img, "mfk_05_03_product_retail.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 4 — Content × Relationship + handoff Part 06
# ═══════════════════════════════════════════════════════════
def slide4():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "05 / CONTENT × RELATIONSHIP  ·  4 of 4",
        "内容×关系：示范精准，并把选择沉淀为复利资产",
        "内容负责让「精准的感性」可感知；关系负责让「从试香到签名」可累积。",
    )

    # Content
    rr(d, [MX, 280, MX + 1750, 1100], WHITE, 12)
    d.rectangle([MX, 280, MX + 1750, 292], fill=GOLD)
    d.text((MX + 36, 320), "内容编排", font=F["h2"], fill=GOLD)
    d.text((MX + 36, 390), "示范「准」，不堆情绪形容词", font=F["h3"], fill=INK)
    rows = [
        ("内容类型", "时刻选香短片 / 衣橱角色图鉴 / 咨询过程透明条"),
        ("信息结构", "场景冲突 → 精准判断 → 一支角色清晰推荐"),
        ("美学执行", "嗅觉可感描述 + 视觉留白比例；禁紫雾光效贴纸风"),
        ("语言闸", "禁用：小众/高级感/氛围感/松弛奢华/老钱风…"),
        ("成功计量", "主张复述正确率；完播后「知如何选」自报提升"),
        ("不做", "先大传播再补逻辑；用单爆款替代衣橱系统叙事"),
    ]
    for i, (a, b) in enumerate(rows):
        yy = 460 + i * 90
        d.text((MX + 36, yy), a, font=F["label"], fill=MUTED)
        d.text((MX + 280, yy), b, font=F["body"], fill=INK)

    # Relationship
    rr(d, [MX + 1790, 280, W - MX, 1100], WHITE, 12)
    d.rectangle([MX + 1790, 280, W - MX, 292], fill=TEAL)
    d.text((MX + 1826, 320), "关系运营", font=F["h2"], fill=TEAL)
    d.text((MX + 1826, 390), "个人香气档案 = 复利中枢", font=F["h3"], fill=INK)
    rows2 = [
        ("档案字段", "偏好冲突 / 忌口 / 场景频次 / 已试 / 已拥有"),
        ("触达逻辑", "按场景补香提醒；层叠建议；回访试香"),
        ("会员价值", "衣橱可视化 + 签名进度，而非积分话术"),
        ("与零售衔接", "档案ID贯通试香装与正装履约"),
        ("成功计量", "建档率；90天复访；档案驱动转化占比"),
        ("不做", "无档案群发促销；把关系做成纯折扣池"),
    ]
    for i, (a, b) in enumerate(rows2):
        yy = 460 + i * 90
        d.text((MX + 1826, yy), a, font=F["label"], fill=MUTED)
        wrap(d, b, (MX + 2100, yy), F["body"], INK, 1400, 28)

    # Coherence + handoff
    d.text((MX, 1140), "四线一致性检验 + 移交 PART 06", font=F["h2"], fill=INK)
    checks = [
        ("一致性", "四线是否都在回答「哪支适合我、为什么」"),
        ("可替换性", "拿掉 MFK 署名与衣橱导航后主张是否崩塌"),
        ("可运营", "咨询步骤能否跨店复制且可记录"),
        ("可计量", "是否有转化/建档/复述三类指标看板"),
    ]
    cw = (W - 2 * MX - 3 * GAP) // 4
    for i, (t, b) in enumerate(checks):
        x = MX + i * (cw + GAP)
        rr(d, [x, 1200, x + cw, 1480], SOFT_T if i % 2 == 0 else SOFT_G, 8)
        d.text((x + 20, 1240), t, font=F["h3"], fill=TEAL)
        wrap(d, b, (x + 20, 1320), F["body"], INK, cw - 40, 34)

    rr(d, [MX, 1520, W - MX, 1920], SOFT_R, 12)
    d.text((MX + 32, 1560), "移交 PART 06 · 90天试点输入", font=F["h3"], fill=RED)
    handoff = [
        ("试点命题", "场景导航+试香档案能否提升样品→正装转化"),
        ("必做触点", "1家/渠道试点柜台 + 时刻内容条 + 档案最小闭环"),
        ("核心KPI", "转化率 · 三秒命中 · 建档率 · 主张复述"),
        ("止损条件", "空话回潮 / 无档案转化 / 履约成本失控 → 停扩"),
    ]
    hw = (W - 2 * MX - 3 * GAP - 64) // 4
    for i, (a, b) in enumerate(handoff):
        x = MX + 32 + i * (hw + GAP)
        rr(d, [x, 1630, x + hw, 1860], WHITE, 8)
        d.text((x + 16, 1660), a, font=F["label"], fill=RED)
        wrap(d, b, (x + 16, 1720), F["body"], INK, hw - 32, 32)

    footer(d, "Source: PART05 主张与矩阵；BW 禁用表；PART04 美学码与进入锁定")
    save(img, "mfk_05_04_content_relationship.png")


if __name__ == "__main__":
    slide1()
    slide2()
    slide3()
    slide4()
    print("DONE: PART 05 × 4")
