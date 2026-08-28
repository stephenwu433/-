#!/usr/bin/env python3
"""
Clarity fix pack — lock lexicon hierarchy across priority slides.
Locked definitions (ONLY these):
  品牌问题: 消费者欣赏MFK，却难以确定哪一支真正适合自己
  战略定位: 私人香气表达的精准权威
  品牌母题: 精准的感性
  产品/场景系统: 时刻衣柜
  体验机制: 从试香到签名
  消费者表达: 让香气，准确表达复杂的你
"""
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
MUTED = (90, 90, 90)
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

BG_COVER = Path("/home/ubuntu/.cursor/projects/workspace/assets/38a58645-eda5-4f5b-9a7e-0e2a7c23d3d2.png")
BG_DARK = Path("/home/ubuntu/.cursor/projects/workspace/assets/ea789c2c-218c-4b09-ab49-46393f3059c0.png")
if not BG_DARK.exists():
    BG_DARK = Path("/home/ubuntu/.cursor/projects/workspace/assets/49a9cc62-4bc4-4ae4-a911-53783998238c.png")

_CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(_CJK)
FP = fm.FontProperties(fname=_CJK)
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [fm.FontProperties(fname=_CJK).get_name(), "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# Locked lexicon
POS = "私人香气表达的精准权威"
MOTIF = "精准的感性"
SYSTEM = "时刻衣柜"
JOURNEY = "从试香到签名"
PROMISE = "让香气，准确表达复杂的你。"
PROBLEM = "消费者欣赏MFK，却难以确定哪一支真正适合自己"
AUDIENCE = "对MFK已有认知、正在多品牌比较、需要通过试香完成首购或跨香型购买的高端香水消费者"


def fonts():
    s = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
    n = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    b = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
    i = "/usr/share/fonts/truetype/inter/Inter-Regular.ttf"
    ib = "/usr/share/fonts/truetype/inter/Inter-Bold.ttf"
    return {
        "brand": ImageFont.truetype(i, 22),  # Latin only
        "eyebrow": ImageFont.truetype(b, 28, index=2),  # CJK — never Inter
        "title": ImageFont.truetype(s, 54, index=2),
        "hero": ImageFont.truetype(s, 68, index=2),
        "h2": ImageFont.truetype(s, 34, index=2),
        "h3": ImageFont.truetype(b, 26, index=2),
        "body": ImageFont.truetype(n, 24, index=2),
        "small": ImageFont.truetype(n, 20, index=2),
        "tiny": ImageFont.truetype(n, 16, index=2),
        "sub": ImageFont.truetype(n, 26, index=2),
        "label": ImageFont.truetype(b, 18, index=2),  # CJK — never Inter
        "num": ImageFont.truetype(ib, 36),
        "row": ImageFont.truetype(n, 30, index=2),
        "row_b": ImageFont.truetype(b, 32, index=2),
        "foot": ImageFont.truetype(i, 18),
    }


F = fonts()


def rr(d, box, fill, r=12):
    d.rounded_rectangle(box, radius=r, fill=fill)


def wrap(d, text, xy, font, fill, max_w, lh):
    """Word-wrap; flatten newlines so Pillow textlength never sees multiline."""
    x, y = xy
    text = str(text).replace("\r", " ").replace("\n", " ")
    line = ""
    for ch in text:
        test = line + ch
        if d.textlength(test, font=font) <= max_w:
            line = test
        else:
            if line:
                d.text((x, y), line, font=font, fill=fill)
                y += lh
            line = ch
    if line:
        d.text((x, y), line, font=font, fill=fill)
    return y


def header(d, code, title, question, dark=False):
    c1, c2, c3 = ((MUTED, INK, MUTED) if not dark else ((160, 148, 140), (245, 242, 235), (180, 168, 160)))
    d.text((MX, 40), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=c1)
    d.text((W - MX - 200, 40), "LVMH BEAUTY", font=F["brand"], fill=c1)
    d.text((MX, 88), code, font=F["label"], fill=RED if not dark else GOLD)
    d.text((MX, 118), title, font=F["title"], fill=c2)
    d.rectangle([MX, 198, MX + 100, 204], fill=GOLD)
    d.text((MX, 220), question, font=F["sub"], fill=c3)


def footer(d, src, dark=False):
    c = MUTED if not dark else (150, 140, 132)
    d.line([(MX, FY - 16), (W - MX, FY - 16)], fill=LINE if not dark else (80, 50, 50), width=2)
    d.text((MX, FY), src, font=F["tiny"], fill=c)
    d.text((W - MX - 360, FY), "MFK Brand Strategy  |  CONFIDENTIAL", font=F["tiny"], fill=c)


def save(img, name):
    img.save(OUT / name, "PNG")
    img.resize((1920, 1080), Image.Resampling.LANCZOS).save(
        OUT / name.replace(".png", "_1920.png"), "PNG"
    )
    img.save(ART / name, "PNG")
    print("saved", name)


GOLD = (184, 148, 90)


# ═══════════════════════════════════════════════════════════
# 1) Cover — denser, locked lexicon
# ═══════════════════════════════════════════════════════════
def slide_cover():
    bg = Image.open(BG_COVER).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(0, 1750):
        a = int(90 * (1 - i / 1750))
        od.line([(i, 0), (i, H)], fill=(245, 242, 235, a))
    img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)

    d.text((MX, 88), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED)
    d.text((W - MX - 240, 88), "LVMH BEAUTY", font=F["brand"], fill=MUTED)

    d.text((MX, 400), "LVMH BEAUTY  ·  未来 1—3 年香氛美学与体验创新方案", font=F["eyebrow"], fill=RED)
    wrap(d, f"MFK品牌全案：{PROMISE}", (MX, 480), F["hero"], INK, 1780, 86)
    wrap(d, "以调香师专业与嗅觉衣橱，帮助消费者确认属于自己的标志性香气。", (MX, 700), F["sub"], INK, 1680, 44)

    # Locked hierarchy — labeled, not competing "directions"
    rows = [
        ("战略定位", POS, RED),
        ("品牌母题", MOTIF, INK),
        ("产品系统", SYSTEM, INK),
        ("体验机制", JOURNEY, INK),
    ]
    y = 860
    for lab, val, col in rows:
        d.text((MX, y), lab, font=F["label"], fill=MUTED)
        d.text((MX + 220, y - 4), val, font=F["row_b"] if lab == "战略定位" else F["row"], fill=col)
        if lab == "战略定位":
            tw = d.textlength(val, font=F["row_b"])
            d.rectangle([MX + 220, y + 42, MX + 220 + int(tw), y + 46], fill=GOLD)
        y += 70

    d.text((MX, 1200), "品牌问题", font=F["label"], fill=MUTED)
    wrap(d, PROBLEM, (MX + 220, 1196), F["body"], INK, 1500, 34)

    d.text((MX, 1980), "MFK × LVMH BEAUTY  /  BRAND GROWTH SYSTEM", font=F["foot"], fill=MUTED)
    save(img, "mfk_00_cover.png")


