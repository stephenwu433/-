#!/usr/bin/env python3
"""Aesthetic prophecy slide — competition-fit narrative after TOC."""
from pathlib import Path
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

POS = "私人香气表达的精准权威"
MOTIF = "精准的感性"
SYSTEM = "时刻衣柜"
JOURNEY = "从试香到签名"

_S = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
_N = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
_I = "/usr/share/fonts/truetype/inter/Inter-Regular.ttf"

F = {
    "brand": ImageFont.truetype(_I, 22),
    "label": ImageFont.truetype(_B, 18, index=2),
    "title": ImageFont.truetype(_S, 54, index=2),
    "hero": ImageFont.truetype(_S, 56, index=2),
    "h2": ImageFont.truetype(_S, 34, index=2),
    "h3": ImageFont.truetype(_B, 26, index=2),
    "body": ImageFont.truetype(_N, 24, index=2),
    "small": ImageFont.truetype(_N, 20, index=2),
    "tiny": ImageFont.truetype(_N, 16, index=2),
    "sub": ImageFont.truetype(_N, 26, index=2),
}


def rr(d, box, fill, r=12):
    d.rounded_rectangle(box, radius=r, fill=fill)


def wrap(d, text, xy, font, fill, max_w, lh):
    x, y = xy
    text = str(text).replace("\n", " ")
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


def save(img, name):
    img.save(OUT / name, "PNG", optimize=True)
    img.resize((1920, 1080), Image.Resampling.LANCZOS).save(
        OUT / name.replace(".png", "_1920.png"), "PNG", optimize=True
    )
    img.save(ART / name, "PNG", optimize=True)
    print("saved", name)


def slide_aesthetic_prophecy():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)

    d.text((MX, 40), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED)
    d.text((W - MX - 200, 40), "LVMH BEAUTY", font=F["brand"], fill=MUTED)
    d.text((MX, 88), "00 / AESTHETIC PROPHECY", font=F["label"], fill=RED)
    d.text((MX, 118), "美学预言：未来的奢华，来自被准确理解", font=F["title"], fill=INK)
    d.rectangle([MX, 198, MX + 100, 204], fill=GOLD)
    d.text(
        (MX, 220),
        "赛题口径：洞见未来 1—3 年趋势 → 定义下一种奢华美学 → 革新运营模式",
        font=F["sub"],
        fill=MUTED,
    )

    # Prophecy statement
    rr(d, [MX, 290, W - MX, 560], SOFT_R, 12)
    d.text((MX + 36, 320), "未来 1—3 年预判", font=F["label"], fill=RED)
    wrap(
        d,
        "高端香水的价值重心将进一步延伸至对个人状态的准确表达。消费者需要的不只是被认可的香气，还包括一套能够理解场景、解释选择并陪伴其形成签名香气的体验系统。",
        (MX + 36, 380),
        F["h3"],
        INK,
        W - 2 * MX - 80,
        42,
    )
    d.text((MX + 36, 500), f"我们预判的下一种奢华香氛美学：{MOTIF}", font=F["h2"], fill=RED)

    # Chain
    d.text((MX, 600), "整套关系（固定读序）", font=F["h2"], fill=INK)
    chain = [
        ("未来趋势", "奢华体验走向私人化、情境化、可解释", TEAL),
        ("美学预言", MOTIF, RED),
        ("战略定位", POS, RED),
        ("运营创新", SYSTEM, TEAL),
        ("体验机制", JOURNEY, TEAL),
        ("商业验证", "90天试点", GOLD),
    ]
    cw = (W - 2 * MX - 5 * GAP) // 6
    for i, (lab, val, col) in enumerate(chain):
        x = MX + i * (cw + GAP)
        rr(d, [x, 680, x + cw, 1080], WHITE, 10)
        d.rectangle([x, 680, x + cw, 692], fill=col)
        d.text((x + 16, 720), lab, font=F["label"], fill=MUTED)
        wrap(d, val, (x + 16, 800), F["h3"], INK, cw - 32, 36)
        if i < 5:
            # arrow between cards
            ax = x + cw + 4
            d.polygon([(ax, 860), (ax + GAP - 8, 880), (ax, 900)], fill=GOLD)

    # Evidence proof strip — market / consumer / competitor prove the future shift
    d.text((MX, 1140), "证据如何共同证明这项未来变化（后页展开）", font=F["h2"], fill=INK)
    proofs = [
        ("市场", "衣柜化 / 层叠 / 场景轮换上升", "私人化·情境化在发生"),
        ("消费者", "欣赏却难确定「哪支适合我」", "需要可解释的选择系统"),
        ("竞品", "选择权威战场拥挤、可替换主张多", "美学标准比口号更稀缺"),
    ]
    pw = (W - 2 * MX - 2 * GAP) // 3
    for i, (a, b, c) in enumerate(proofs):
        x = MX + i * (pw + GAP)
        rr(d, [x, 1220, x + pw, 1520], SOFT_T if i != 1 else SOFT_G, 10)
        d.text((x + 28, 1260), a, font=F["label"], fill=TEAL)
        wrap(d, b, (x + 28, 1320), F["body"], INK, pw - 56, 34)
        wrap(d, c, (x + 28, 1420), F["h3"], INK, pw - 56, 36)

    # Closing MFK sentence
    rr(d, [MX, 1580, W - MX, 1920], SOFT_G, 12)
    d.text((MX + 36, 1630), "MFK 的参赛回答（革新运营模式）", font=F["label"], fill=GOLD)
    wrap(
        d,
        f"以「{MOTIF}」为下一种奢华美学，以「{SYSTEM}」组织私人场景，以「{JOURNEY}」完成确定选择——成为「{POS}」。",
        (MX + 36, 1700),
        F["h3"],
        INK,
        W - 2 * MX - 80,
        44,
    )
    d.text(
        (MX + 36, 1840),
        "第2页锁定语言层级；本页给出赛题预言。二者分工，不互相替代。",
        font=F["body"],
        fill=MUTED,
    )

    d.line([(MX, FY - 16), (W - MX, FY - 16)], fill=LINE, width=2)
    d.text((MX, FY), "证据状态：策略推断（由 PART02 市场/消费者/竞品共同支撑）· 美学名=母题，不改战略定位", font=F["tiny"], fill=MUTED)
    d.text((W - MX - 360, FY), "MFK Brand Strategy  |  CONFIDENTIAL", font=F["tiny"], fill=MUTED)
    save(img, "mfk_00_aesthetic_prophecy.png")


if __name__ == "__main__":
    slide_aesthetic_prophecy()
