#!/usr/bin/env python3
"""Denser cover (like original) + post-Part06 summary on dark bg."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/workspace/mfk-slides")
ART = Path("/opt/cursor/artifacts")
BG_COVER = Path("/home/ubuntu/.cursor/projects/workspace/assets/38a58645-eda5-4f5b-9a7e-0e2a7c23d3d2.png")
BG_DARK = Path("/home/ubuntu/.cursor/projects/workspace/assets/ea789c2c-218c-4b09-ab49-46393f3059c0.png")
W, H = 3840, 2160

INK = (28, 28, 28)
MUTED = (90, 90, 90)
RED = (155, 36, 51)
GOLD = (184, 148, 90)
CREAM = (245, 242, 235)
SOFT = (210, 200, 190)
LINE_L = (180, 168, 160)


def fonts():
    s = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
    n = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    b = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
    i = "/usr/share/fonts/truetype/inter/Inter-Regular.ttf"
    ib = "/usr/share/fonts/truetype/inter/Inter-Bold.ttf"
    return {
        "brand": ImageFont.truetype(i, 26),
        "eyebrow": ImageFont.truetype(b, 32, index=2),
        "hero": ImageFont.truetype(s, 72, index=2),
        "support": ImageFont.truetype(n, 34, index=2),
        "row": ImageFont.truetype(n, 32, index=2),
        "row_b": ImageFont.truetype(b, 34, index=2),
        "motif": ImageFont.truetype(n, 28, index=2),
        "foot": ImageFont.truetype(i, 22),
        "h2": ImageFont.truetype(s, 40, index=2),
        "h3": ImageFont.truetype(b, 28, index=2),
        "body": ImageFont.truetype(n, 26, index=2),
        "small": ImageFont.truetype(n, 22, index=2),
        "label": ImageFont.truetype(b, 20, index=2),
        "promise": ImageFont.truetype(s, 56, index=2),
    }


F = fonts()


def wrap(d, text, xy, font, fill, max_w, lh):
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


def cover():
    """Denser cover matching third-image information density."""
    bg = Image.open(BG_COVER).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    # light left wash for readability
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(0, 1750):
        a = int(85 * (1 - i / 1750))
        od.line([(i, 0), (i, H)], fill=(245, 242, 235, a))
    img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)
    MX = 180

    d.text((MX, 88), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED)
    d.text((W - MX - 260, 88), "LVMH BEAUTY", font=F["brand"], fill=MUTED)

    # denser stack — like third image
    y = 420
    d.text(
        (MX, y),
        "LVMH BEAUTY  ·  未来 1—3 年香氛美学与体验创新方案",
        font=F["eyebrow"],
        fill=RED,
    )

    y = 520
    wrap(
        d,
        "MFK品牌全案：让香气，准确表达复杂的你。",
        (MX, y),
        F["hero"],
        INK,
        1750,
        90,
    )

    y = 740
    wrap(
        d,
        "以调香师专业与嗅觉衣橱，帮助消费者确认属于自己的标志性香气。",
        (MX, y),
        F["support"],
        INK,
        1680,
        48,
    )

    # brand direction with underline
    y = 900
    d.text((MX, y), "品牌方向  |  个人标志性香气的精准选择权威", font=F["row"], fill=INK)
    tw = d.textlength("品牌方向  |  个人标志性香气的精准选择权威", font=F["row"])
    d.rectangle([MX, y + 48, MX + int(tw), y + 52], fill=GOLD)

    y = 1000
    d.text((MX, y), "战略方向  |  私人香气表达的精准权威", font=F["row_b"], fill=RED)

    y = 1100
    d.text((MX, y), "品牌母题：精准的感性", font=F["motif"], fill=MUTED)

    # small system reminder — fills empty without cluttering hero
    y = 1240
    d.text((MX, y), "系统要点", font=F["label"], fill=GOLD)
    d.text(
        (MX, y + 50),
        "场景层主切  ·  精准的感性  ·  从试香到签名  ·  90天最小闭环验证",
        font=F["body"],
        fill=MUTED,
    )

    d.text((MX, 1980), "MFK × LVMH BEAUTY  /  BRAND GROWTH SYSTEM", font=F["foot"], fill=MUTED)
    d.text((W - MX - 80, 1980), "01", font=F["foot"], fill=MUTED)

    save(img, "mfk_00_cover.png")


def summary():
    """Post-Part06 full-case summary on dark background."""
    bg = Image.open(BG_DARK).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    img = bg.copy()
    d = ImageDraw.Draw(img)
    MX = 160

    d.text((MX, 80), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=LINE_L)
    d.text((W - MX - 240, 80), "LVMH BEAUTY", font=F["brand"], fill=LINE_L)

    d.text((MX, 200), "00 / CASE CLOSE", font=F["label"], fill=GOLD)
    d.text((MX, 250), "全案收束：从战场到验证的一条线", font=F["promise"], fill=CREAM)
    d.rectangle([MX, 340, MX + 120, 346], fill=GOLD)

    # six beats
    beats = [
        ("01 战场", "场景层主切", "资产配套 · 避开词语红海"),
        ("02 命题", "时刻衣柜", "欣赏 → 确定选择 → 拥有理由"),
        ("03 验证", "系统过闸", "BRD-02 主推 · BRD-01 确认"),
        ("04 进入", "场景剧本", "体验作配套入口 · 美学=精准克制"),
        ("05 编排", "产品×零售×内容×关系", "同一套选择逻辑四线落地"),
        ("06 试点", "90天最小闭环", "Go / Iterate / Kill 预设阈值"),
    ]
    gap = 28
    bw = (W - 2 * MX - 5 * gap) // 6
    for i, (a, b, c) in enumerate(beats):
        x = MX + i * (bw + gap)
        # translucent card
        card = Image.new("RGBA", (bw, 420), (40, 18, 20, 160))
        img.paste(card, (x, 420), card)
        d = ImageDraw.Draw(img)
        d.text((x + 20, 450), a, font=F["label"], fill=GOLD)
        wrap(d, b, (x + 20, 520), F["h3"], CREAM, bw - 40, 36)
        wrap(d, c, (x + 20, 640), F["small"], SOFT, bw - 40, 30)

    # formula + promise
    d = ImageDraw.Draw(img)
    d.text(
        (MX, 920),
        "时刻衣柜 × 精准的感性 × 试香到签名  =  难替代的选择权威",
        font=F["h2"],
        fill=CREAM,
    )
    d.text(
        (MX, 1020),
        "让香气，准确表达复杂的你。",
        font=F["promise"],
        fill=CREAM,
    )
    d.text(
        (MX, 1140),
        "不是更多形容词，而是帮你在此刻选对，并说清为什么是你。方向先验转化，过闸再扩面。",
        font=F["body"],
        fill=SOFT,
    )

    # footer — no page number
    d.text((MX, 1780), "EVIDENCE-LED  ·  HUMAN-VERIFIED  ·  PRIORITIZE VALIDATION", font=F["foot"], fill=LINE_L)

    save(img, "mfk_00_case_close.png")


if __name__ == "__main__":
    cover()
    summary()