# ═══════════════════════════════════════════════════════════
# 2) Strategic answer — lexicon table (was page 2)
# ═══════════════════════════════════════════════════════════
def slide_strategic_answer():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "00 / STRATEGIC ANSWER",
        "一页看懂品牌方向（唯一语言层级）",
        "后面所有页面只允许使用下表定义；近义说法一律停用。",
    )

    rr(d, [MX, 290, W - MX, 430], SOFT_R, 10)
    d.text((MX + 28, 315), "评委应能复述的一句话", font=F["label"], fill=RED)
    wrap(
        d,
        f"MFK 要成为「{POS}」：用「{MOTIF}」作判断标准，用「{SYSTEM}」编排场景选择，用「{JOURNEY}」完成确定选择。",
        (MX + 28, 360),
        F["h3"],
        INK,
        W - 2 * MX - 60,
        40,
    )

    # Lexicon table
    d.text((MX, 470), "锁定层级表（全案唯一口径）", font=F["h2"], fill=INK)
    headers = ["层级", "锁定说法", "负责什么", "不许再写成"]
    widths = [420, 900, 900, 1100]
    y = 540
    rr(d, [MX, y, W - MX, y + 52], SOFT, 4)
    x = MX + 16
    for h, w in zip(headers, widths):
        d.text((x, y + 14), h, font=F["small"], fill=MUTED)
        x += w

    rows = [
        ("品牌问题", PROBLEM[:18] + "…", "要解决的购买决策缺口", "情绪同质化等泛问题抢位"),
        ("战略定位", POS, "长期要占的认知位置", "精准选择权威 / 标志性权威 混用"),
        ("品牌母题", MOTIF, "品牌哲学与判断标准", "当定位、当口号、当系统名"),
        ("产品/场景系统", SYSTEM, "产品与场景如何编排", "当品牌方向"),
        ("体验机制", JOURNEY, "如何把欣赏变成确定选择", "当战略定位"),
        ("消费者表达", PROMISE.replace("。", ""), "对外承诺句", "与定位抢同一层级"),
    ]
    for i, row in enumerate(rows):
        yy = 600 + i * 140
        bg = SOFT_R if i == 1 else (WHITE if i % 2 == 0 else SOFT_T)
        rr(d, [MX, yy, W - MX, yy + 128], bg, 6)
        x = MX + 16
        for j, (cell, w) in enumerate(zip(row, widths)):
            col = RED if i == 1 and j <= 1 else INK
            font = F["h3"] if j == 1 and i == 1 else F["body"]
            wrap(d, cell, (x, yy + 40), font, col, w - 24, 32)
            x += w

    rr(d, [MX, 1480, W - MX, 1920], SOFT_G, 12)
    d.text((MX + 28, 1520), "三者分工（钉死）", font=F["h3"], fill=GOLD)
    cols = [
        (MOTIF, "哲学 / 判断标准", "多一分则腻，少一分则寡"),
        (SYSTEM, "产品与场景编排", "按时刻回答「此刻用哪支」"),
        (JOURNEY, "体验路径", "试香→建档→签名确认"),
    ]
    cw = (W - 2 * MX - 2 * GAP - 56) // 3
    for i, (a, b, c) in enumerate(cols):
        x = MX + 28 + i * (cw + GAP)
        rr(d, [x, 1600, x + cw, 1860], WHITE, 8)
        d.text((x + 20, 1630), a, font=F["h3"], fill=RED)
        d.text((x + 20, 1700), b, font=F["body"], fill=INK)
        wrap(d, c, (x + 20, 1760), F["small"], MUTED, cw - 40, 30)

    footer(d, "规则：三者不再平行争夺「品牌方向」；战略定位仅保留「私人香气表达的精准权威」")
    save(img, "mfk_00_strategic_answer.png")


