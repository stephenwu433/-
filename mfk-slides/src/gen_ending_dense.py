#!/usr/bin/env python3
"""Ending slide — denser hierarchy on dark bg, no page number."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/workspace/mfk-slides")
ART = Path("/opt/cursor/artifacts")
BG = Path("/home/ubuntu/.cursor/projects/workspace/assets/ea789c2c-218c-4b09-ab49-46393f3059c0.png")
# fallback to previous dark bg if needed
if not BG.exists():
    BG = Path("/home/ubuntu/.cursor/projects/workspace/assets/49a9cc62-4bc4-4ae4-a911-53783998238c.png")

W, H = 3840, 2160
CREAM = (245, 242, 235)
SOFT = (200, 188, 178)
MUTED = (160, 148, 140)
GOLD = (196, 168, 120)
RED_SOFT = (200, 120, 120)


def fonts():
    s = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
    n = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    b = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
    i = "/usr/share/fonts/truetype/inter/Inter-Regular.ttf"
    ib = "/usr/share/fonts/truetype/inter/Inter-Bold.ttf"
    return {
        "brand": ImageFont.truetype(i, 26),
        "eyebrow": ImageFont.truetype(ib, 30),
        "hero": ImageFont.truetype(s, 72, index=2),
        "support": ImageFont.truetype(n, 32, index=2),
        "row": ImageFont.truetype(n, 30, index=2),
        "row_b": ImageFont.truetype(b, 32, index=2),
        "motif": ImageFont.truetype(n, 26, index=2),
        "body": ImageFont.truetype(n, 24, index=2),
        "label": ImageFont.truetype(ib, 18),
        "foot": ImageFont.truetype(ib, 20),
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


def build():
    bg = Image.open(BG).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    img = bg.copy()
    d = ImageDraw.Draw(img)
    MX = 180

    d.text((MX, 88), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED)
    d.text((W - MX - 260, 88), "LVMH BEAUTY", font=F["brand"], fill=MUTED)

    # denser stack — mirror cover hierarchy on dark
    d.text(
        (MX, 380),
        "LVMH BEAUTY  ·  未来 1—3 年香氛美学与体验创新方案",
        font=F["eyebrow"],
        fill=GOLD,
    )

    wrap(
        d,
        "MFK品牌全案：让香气，准确表达复杂的你。",
        (MX, 470),
        F["hero"],
        CREAM,
        1900,
        88,
    )

    d.rectangle([MX, 680, MX + 140, 686], fill=GOLD)

    wrap(
        d,
        "以调香师专业与嗅觉衣橱，帮助消费者确认属于自己的标志性香气。",
        (MX, 730),
        F["support"],
        SOFT,
        1800,
        46,
    )

    d.text((MX, 880), "品牌方向  |  个人标志性香气的精准选择权威", font=F["row"], fill=CREAM)
    tw = d.textlength("品牌方向  |  个人标志性香气的精准选择权威", font=F["row"])
    d.rectangle([MX, 928, MX + int(tw), 932], fill=GOLD)

    d.text((MX, 980), "战略方向  |  私人香气表达的精准权威", font=F["row_b"], fill=GOLD)

    d.text((MX, 1080), "品牌母题：精准的感性", font=F["motif"], fill=SOFT)
    d.text((MX, 1140), "体验机制：从试香到签名", font=F["motif"], fill=SOFT)

    d.text((MX, 1260), "系统收束", font=F["label"], fill=GOLD)
    d.text(
        (MX, 1310),
        "场景层主切  ·  时刻衣柜命题  ·  BRD-02 主推 / BRD-01 确认  ·  90天最小闭环验证",
        font=F["body"],
        fill=SOFT,
    )
    d.text(
        (MX, 1380),
        "时刻衣柜 × 精准的感性 × 试香到签名  =  难替代的选择权威",
        font=F["body"],
        fill=CREAM,
    )

    # footer — no page number
    d.text(
        (MX, 1780),
        "EVIDENCE-LED  ·  HUMAN-VERIFIED  ·  PRIORITIZE VALIDATION",
        font=F["foot"],
        fill=MUTED,
    )

    out = OUT / "mfk_00_ending.png"
    img.save(out, "PNG")
    img.resize((1920, 1080), Image.Resampling.LANCZOS).save(
        OUT / "mfk_00_ending_1920.png", "PNG"
    )
    img.save(ART / "mfk_00_ending.png", "PNG")
    img.save(ART / "mfk_00_ending_dense.png", "PNG")
    print("saved", out)


if __name__ == "__main__":
    build()
