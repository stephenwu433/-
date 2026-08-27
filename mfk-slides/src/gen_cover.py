#!/usr/bin/env python3
"""Cover slide — clearer hierarchy on provided glass background."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

OUT = Path("/workspace/mfk-slides")
ART = Path("/opt/cursor/artifacts")
BG = Path("/home/ubuntu/.cursor/projects/workspace/assets/38a58645-eda5-4f5b-9a7e-0e2a7c23d3d2.png")
W, H = 3840, 2160

INK = (28, 28, 28)
MUTED = (70, 70, 70)
RED = (155, 36, 51)
GOLD = (184, 148, 90)


def fonts():
    s = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
    n = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    b = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
    i = "/usr/share/fonts/truetype/inter/Inter-Regular.ttf"
    ib = "/usr/share/fonts/truetype/inter/Inter-Bold.ttf"
    return {
        "brand": ImageFont.truetype(i, 28),
        "eyebrow": ImageFont.truetype(ib, 30),
        "hero": ImageFont.truetype(s, 92, index=2),
        "support": ImageFont.truetype(n, 36, index=2),
        "dir_label": ImageFont.truetype(ib, 26),
        "dir": ImageFont.truetype(s, 40, index=2),
        "motif": ImageFont.truetype(n, 28, index=2),
        "foot": ImageFont.truetype(i, 24),
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
    bg = Image.open(BG).convert("RGB")
    # upscale to HD
    bg = bg.resize((W, H), Image.Resampling.LANCZOS)
    # slight left wash so text stays crisp without killing the glass
    overlay = Image.new("RGBA", (W, H), (245, 242, 235, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(0, 1680):
        alpha = int(70 * (1 - i / 1680))
        od.line([(i, 0), (i, H)], fill=(245, 242, 235, alpha))
    img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)

    MX = 180

    # top brands
    d.text((MX, 90), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED)
    d.text((W - MX - 280, 90), "LVMH BEAUTY", font=F["brand"], fill=MUTED)

    # eyebrow
    d.text(
        (MX, 480),
        "LVMH BEAUTY  ·  未来 1–3 年香氛美学与体验创新",
        font=F["eyebrow"],
        fill=RED,
    )

    # hero — ONE line of brand promise as the cover signal
    hero = "让香气，准确表达复杂的你。"
    d.text((MX, 580), hero, font=F["hero"], fill=INK)
    # underline below full glyph height (~font size)
    d.rectangle([MX, 580 + 110, MX + 140, 580 + 118], fill=GOLD)

    # one supporting sentence — higher contrast
    wrap(
        d,
        "以调香师专业与嗅觉衣橱，帮助消费者确认属于自己的标志性香气。",
        (MX, 740),
        F["support"],
        INK,
        1680,
        52,
    )

    # ONE direction line (merged, not two competing lines)
    d.text((MX, 980), "战略方向", font=F["dir_label"], fill=RED)
    d.text((MX + 200, 972), "私人香气表达的精准权威", font=F["dir"], fill=INK)
    d.text((MX, 1060), "品牌母题  ·  精准的感性", font=F["motif"], fill=MUTED)

    # footer
    d.text(
        (MX, 1980),
        "MFK × LVMH BEAUTY  /  BRAND GROWTH SYSTEM",
        font=F["foot"],
        fill=MUTED,
    )
    d.text((W - MX - 80, 1980), "01", font=F["foot"], fill=MUTED)

    out = OUT / "mfk_00_cover.png"
    img.save(out, "PNG")
    img.resize((1920, 1080), Image.Resampling.LANCZOS).save(
        OUT / "mfk_00_cover_1920.png", "PNG"
    )
    img.save(ART / "mfk_00_cover.png", "PNG")
    print("saved", out)


if __name__ == "__main__":
    build()