# ═══════════════════════════════════════════════════════════
# Target consumer lock
# ═══════════════════════════════════════════════════════════
def slide_audience():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "01 / TARGET CONSUMER",
        "目标消费者锁定（本项目唯一服务对象）",
        "数据可来自不同研究，但全部必须服务同一购买决策。",
    )

    rr(d, [MX, 300, W - MX, 560], SOFT_R, 12)
    d.text((MX + 36, 340), "锁定定义", font=F["label"], fill=RED)
    wrap(d, AUDIENCE, (MX + 36, 400), F["h2"], INK, W - 2 * MX - 80, 52)
    d.text((MX + 36, 500), "年龄仅在有真实证据时再写入；本页不预设 25–35。", font=F["body"], fill=MUTED)

    # In / evidence role
    d.text((MX, 620), "证据如何服务同一对象（防口径打架）", font=F["h2"], fill=INK)
    rows = [
        ("可用证据", "扮演角色", "不可直接当成"),
        ("Gen Z 持香数量", "说明衣柜行为结构在变", "本项目唯一年龄目标"),
        ("欧洲层叠渗透", "说明场景轮换行为存在", "本项目唯一地理市场"),
        ("Niche 份额对照", "说明选择效率战场拥挤", "MFK 已占位证明"),
        ("样品→正装转化差", "说明路径决定转化", "全国渠道已验证结果"),
        ("语料冲突簇", "支持方向进入下一轮验证", "市场总体认同证明"),
    ]
    widths = [700, 1200, 1400]
    y = 700
    rr(d, [MX, y, W - MX, y + 52], SOFT, 4)
    x = MX + 16
    for h, w in zip(rows[0], widths):
        d.text((x, y + 14), h, font=F["small"], fill=MUTED)
        x += w
    for i, row in enumerate(rows[1:]):
        yy = 760 + i * 140
        rr(d, [MX, yy, W - MX, yy + 128], WHITE if i % 2 == 0 else SOFT_T, 6)
        x = MX + 16
        for j, (cell, w) in enumerate(zip(row, widths)):
            d.text((x, yy + 44), cell, font=F["body"], fill=INK)
            x += w

    rr(d, [MX, 1520, W - MX, 1920], SOFT_G, 10)
    d.text((MX + 28, 1560), "优先解决的一次购买决策", font=F["h3"], fill=TEAL)
    wrap(
        d,
        f"{PROBLEM} → 通过「{JOURNEY}」完成首购或跨香型购买确认，并形成可复述的 Why MFK。",
        (MX + 28, 1640),
        F["h3"],
        INK,
        W - 2 * MX - 60,
        44,
    )
    d.text((MX + 28, 1780), f"对齐：战略定位「{POS}」· 系统「{SYSTEM}」· 母题「{MOTIF}」", font=F["body"], fill=MUTED)

    footer(d, "证据状态规则：事实/外部研究/语料信号/策略推断/试点目标 — 后页图表必须标注")
    save(img, "mfk_01_target_consumer.png")


