#!/usr/bin/env python3
"""Ending slide — dark background, no page number, aligned with cover."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/workspace/mfk-slides")
ART = Path("/opt/cursor/artifacts")
BG = Path("/home/ubuntu/.cursor/projects/workspace/assets/49a9cc62-4bc4-4ae4-a911-53783998238c.png")
W, H = 3840, 2160

CREAM = (245, 242, 235)
MUTED = (180, 168, 160)
GOLD = (196, 168, 120)
SOFT = (210, 200, 190)


def fonts():
    s = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
    n = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    i = "/usr/share/fonts/truetype/inter/Inter-Regular.ttf"
    ib = "/usr/share/fonts/truetype/inter/Inter-Bold.ttf"
    return {
        "brand": ImageFont.truetype(i, 26),
        "hero": ImageFont.truetype(s, 86, index=2),
        "dir": ImageFont.truetype(s, 40, index=2),
        "body": ImageFont.truetype(n, 30, index=2),
        "foot": ImageFont.truetype(ib, 22),
    }


F = fonts()


def build():
    bg = Image.open(BG).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    img = bg.copy()
    d = ImageDraw.Draw(img)
    MX = 180

    # top brands — cream on dark
    d.text((MX, 90), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED)
    d.text((W - MX - 260, 90), "LVMH BEAUTY", font=F["brand"], fill=MUTED)

    # hero promise
    d.text((MX, 780), "让香气，准确表达复杂的你。", font=F["hero"], fill=CREAM)

    # short gold accent under hero (left of the bg line)
    d.rectangle([MX, 920, MX + 160, 926], fill=GOLD)

    # one direction + motif/experience on one clean block
    d.text((MX, 980), "MFK  |  私人香气表达的精准权威", font=F["dir"], fill=CREAM)
    d.text(
        (MX, 1080),
        "品牌母题：精准的感性    ·    体验机制：从试香到签名",
        font=F["body"],
        fill=SOFT,
    )

    # footer meta only — NO page number
    # bg already has a line ~ y 1644; place footer below it
    d.text((MX, 1780), "EVIDENCE-LED  ·  HUMAN-VERIFIED", font=F["foot"], fill=MUTED)

    out = OUT / "mfk_00_ending.png"
    img.save(out, "PNG")
    img.resize((1920, 1080), Image.Resampling.LANCZOS).save(
        OUT / "mfk_00_ending_1920.png", "PNG"
    )
    img.save(ART / "mfk_00_ending.png", "PNG")
    print("saved", out)


if __name__ == "__main__":
    build()
