#!/usr/bin/env python3
"""Part 03 chapter divider: renamed + Feishu corpus QR."""
from pathlib import Path
import qrcode
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/workspace/mfk-slides")
ART = Path("/opt/cursor/artifacts")
W, H = 3840, 2160
MX = 140
CREAM = (245, 242, 235)
INK = (28, 28, 28)
MUTED = (90, 90, 90)
RED = (155, 36, 51)
GOLD = (184, 148, 90)
BG = Path("/home/ubuntu/.cursor/projects/workspace/assets/38a58645-eda5-4f5b-9a7e-0e2a7c23d3d2.png")
FEISHU = "https://ocna8mptgpzi.feishu.cn/base/MdwsbiODRaxwyNsBHIKc4oSvn5Z?table=tblfvh2eVD1qV1I8&view=vewiPkNFt5"

_S = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
_N = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
_IB = "/usr/share/fonts/truetype/inter/Inter-Bold.ttf"
_I = "/usr/share/fonts/truetype/inter/Inter-Regular.ttf"

F = {
    "brand": ImageFont.truetype(_I, 22),
    "part": ImageFont.truetype(_IB, 36),
    "title": ImageFont.truetype(_S, 72, index=2),
    "sub": ImageFont.truetype(_N, 28, index=2),
    "qr_cap": ImageFont.truetype(_N, 16, index=2),
}


def make_qr(url, box=260):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB").resize(
        (box, box), Image.Resampling.NEAREST
    )


def slide_p03_chapter():
    bg = Image.open(BG).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(0, 2100):
        a = int(110 * (1 - i / 2100))
        od.line([(i, 0), (i, H)], fill=(245, 242, 235, a))
    img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)

    d.text((MX, 88), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED)
    d.text((W - MX - 240, 88), "LVMH BEAUTY", font=F["brand"], fill=MUTED)
    d.text((MX, 720), "PART 03", font=F["part"], fill=RED)

    title = "系统筛选与方向收敛"
    d.text((MX, 800), title, font=F["title"], fill=INK)
    tw = d.textlength(title, font=F["title"])
    d.rectangle([MX, 900, MX + int(tw), 906], fill=GOLD)

    d.text((MX, 960), "从411条语料中筛选两个待真人验证的品牌方向", font=F["sub"], fill=INK)

    qr = make_qr(FEISHU, 260)
    qx, qy = MX, 1280
    pad = 16
    d.rounded_rectangle([qx - pad, qy - pad, qx + 260 + pad, qy + 260 + pad + 70], radius=8, fill=(255, 255, 255))
    img.paste(qr, (qx, qy))
    d = ImageDraw.Draw(img)
    d.text((qx, qy + 270), "扫码查看完整语料数据表", font=F["qr_cap"], fill=MUTED)
    d.text((qx, qy + 300), "来源：Instagram · TikTok · 小红书", font=F["qr_cap"], fill=MUTED)

    name = "mfk_03_00_chapter.png"
    img.save(OUT / name, "PNG", optimize=True)
    img.resize((1920, 1080), Image.Resampling.LANCZOS).save(OUT / name.replace(".png", "_1920.png"), "PNG", optimize=True)
    img.save(ART / name, "PNG", optimize=True)
    print("saved", name)


if __name__ == "__main__":
    slide_p03_chapter()