# ═══════════════════════════════════════════════════════════
# Part 02 proposition — locked language
# ═══════════════════════════════════════════════════════════
def slide_p02_proposition():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "02 / MFK PROPOSITION",
        "证据收束：产品系统落在「时刻衣柜」",
        f"这是产品/场景系统名，不是战略定位。战略定位仍是「{POS}」。",
    )

    rr(d, [MX, 290, W - MX, 520], SOFT_R, 12)
    d.text((MX + 32, 320), "本页结论（产品系统）", font=F["label"], fill=RED)
    d.text((MX + 32, 380), f"把 MFK 从「一支爆款代名词」，收成可运营的「{SYSTEM}」。", font=F["h2"], fill=INK)
    d.text((MX + 32, 460), f"服务战略定位：{POS}", font=F["body"], fill=MUTED)

    triad = [
        ("主攻", "场景层", f"用{SYSTEM}回答「此刻用哪支」"),
        ("配套", "资产重组", "540 等按衣橱角色分工"),
        ("避开", "词语红海", "不把空话形容词当主战场"),
    ]
    tw = (W - 2 * MX - 2 * GAP) // 3
    for i, (a, b, c) in enumerate(triad):
        x = MX + i * (tw + GAP)
        rr(d, [x, 560, x + tw, 860], WHITE, 10)
        d.rectangle([x, 560, x + tw, 572], fill=RED if i == 0 else (TEAL if i == 1 else GOLD))
        d.text((x + 28, 610), a, font=F["label"], fill=MUTED)
        d.text((x + 28, 670), b, font=F["h2"], fill=INK)
        wrap(d, c, (x + 28, 760), F["body"], MUTED, tw - 56, 34)

    # Lexicon reminder
    rr(d, [MX, 920, W - MX, 1280], SOFT_T, 10)
    d.text((MX + 28, 960), "语言对齐检查（本页只谈系统，不改定位）", font=F["h3"], fill=TEAL)
    checks = [
        f"✓ 战略定位 = {POS}",
        f"✓ 品牌母题 = {MOTIF}（判断标准）",
        f"✓ 产品系统 = {SYSTEM}",
        f"✓ 体验机制 = {JOURNEY}（下一章验证后编排）",
        f"✗ 不用「精准选择权威」替换定位句",
        f"✗ 不把{SYSTEM}写成品牌方向",
    ]
    for i, c in enumerate(checks):
        d.text((MX + 28 + (i % 2) * 1700, 1060 + (i // 2) * 60), c, font=F["body"], fill=INK)

    rr(d, [MX, 1340, W - MX, 1920], SOFT_G, 10)
    d.text((MX + 28, 1400), "对目标消费者的含义", font=F["h3"], fill=GOLD)
    wrap(d, AUDIENCE, (MX + 28, 1480), F["body"], INK, W - 2 * MX - 60, 40)
    wrap(
        d,
        f"他们缺的不是更多香，而是一套能说清「为何适合我」的判断系统——{SYSTEM}是编排，{MOTIF}是标准，{JOURNEY}是路径。",
        (MX + 28, 1640),
        F["h3"],
        INK,
        W - 2 * MX - 60,
        44,
    )

    footer(d, "证据状态：策略推断（由 PART02 市场/消费者/竞品收束）· 待 PART03 系统筛选后进入验证")
    save(img, "mfk_02_mfk_proposition.png")


# ═══════════════════════════════════════════════════════════
# Part 03 v5 — soften claim (was "命题成立")
# ═══════════════════════════════════════════════════════════
def slide_p03_close():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "03 / DIRECTION CONVERGENCE  ·  5 of 5",
        "系统筛选结论：内部证据链通过，进入真人概念验证",
        "本章是「系统筛选与方向收敛」，不是市场总体验证。",
    )

    # Softened verdict
    rr(d, [MX, 290, W - MX, 520], SOFT_G, 12)
    d.text((MX + 32, 320), "本页裁定（降级后的正确力度）", font=F["label"], fill=TEAL)
    wrap(
        d,
        "内部证据链通过：主方向进入真人概念验证，备选方向保留。",
        (MX + 32, 380),
        F["h2"],
        INK,
        W - 2 * MX - 80,
        48,
    )
    d.text((MX + 32, 470), f"主方向：{MOTIF}（母题）+ {JOURNEY}（体验）服务定位「{POS}」", font=F["body"], fill=MUTED)

    # What NOT proven
    d.text((MX, 560), "尚未证明（禁止在本页或后页夸大）", font=F["h2"], fill=INK)
    nots = [
        "市场总体认同该方向",
        "消费者会因此购买",
        "MFK 已经拥有该认知",
        "该方向无法被 Byredo / Le Labo 替代（仅 CHK 不可替换=否，属语料/主张层）",
    ]
    for i, t in enumerate(nots):
        x = MX + (i % 2) * 1750
        y = 640 + (i // 2) * 120
        rr(d, [x, y, x + 1680, y + 100], SOFT_R, 8)
        d.text((x + 28, y + 32), "尚未证明 ·  " + t, font=F["body"], fill=RED)

    # Count objects clarification
    d.text((MX, 920), "计数对象不同，不可连续解读为同一种统计", font=F["h2"], fill=INK)
    objs = [
        ("语料池", "研究输入", "语料信号"),
        ("证据条 49", "跨平台可回溯条目", "语料信号"),
        ("标签 26", "编码词典结构", "方法设定"),
        ("洞察簇 5", "张力命名产出", "语料信号"),
        ("候选 DIR 4", "方向草案", "策略推断"),
        ("确认 BRD 2", "过闸方向", "策略推断"),
    ]
    ow = (W - 2 * MX - 5 * GAP) // 6
    for i, (a, b, c) in enumerate(objs):
        x = MX + i * (ow + GAP)
        rr(d, [x, 1000, x + ow, 1320], WHITE, 8)
        d.text((x + 16, 1040), a, font=F["h3"], fill=INK)
        wrap(d, b, (x + 16, 1120), F["small"], MUTED, ow - 32, 28)
        d.text((x + 16, 1240), c, font=F["label"], fill=TEAL)

    # Mapping to locked lexicon
    rr(d, [MX, 1380, W - MX, 1920], SOFT_T, 12)
    d.text((MX + 28, 1420), "收敛映射到锁定层级", font=F["h3"], fill=TEAL)
    maps = [
        (f"BRD-02 → 品牌母题「{MOTIF}」", "主推：判断标准"),
        (f"BRD-01 → 体验机制「{JOURNEY}」", "确认：转化路径"),
        (f"产品系统仍是「{SYSTEM}」", "场景编排，非定位"),
        (f"战略定位不变「{POS}」", "长期认知位置"),
    ]
    mw = (W - 2 * MX - 3 * GAP - 56) // 4
    for i, (a, b) in enumerate(maps):
        x = MX + 28 + i * (mw + GAP)
        rr(d, [x, 1520, x + mw, 1840], WHITE, 8)
        wrap(d, a, (x + 16, 1560), F["body"], INK, mw - 32, 34)
        d.text((x + 16, 1740), b, font=F["small"], fill=MUTED)

    footer(d, "证据状态：语料信号 + 策略推断 · 下一动作=真人概念验证（PART06），非市场独占宣称")
    save(img, "mfk_03_v5_q3_validate.png")


def slide_p03_contract():
    """Update Part3 page1 naming."""
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "03 / SYSTEM SCREENING  ·  1 of 5",
        "系统筛选与方向收敛（不是市场总验证）",
        f"任务：把 PART02「{SYSTEM}」命题，收敛为可进入真人验证的母题+体验组合。",
    )

    rr(d, [MX, 290, W - MX, 480], SOFT_R, 10)
    d.text((MX + 28, 320), "PART02 输入（待筛选）", font=F["label"], fill=RED)
    d.text((MX + 28, 380), f"产品系统假设：{SYSTEM}｜服务定位：{POS}", font=F["h3"], fill=INK)
    d.text((MX + 28, 440), "本章只回答：内部语料证据链是否支持进入下一轮验证。", font=F["body"], fill=MUTED)

    qs = [
        ("Q1", "冲突是否可命名可回溯？", "通过→场景系统可编码", "语料信号"),
        ("Q2", "词语层主张是否被闸杀？", "通过→避开词语红海成立", "方法+语料"),
        ("Q3", "母题+体验能否过专属闸？", "通过→进入真人验证", "策略推断"),
    ]
    qw = (W - 2 * MX - 2 * GAP) // 3
    for i, (qid, q, a, st) in enumerate(qs):
        x = MX + i * (qw + GAP)
        rr(d, [x, 540, x + qw, 1100], WHITE, 10)
        d.text((x + 28, 580), qid, font=F["label"], fill=TEAL)
        wrap(d, q, (x + 28, 650), F["h3"], INK, qw - 56, 40)
        wrap(d, a, (x + 28, 820), F["body"], MUTED, qw - 56, 36)
        d.text((x + 28, 1000), "证据状态 · " + st, font=F["small"], fill=GOLD)

    # Object warning
    rr(d, [MX, 1180, W - MX, 1560], SOFT_G, 10)
    d.text((MX + 28, 1220), "读数警告", font=F["h3"], fill=GOLD)
    wrap(
        d,
        "语料池、证据条、标签数、洞察簇、候选方向是不同对象。后页图表禁止把它们画成同一统计口径的「连续下降漏斗真相」。漏斗只表示筛选阶段，不表示同一总体的转化率。",
        (MX + 28, 1300),
        F["body"],
        INK,
        W - 2 * MX - 60,
        40,
    )
    d.text((MX + 28, 1480), "禁止用语：命题成立 / 市场已验证 / 竞品无法替代（绝对句）", font=F["body"], fill=RED)

    rr(d, [MX, 1620, W - MX, 1920], SOFT_T, 10)
    d.text((MX + 28, 1680), "筛选后允许输出的最大结论", font=F["label"], fill=TEAL)
    wrap(
        d,
        f"内部证据链支持「{MOTIF}」作为母题、「{JOURNEY}」作为体验机制，服务定位「{POS}」，进入真人概念验证；备选方向保留。",
        (MX + 28, 1740),
        F["h3"],
        INK,
        W - 2 * MX - 60,
        42,
    )

    footer(d, "章节定位：系统筛选与方向收敛 · 非市场总体验证")
    save(img, "mfk_03_v1_contract.png")


# ═══════════════════════════════════════════════════════════
# Part 05 proposition — locked dual voice
# ═══════════════════════════════════════════════════════════
def slide_p05_prop():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "05 / PROPOSITION LOCK",
        "主张锁定：定位一句，母题与体验两个声部",
        "禁止再把母题/体验/系统写成第二个「品牌方向」。",
    )

    rr(d, [MX, 290, W - MX, 480], SOFT_R, 12)
    d.text((MX + 32, 320), "战略定位（唯一）", font=F["label"], fill=RED)
    d.text((MX + 32, 380), POS, font=F["hero"], fill=INK)
    d.text((MX + 32, 470), f"消费者表达：{PROMISE}", font=F["body"], fill=MUTED)

    # Two voices
    rr(d, [MX, 540, MX + 1750, 1280], WHITE, 12)
    d.rectangle([MX, 540, MX + 1750, 552], fill=RED)
    d.text((MX + 36, 590), f"声部 A · 品牌母题", font=F["h3"], fill=RED)
    d.text((MX + 36, 670), MOTIF, font=F["h2"], fill=INK)
    for i, line in enumerate(
        [
            "层级：品牌母题（哲学/判断标准）",
            "要的不是更浓，是更准的克制",
            "服务：时刻选择时的判断语言",
            "不负责：单独充当战略定位",
        ]
    ):
        d.text((MX + 36, 780 + i * 80), "·  " + line, font=F["body"], fill=INK)

    rr(d, [MX + 1790, 540, W - MX, 1280], WHITE, 12)
    d.rectangle([MX + 1790, 540, W - MX, 552], fill=TEAL)
    d.text((MX + 1826, 590), "声部 B · 体验机制", font=F["h3"], fill=TEAL)
    d.text((MX + 1826, 670), JOURNEY, font=F["h2"], fill=INK)
    for i, line in enumerate(
        [
            "层级：体验机制（转化路径）",
            "欣赏 → 确定选择 → 可复述理由",
            "服务：样品到正装与档案复利",
            "不负责：单独充当战略定位",
        ]
    ):
        d.text((MX + 1826, 780 + i * 80), "·  " + line, font=F["body"], fill=INK)

    rr(d, [MX, 1340, W - MX, 1920], SOFT_G, 12)
    d.text((MX + 32, 1380), f"产品系统「{SYSTEM}」如何接入", font=F["h3"], fill=GOLD)
    wrap(
        d,
        f"{SYSTEM}是产品/场景编排系统：用母题「{MOTIF}」作判断标准，用体验「{JOURNEY}」完成确认，共同服务定位「{POS}」。",
        (MX + 32, 1480),
        F["h3"],
        INK,
        W - 2 * MX - 64,
        44,
    )
    d.text((MX + 32, 1680), f"目标消费者：{AUDIENCE}", font=F["body"], fill=MUTED)
    d.text((MX + 32, 1760), "竞品替换检验：拿掉 MFK 署名判断与衣橱导航后，主张应无法原样成立。", font=F["body"], fill=MUTED)

    footer(d, "语言锁定页 · 后页四线编排不得另起近义定位句")
    save(img, "mfk_05_01_proposition.png")


# ═══════════════════════════════════════════════════════════
# Wardrobe logic — six-grid judgment
# ═══════════════════════════════════════════════════════════
def slide_wardrobe_logic():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "05 / MOMENT WARDROBE LOGIC",
        f"「{SYSTEM}」专属来自判断标准，不是场景名称",
        "每个时刻必须跑完：任务→冲突→嗅觉标准→MFK对应→为何适合→试香确认。",
    )

    # Table header
    headers = ["时刻任务", "消费者冲突", "嗅觉判断标准", "MFK对应（示意）", "为何适合", "试香确认"]
    # 4 moments
    rows = [
        ["通勤在场", "要存在感×不能浓烈", "干净、克制扩散、得体", "日间柱\n(如 Petit Matin)", f"{MOTIF}：准而不压", "办公环境回访\n2小时观感"],
        ["约会记忆", "想被记住×怕甜腻", "签名清晰、甜感可控", "签名/层叠柱\n按肌肤加减", "记忆点来自准\n不是更浓", "肌肤干燥后\n再评记忆点"],
        ["正式场合", "贵气×不炫耀", "结构清晰、不过度甜", "签名柱\n(如 BR 540 角色化)", "贵气来自比例\n非炫耀扩散", "场合前后对比\n是否压迫他人"],
        ["旅行/换场", "想表达×怕选错", "可层叠、易携带确认", "探索柱\n试香/旅行装", "低风险认识\n再进衣橱", "旅行装日记\n→正装决策"],
    ]

    col_w = [520, 580, 620, 560, 560, 560]
    y = 300
    rr(d, [MX, y, W - MX, y + 56], SOFT, 4)
    x = MX + 8
    for h, w in zip(headers, col_w):
        d.text((x, y + 16), h, font=F["small"], fill=MUTED)
        x += w

    for i, row in enumerate(rows):
        yy = 368 + i * 280
        rr(d, [MX, yy, W - MX, yy + 268], WHITE if i % 2 == 0 else SOFT_T, 6)
        x = MX + 8
        for j, (cell, w) in enumerate(zip(row, col_w)):
            for k, line in enumerate(cell.split("\n")):
                d.text((x, yy + 40 + k * 40), line, font=F["body"] if j == 0 else F["small"], fill=RED if j == 0 else INK)
            x += w

    rr(d, [MX, 1520, W - MX, 1920], SOFT_R, 10)
    d.text((MX + 28, 1560), "MFK 专属性声明", font=F["h3"], fill=RED)
    wrap(
        d,
        f"通勤/约会/正式/旅行是通用场景名；MFK 专属来自「{MOTIF}」判断标准 + 调香师署名资产 + 「{JOURNEY}」确认闭环。缺判断标准的场景表 = 普通推荐，不构成定位。",
        (MX + 28, 1650),
        F["body"],
        INK,
        W - 2 * MX - 60,
        40,
    )
    d.text((MX + 28, 1800), f"对齐战略定位：{POS}", font=F["body"], fill=MUTED)

    footer(d, "证据状态：策略推断（示意SKU可替换为正式产品表）· 需柜台实测校准")
    save(img, "mfk_05_wardrobe_logic.png")


