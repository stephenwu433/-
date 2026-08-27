#!/usr/bin/env python3
"""00 Strategic Answer — one-page direction aligned with Parts 01–06."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/workspace/mfk-slides")
ART = Path("/opt/cursor/artifacts")
W, H = 3840, 2160
MX = 160
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


def fonts():
    s = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
    n = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    b = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
    i = "/usr/share/fonts/truetype/inter/Inter-Regular.ttf"
    ib = "/usr/share/fonts/truetype/inter/Inter-Bold.ttf"
    return {
        "title": ImageFont.truetype(s, 64, index=2),
        "h2": ImageFont.truetype(s, 36, index=2),
        "h3": ImageFont.truetype(b, 28, index=2),
        "body": ImageFont.truetype(n, 24, index=2),
        "small": ImageFont.truetype(n, 20, index=2),
        "tiny": ImageFont.truetype(n, 17, index=2),
        "sub": ImageFont.truetype(n, 28, index=2),
        "label": ImageFont.truetype(ib, 18),
        "num": ImageFont.truetype(ib, 36),
        "brand": ImageFont.truetype(i, 18),
        "promise": ImageFont.truetype(s, 42, index=2),
    }


F = fonts()


def rr(d, box, fill, r=14):
    d.rounded_rectangle(box, radius=r, fill=fill)


def wrap(d, text, xy, font, fill, max_w, lh=34):
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


def build():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)

    d.text((MX, 48), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED)
    d.text((W - MX - 220, 48), "LVMH BEAUTY", font=F["brand"], fill=MUTED)
    d.text((MX, 100), "00 / STRATEGIC ANSWER", font=F["label"], fill=RED)
    d.text((MX, 140), "一页看懂品牌方向", font=F["title"], fill=INK)
    d.rectangle([MX, 230, MX + 110, 236], fill=GOLD)
    d.text(
        (MX, 258),
        "场景切入 · 精准认知 · 感性母题 · 签名体验——四件事串成一条线。",
        font=F["sub"],
        fill=MUTED,
    )

    # One-line system equation
    rr(d, [MX, 330, W - MX, 470], SOFT_R, 12)
    d.text((MX + 36, 355), "方向公式", font=F["label"], fill=RED)
    d.text(
        (MX + 36, 400),
        "时刻衣柜（场景）  ×  精准的感性（标准）  ×  试香到签名（路径）  =  难替代的选择权威",
        font=F["h2"],
        fill=INK,
    )

    # Four pillars — corrected hierarchy
    pillars = [
        (
            "01",
            "切入层",
            "场景层主切",
            "此刻该用哪一支的选择剧本",
            "配套：资产重组衣橱角色\n淘汰：词语层红海主攻",
            TEAL,
            SOFT_T,
        ),
        (
            "02",
            "长期认知",
            "私人香气的精准权威",
            "不是更浓的奢华，是更准的判断",
            "对齐 PART01–03：\n选择效率 × 难替换",
            RED,
            SOFT_R,
        ),
        (
            "03",
            "品牌母题",
            "精准的感性",
            "多一分则腻，少一分则寡",
            "统领产品 / 内容 / 美学\n禁用空话形容词",
            RED,
            SOFT_R,
        ),
        (
            "04",
            "体验机制",
            "从试香到签名",
            "欣赏 → 确定选择 → 可复述理由",
            "咨询可记录 · 档案可复利\n样品→正装可归因",
            GOLD,
            SOFT_G,
        ),
    ]

    gap = 36
    pw = (W - 2 * MX - 3 * gap) // 4
    y0 = 520
    for i, (num, layer, title, line, note, accent, bg) in enumerate(pillars):
        x = MX + i * (pw + gap)
        rr(d, [x, y0, x + pw, y0 + 780], bg, 14)
        d.rectangle([x, y0, x + pw, y0 + 12], fill=accent)
        d.text((x + 28, y0 + 40), num, font=F["num"], fill=accent)
        d.text((x + 28, y0 + 110), layer, font=F["label"], fill=MUTED)
        d.text((x + 28, y0 + 160), title, font=F["h3"], fill=INK)
        wrap(d, line, (x + 28, y0 + 250), F["body"], INK, pw - 56, 36)
        d.line([(x + 28, y0 + 420), (x + pw - 28, y0 + 420)], fill=LINE, width=2)
        for j, nl in enumerate(note.split("\n")):
            d.text((x + 28, y0 + 460 + j * 40), nl, font=F["small"], fill=MUTED)

        # arrows between cards
        if i < 3:
            ax = x + pw + 6
            ay = y0 + 390
            d.polygon([(ax, ay - 10), (ax + gap - 12, ay), (ax, ay + 10)], fill=LINE)

    # Read order strip
    rr(d, [MX, 1340, W - MX, 1480], SOFT, 10)
    d.text((MX + 36, 1375), "怎么读这一页", font=F["label"], fill=MUTED)
    d.text(
        (MX + 36, 1415),
        "从左到右：先定在哪一层打仗 → 要占什么长期认知 → 用什么母题统领表达 → 用什么体验把选择做完。下面一句是对消费者的承诺。",
        font=F["body"],
        fill=INK,
    )

    # Consumer promise
    rr(d, [MX, 1520, W - MX, 1780], WHITE, 12)
    d.rectangle([MX, 1520, MX + 14, 1780], fill=RED)
    d.text((MX + 48, 1560), "消费者承诺", font=F["label"], fill=RED)
    d.text(
        (MX + 48, 1620),
        "让香气，准确表达复杂的你。",
        font=F["promise"],
        fill=INK,
    )
    d.text(
        (MX + 48, 1710),
        "落地含义：不是给你更多形容词，而是帮你在此刻选对，并说清为什么是你。",
        font=F["body"],
        fill=MUTED,
    )

    # Foot notes
    d.line([(MX, FY - 18), (W - MX, FY - 18)], fill=LINE, width=2)
    d.text(
        (MX, FY),
        "对齐 PART01–06：场景主切 · BRD-02 母题 · BRD-01 体验 · 90天先验转化 ｜ 优先验证方向，尚未宣称市场独占",
        font=F["tiny"],
        fill=MUTED,
    )
    d.text((W - MX - 320, FY), "MFK Brand Strategy  |  00", font=F["tiny"], fill=MUTED)

    save(img, "mfk_00_strategic_answer.png")


if __name__ == "__main__":
    build()