# ═══════════════════════════════════════════════════════════
# Case close + ending with locked lexicon
# ═══════════════════════════════════════════════════════════
def slide_case_close():
    bg = Image.open(BG_DARK).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    img = bg.copy()
    d = ImageDraw.Draw(img)
    CREAM2 = (245, 242, 235)
    SOFT2 = (200, 188, 178)
    MUTED2 = (160, 148, 140)

    d.text((MX, 80), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED2)
    d.text((W - MX - 220, 80), "LVMH BEAUTY", font=F["brand"], fill=MUTED2)
    d.text((MX, 200), "00 / CASE CLOSE", font=F["label"], fill=GOLD)
    d.text((MX, 250), "全案收束：评委应记住的唯一层级", font=F["hero"], fill=CREAM2)
    d.rectangle([MX, 350, MX + 120, 356], fill=GOLD)

    beats = [
        ("战略定位", POS),
        ("品牌母题", MOTIF),
        ("产品系统", SYSTEM),
        ("体验机制", JOURNEY),
        ("消费者表达", PROMISE.replace("。", "")),
        ("下一步", "真人概念验证，非市场独占宣称"),
    ]
    bw = (W - 2 * MX - 5 * GAP) // 6
    for i, (a, b) in enumerate(beats):
        x = MX + i * (bw + GAP)
        card = Image.new("RGBA", (bw, 480), (40, 18, 20, 170))
        img.paste(card, (x, 420), card)
        d = ImageDraw.Draw(img)
        d.text((x + 16, 450), a, font=F["label"], fill=GOLD)
        wrap(d, b.replace("\n", ""), (x + 16, 520), F["h3"], CREAM2, bw - 32, 36)

    d = ImageDraw.Draw(img)
    wrap(
        d,
        f"MFK 要成为「{POS}」：用「{MOTIF}」判断，用「{SYSTEM}」编排，用「{JOURNEY}」确认。",
        (MX, 980),
        F["h2"],
        CREAM2,
        W - 2 * MX,
        48,
    )
    d.text((MX, 1140), PROMISE, font=F["hero"], fill=CREAM2)
    wrap(
        d,
        "内部证据链已通过筛选；方向进入真人验证。过闸再扩面——方向成立 ≠ 规模成立。",
        (MX, 1280),
        F["body"],
        SOFT2,
        W - 2 * MX,
        36,
    )
    d.text((MX, 1780), "EVIDENCE-LED  ·  HUMAN-VERIFIED  ·  PRIORITIZE VALIDATION", font=F["foot"], fill=MUTED2)
    save(img, "mfk_00_case_close.png")


def slide_ending():
    bg = Image.open(BG_DARK).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    img = bg.copy()
    d = ImageDraw.Draw(img)
    CREAM2 = (245, 242, 235)
    SOFT2 = (200, 188, 178)
    MUTED2 = (160, 148, 140)

    d.text((MX, 88), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED2)
    d.text((W - MX - 240, 88), "LVMH BEAUTY", font=F["brand"], fill=MUTED2)

    d.text((MX, 360), "LVMH BEAUTY  ·  未来 1—3 年香氛美学与体验创新方案", font=F["eyebrow"], fill=GOLD)
    wrap(d, f"MFK品牌全案：{PROMISE}", (MX, 450), F["hero"], CREAM2, 1900, 84)
    d.rectangle([MX, 660, MX + 140, 666], fill=GOLD)
    wrap(d, "以调香师专业与嗅觉衣橱，帮助消费者确认属于自己的标志性香气。", (MX, 710), F["sub"], SOFT2, 1800, 44)

    rows = [
        ("战略定位", POS),
        ("品牌母题", MOTIF),
        ("产品系统", SYSTEM),
        ("体验机制", JOURNEY),
    ]
    y = 880
    for lab, val in rows:
        d.text((MX, y), lab, font=F["label"], fill=MUTED2)
        d.text((MX + 240, y - 2), val, font=F["row_b"] if lab == "战略定位" else F["row"], fill=CREAM2)
        y += 70

    d.text((MX, 1220), "品牌问题", font=F["label"], fill=MUTED2)
    wrap(d, PROBLEM, (MX + 240, 1216), F["body"], SOFT2, 1600, 34)

    d.text((MX, 1380), "下一步", font=F["label"], fill=GOLD)
    d.text((MX + 240, 1376), "内部证据链已通过 → 真人概念验证（非市场独占宣称）", font=F["body"], fill=CREAM2)

    d.text((MX, 1780), "EVIDENCE-LED  ·  HUMAN-VERIFIED  ·  PRIORITIZE VALIDATION", font=F["foot"], fill=MUTED2)
    save(img, "mfk_00_ending.png")


# ═══════════════════════════════════════════════════════════
# Market page footnotes (audit strip) — regenerate p01 core with states
# ═══════════════════════════════════════════════════════════
def slide_p01_core_audited():
    """Rebuild core problem page with evidence-state labels on market case."""
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    header(
        d,
        "01 / CORE PROBLEM + MARKET CASE",
        "核心问题，与一次方向构建的市场依据",
        f"品牌问题锁定：{PROBLEM}",
    )

    # problem
    rr(d, [MX, 280, W - MX, 420], SOFT_R, 10)
    d.text((MX + 24, 300), "品牌问题（锁定）", font=F["label"], fill=RED)
    wrap(d, PROBLEM + f" → 要建立「{POS}」。", (MX + 24, 345), F["h3"], INK, W - 2 * MX - 50, 40)

    # KPI cards with evidence state
    cards = [
        ("P&C 有机 0%", "集团零增长压力", "事实", "LVMH FY2025/H1'26"),
        ("Gen Z 8–12 支", "衣柜行为结构信号", "外部研究", "Scento 2026*待核页码"),
        ("层叠 +63.9%", "场景轮换热度信号", "外部研究", "Spate 2026*待核关键词"),
        ("MFK 5.5%", "选择效率对照", "外部研究", "份额口径*待核平台"),
        ("转化 25% vs 4%", "路径决定转化", "外部研究", "WWD/Phiur*待核样本"),
    ]
    cw = (W - 2 * MX - 4 * GAP) // 5
    for i, (n, t, st, src) in enumerate(cards):
        x = MX + i * (cw + GAP)
        rr(d, [x, 460, x + cw, 820], WHITE, 8)
        d.text((x + 16, 490), n, font=F["h3"], fill=RED if i == 0 else TEAL)
        wrap(d, t, (x + 16, 580), F["body"], INK, cw - 32, 32)
        d.text((x + 16, 700), st, font=F["label"], fill=GOLD)
        wrap(d, src, (x + 16, 750), F["tiny"], MUTED, cw - 32, 22)

    # causal table
    d.text((MX, 870), "从数据到「必须构建」（策略推断）", font=F["h2"], fill=INK)
    rows = [
        ("证据", "状态", "结构含义", "对 MFK"),
        ("零增长", "事实", "不能靠品类自然放量", "必须做选择效率×转化"),
        ("衣柜/层叠上升", "外部研究", "单香口号接不住结构", f"系统用「{SYSTEM}」"),
        ("份额拥挤", "外部研究", "头部差被选效率", f"定位「{POS}」"),
        ("转化路径差", "外部研究", "路径决定结果", f"机制「{JOURNEY}」"),
    ]
    widths = [520, 420, 1100, 1280]
    y = 940
    for i, row in enumerate(rows):
        yy = y + i * 100
        bg = SOFT if i == 0 else (WHITE if i % 2 else SOFT_T)
        rr(d, [MX, yy, W - MX, yy + 92], bg, 4)
        x = MX + 16
        for j, (cell, w) in enumerate(zip(row, widths)):
            d.text((x, yy + 30), cell, font=F["small"] if i == 0 else F["body"], fill=MUTED if i == 0 else INK)
            x += w

    rr(d, [MX, 1480, W - MX, 1920], SOFT_G, 10)
    d.text((MX + 24, 1520), "目标消费者（锁定）", font=F["h3"], fill=TEAL)
    wrap(d, AUDIENCE, (MX + 24, 1600), F["h3"], INK, W - 2 * MX - 50, 42)
    d.text((MX + 24, 1760), f"母题「{MOTIF}」=判断标准；系统「{SYSTEM}」=编排；体验「{JOURNEY}」=路径。", font=F["body"], fill=MUTED)
    d.text((MX + 24, 1830), "*标「待核」项提交前必须补：地区｜时间｜样本量｜指标定义｜来源页码/链接", font=F["small"], fill=ORANGE)

    footer(d, "证据状态：事实/外部研究/策略推断已标注 · 待核项不得写成已证实市场结论")
    save(img, "mfk_01_core_problem.png")


def stamp_audit_footer(name, state_line, detail_line):
    """Overlay audit strip on existing chart slides that lack generators."""
    path = OUT / name
    if not path.exists():
        print("skip missing", name)
        return
    img = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(img)
    # Cover old footer band
    d.rectangle([0, 1960, W, H], fill=CREAM)
    d.line([(MX, 1975), (W - MX, 1975)], fill=LINE, width=2)
    d.text((MX, 1990), state_line, font=F["tiny"], fill=TEAL)
    wrap(d, detail_line, (MX, 2025), F["tiny"], MUTED, W - 2 * MX - 400, 22)
    d.text((W - MX - 360, 2080), "MFK Brand Strategy  |  CONFIDENTIAL", font=F["tiny"], fill=MUTED)
    save(img, name)


def stamp_part02_audit_pages():
    stamp_audit_footer(
        "mfk_02_market_signal.png",
        "证据状态：外部研究（待核）· 审计字段：地区｜时间｜样本量｜指标定义｜来源页码/链接",
        "本页数字不得单独写成市场结论；须服务目标消费者「多品牌比较→试香确认」的一次购买决策。待核项提交前补齐来源。",
    )
    stamp_audit_footer(
        "mfk_02_consumer_friction.png",
        "证据状态：语料信号 + 外部研究（待核）· 审计字段：地区｜时间｜样本量｜指标定义｜来源页码/链接",
        "摩擦点用于诊断选择效率缺口，不直接等于品牌定位。对齐锁定问题：欣赏却难确定适合自己的那一支。",
    )
    stamp_audit_footer(
        "mfk_02_competitor_map.png",
        "证据状态：策略推断（竞品对照）· 审计字段：对照品牌｜对照维度｜证据来源｜证据状态",
        "竞品对照=Byredo / Le Labo（非 LV）。用于说明选择权威战场拥挤，不证明 MFK 已占位。",
    )
    stamp_audit_footer(
        "mfk_02_competitor_deep.png",
        "证据状态：策略推断（竞品深潜）· 审计字段：对照品牌｜对照维度｜证据来源｜证据状态",
        "深潜结论服务于「私人香气表达的精准权威」定位缺口，禁止写成竞品无法替代的市场事实。",
    )
    stamp_audit_footer(
        "mfk_02_mfk_diagnosis.png",
        "证据状态：策略推断（品牌诊断）· 下一动作=PART03 系统筛选",
        "诊断收束到产品系统「时刻衣柜」；战略定位保持「私人香气表达的精准权威」，二者不可互换。",
    )


if __name__ == "__main__":
    slide_cover()
    slide_strategic_answer()
    slide_audience()
    slide_p01_core_audited()
    slide_p02_proposition()
    slide_p03_contract()
    slide_p03_close()
    slide_p05_prop()
    slide_wardrobe_logic()
    slide_case_close()
    slide_ending()
    stamp_part02_audit_pages()
    print("CLARITY FIX PACK DONE")
