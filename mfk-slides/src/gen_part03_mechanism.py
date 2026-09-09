#!/usr/bin/env python3
"""PART 03 — mechanism-first rebuild: how BRD-02 is derived."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/workspace/mfk-slides")
ART = Path("/opt/cursor/artifacts")
W, H = 3840, 2160
MX = 160
GAP = 36
CW = (W - 2 * MX - 2 * GAP) // 3
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


def fonts():
    s = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
    n = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    b = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
    i = "/usr/share/fonts/truetype/inter/Inter-Regular.ttf"
    ib = "/usr/share/fonts/truetype/inter/Inter-Bold.ttf"
    return {
        "title": ImageFont.truetype(s, 68, index=2),
        "h2": ImageFont.truetype(s, 40, index=2),
        "h3": ImageFont.truetype(b, 30, index=2),
        "body": ImageFont.truetype(n, 26, index=2),
        "small": ImageFont.truetype(n, 22, index=2),
        "tiny": ImageFont.truetype(n, 18, index=2),
        "sub": ImageFont.truetype(n, 30, index=2),
        "label": ImageFont.truetype(b, 20, index=2),
        "num": ImageFont.truetype(ib, 52),
        "num_sm": ImageFont.truetype(ib, 36),
        "brand": ImageFont.truetype(i, 20),
    }


F = fonts()


def new():
    img = Image.new("RGB", (W, H), CREAM)
    return img, ImageDraw.Draw(img)


def header(d, code, title, question):
    d.text((MX, 48), "MAISON FRANCIS KURKDJIAN  PARIS", font=F["brand"], fill=MUTED)
    d.text((W - MX - 220, 48), "LVMH BEAUTY", font=F["brand"], fill=MUTED)
    d.text((MX, 100), code, font=F["label"], fill=RED)
    d.text((MX, 140), title, font=F["title"], fill=INK)
    d.rectangle([MX, 230, MX + 110, 236], fill=GOLD)
    d.text((MX, 258), question, font=F["sub"], fill=MUTED)


def footer(d, src):
    d.line([(MX, FY - 18), (W - MX, FY - 18)], fill=LINE, width=2)
    d.text((MX, FY), src, font=F["tiny"], fill=MUTED)
    d.text((W - MX - 420, FY), "MFK Brand Strategy  |  PART 03  |  CONFIDENTIAL", font=F["tiny"], fill=MUTED)


def rr(d, box, fill, r=14):
    d.rounded_rectangle(box, radius=r, fill=fill)


def text_wrap(d, text, xy, font, fill, max_w, lh=34):
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
    p = OUT / name
    img.save(p, "PNG")
    img.resize((1920, 1080), Image.Resampling.LANCZOS).save(
        OUT / name.replace(".png", "_1920.png"), "PNG"
    )
    img.save(ART / name, "PNG")
    print("saved", name)


# ═══════════════════════════════════════════════════════════
# SLIDE 1 — Mechanism map (decision rules, not pipeline décor)
# ═══════════════════════════════════════════════════════════
def slide_01():
    img, d = new()
    header(
        d,
        "03 / SYSTEM SCREENING  ·  1 of 5",
        "系统筛选与方向收敛：规则先于结果",
        "本章不是市场总验证。研究问题：内部语料证据链是否支持方向进入真人概念验证？",
    )

    # Core claim strip
    rr(d, [MX, 330, W - MX, 430], SOFT_R, 12)
    d.text((MX + 32, 355), "核心机制一句话", font=F["label"], fill=RED)
    d.text(
        (MX + 32, 385),
        "语料必须先被编码成冲突 → 冲突才能升格为候选 → 候选必须过「空话闸 + 可替换性闸 + 五维压力」→ 存活方向再按「稀缺×难复制」选主推。",
        font=F["body"],
        fill=INK,
    )

    # Four gates with IF/THEN
    gates = [
        (
            "闸门 A",
            "冲突优先",
            TEAL,
            SOFT_T,
            "IF 语料只表达偏好\nTHEN 停在需求簇，不进主战场\n\nIF 语料形成对立张力\nTHEN 编码为冲突簇 INS-C*\n→ 才有资格生成 DIR",
            "为何：偏好可被任何品牌\n接；张力才定义战场",
        ),
        (
            "闸门 B",
            "空话禁用",
            GOLD,
            SOFT_G,
            "IF 主张命中 BW 禁用词\n（小众/高级感/氛围感…）\nTHEN 结果=需改写，不得升格\n\nIF 无空话但证据不足\nTHEN 结果=需补证，可保留",
            "为何：词语层是红海；\n禁用强迫落到机制表述",
        ),
        (
            "闸门 C",
            "可替换性",
            RED,
            SOFT_R,
            "关键问题：换成 Byredo/\nLe Labo 是否仍成立？\n\nIF 是 → 方向弱，难升主推\nIF 否 → 专属成立，可争主推\n（DIR-02 = 否；DIR-04 = 是）",
            "为何：长期资产必须是\n竞品抄不走的判断标准",
        ),
        (
            "闸门 D",
            "主推排序",
            INK,
            SOFT,
            "过闸后不是比「证据条数」\n\n主推公式：\n稀缺 × 难复制  >  可运营\n\nBRD-02 赢在哲学 moat\nBRD-01 留作体验路径",
            "为何：条数最多≠资产最强\nC02=15条却不是主推",
        ),
    ]
    gw = (W - 2 * MX - 3 * GAP) // 4
    for i, (tag, name, accent, bg, body, why) in enumerate(gates):
        x = MX + i * (gw + GAP)
        y = 470
        rr(d, [x, y, x + gw, y + 980], bg, 14)
        d.rectangle([x, y, x + gw, y + 10], fill=accent)
        d.text((x + 28, y + 36), tag, font=F["label"], fill=accent)
        d.text((x + 28, y + 78), name, font=F["h2"], fill=INK)
        yy = y + 150
        for line in body.split("\n"):
            d.text((x + 28, yy), line, font=F["small"], fill=INK)
            yy += 36
        d.line([(x + 28, y + 720), (x + gw - 28, y + 720)], fill=LINE, width=2)
        d.text((x + 28, y + 750), "设计意图", font=F["label"], fill=accent)
        for j, line in enumerate(why.split("\n")):
            d.text((x + 28, y + 800 + j * 36), line, font=F["small"], fill=MUTED)

    # Bottom outcome preview
    rr(d, [MX, 1510, W - MX, 1720], WHITE, 14)
    d.text((MX + 36, 1540), "本轮过闸结果（预告，后页展开）", font=F["h3"], fill=INK)
    outcomes = [
        ("DIR-01", "需改写", ORANGE, "命中「高级感」→ 未升格"),
        ("DIR-02", "需补证", GOLD, "无空话 + 不可替换 → 升 BRD-02 主推"),
        ("DIR-03", "通过", GREEN, "体验路径成立 → 升 BRD-01 确认"),
        ("DIR-04", "需补证", ORANGE, "可被竞品替换 → 未升格"),
    ]
    ow = (W - 2 * MX - 36 * 3 - 72) // 4
    for i, (code, res, col, note) in enumerate(outcomes):
        x = MX + 36 + i * (ow + 36)
        d.text((x, 1605), code, font=F["h3"], fill=INK)
        d.text((x + 140, 1608), res, font=F["h3"], fill=col)
        d.text((x, 1660), note, font=F["small"], fill=MUTED)

    # Closing
    rr(d, [MX, 1770, W - MX, 1920], SOFT_T, 12)
    d.text((MX + 36, 1805), "读图约定", font=F["label"], fill=TEAL)
    d.text(
        (MX + 36, 1845),
        "后面四页按 A→B→C→D 展开：冲突如何被命名 → 如何变成候选 → 矩阵如何杀方向 → 为何主推不是证据最多的那条。",
        font=F["body"],
        fill=INK,
    )

    footer(d, "Source: 飞书「MFK香水品牌洞察系统」P-001 / TAG / BW / INS / DIR / CHK / BRD 全表截图还原")
    save(img, "mfk_03_01_mechanism.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 2 — CF conflict tags → INS clusters
# ═══════════════════════════════════════════════════════════
def slide_02():
    img, d = new()
    header(
        d,
        "03 / SYSTEM SCREENING  ·  2 of 5",
        "闸门 A：冲突如何被编码成洞察簇",
        "机制：标签词典里的 CF（核心冲突）不是装饰分类——它规定「什么张力才有资格进战场」。计数对象≠转化漏斗。",
    )

    # Left: CF tags
    rr(d, [MX, 340, MX + 1180, 1480], WHITE, 14)
    d.rectangle([MX, 340, MX + 12, 1480], fill=TEAL)
    d.text((MX + 40, 370), "标签层 · 核心冲突 CF-01~04", font=F["h2"], fill=INK)
    d.text((MX + 40, 430), "纳入标准：语料同时出现对立两端；排除：单边偏好表述", font=F["small"], fill=MUTED)

    cfs = [
        ("CF-01", "想有存在感", "但不想浓烈", "→ 喂给 INS-C01"),
        ("CF-02", "想独特", "又怕难闻/选错", "→ 喂给 INS-C02"),
        ("CF-03", "想奢华", "又不想炫耀", "→ 喂给 INS-C03"),
        ("CF-04", "想表达自己", "又不想被模板化", "→ 横切身份层"),
    ]
    for i, (cid, a, b, arrow) in enumerate(cfs):
        y = 500 + i * 220
        rr(d, [MX + 40, y, MX + 1140, y + 190], SOFT_T, 12)
        d.text((MX + 70, y + 28), cid, font=F["label"], fill=TEAL)
        d.text((MX + 70, y + 70), a, font=F["h3"], fill=INK)
        d.text((MX + 70, y + 120), "×  " + b, font=F["h3"], fill=RED)
        d.text((MX + 720, y + 90), arrow, font=F["body"], fill=MUTED)

    # Right: INS outputs with evidence counts
    rr(d, [MX + 1220, 340, W - MX, 1480], WHITE, 14)
    d.rectangle([MX + 1220, 340, MX + 1232, 1480], fill=RED)
    d.text((MX + 1260, 370), "洞察层 · 系统产出的 5 簇", font=F["h2"], fill=INK)
    d.text((MX + 1260, 430), "冲突簇优先升格；需求簇可保留但不自动进 DIR", font=F["small"], fill=MUTED)

    clusters = [
        ("INS-C02", "独特 × 安全", 15, "冲突", True, "证据最厚"),
        ("INS-N04", "季节清透", 14, "需求", False, "未升 DIR"),
        ("INS-C01", "存在感 × 得体", 8, "冲突", True, "→ DIR-01"),
        ("INS-N01", "干净肌肤感", 6, "需求", True, "→ DIR-04"),
        ("INS-C03", "贵气 × 低调", 5, "冲突", True, "→ DIR-02"),
    ]
    max_n = 15
    bar_max = 900
    for i, (code, name, n, typ, to_dir, note) in enumerate(clusters):
        y = 500 + i * 170
        d.text((MX + 1260, y), code, font=F["h3"], fill=INK)
        d.text((MX + 1520, y + 4), name, font=F["body"], fill=MUTED)
        col = RED if typ == "冲突" else TEAL
        d.text((MX + 2100, y + 4), typ, font=F["label"], fill=col)
        bw = int(bar_max * n / max_n)
        rr(d, [MX + 1260, y + 55, MX + 1260 + bw, y + 95], col, 6)
        d.text((MX + 1260 + bw + 16, y + 58), f"{n} 条  ·  {note}", font=F["small"], fill=MUTED)

    # Mechanism callout
    rr(d, [MX, 1530, W - MX, 1920], SOFT_G, 14)
    d.text((MX + 40, 1570), "机制要点（本页必须读懂的三句话）", font=F["h3"], fill=GOLD)
    lines = [
        "1. 冲突簇 ≠ 证据最多者自动赢：C03 只有 5 条，但仍进入候选，因为它对应 CF-03「奢华×不炫耀」——这是 MFK 作者性最能咬合的张力。",
        "2. 需求簇可以很厚（N04=14）却不升 DIR：季节清透可被产品档期消化，构不成品牌哲学战场。",
        "3. 平台分布（IG/TT/XHS）只证明「可回溯」，不证明「该主推」——主推判定在闸门 C/D，不在条数。",
    ]
    for i, line in enumerate(lines):
        text_wrap(d, line, (MX + 40, 1640 + i * 80), F["body"], INK, W - 2 * MX - 80, 34)

    footer(d, "Source: TAG词典 CF-01~04；INS表 INS-C01/C02/C03/N01/N04 平台分布字段（IG/TT/XHS 合计）")
    save(img, "mfk_03_02_conflict_encoding.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 3 — INS → DIR conversion table
# ═══════════════════════════════════════════════════════════
def slide_03():
    img, d = new()
    header(
        d,
        "03 / SYSTEM SCREENING  ·  3 of 5",
        "转化机制：一条洞察怎样变成一条候选方向",
        "规则：每个 DIR 必须绑定唯一主冲突/需求；写清「美学命题 + MFK可兑现资产 + 反例风险」，否则不许进压力测试。语料信号≠市场验证。",
    )

    # Table header
    cols = [280, 520, 720, 900, 700]  # widths
    headers = ["洞察簇", "转化规则", "候选方向", "美学命题（机制表述）", "升格判定"]
    x0 = MX
    y0 = 340
    rr(d, [MX, y0, W - MX, y0 + 70], SOFT, 8)
    x = x0 + 20
    for h, w in zip(headers, cols):
        d.text((x, y0 + 20), h, font=F["h3"], fill=MUTED)
        x += w

    rows = [
        (
            "INS-C01\n存在感×得体\n证据 8",
            "冲突可产品化\n→ 生成 DIR",
            "DIR-01\n日常可穿的\n高端香",
            "克制的高级感：\n不喧哗的存在",
            "进测试\n但 CHK 命中\n「高级感」→ 杀",
            SOFT_R,
        ),
        (
            "INS-C03\n贵气×低调\n证据 5",
            "冲突咬合作者\n资产 → 生成 DIR",
            "DIR-02\n嗅觉精准主义",
            "多一分则腻\n少一分则寡\n（精准克制）",
            "进测试\n无空话+不可替换\n→ 升主推",
            SOFT_T,
        ),
        (
            "INS-C02\n独特×安全\n证据 15",
            "冲突落在选择\n旅程 → 生成 DIR",
            "DIR-03\n从试到拥有",
            "陪伴式发现：\nMFK 陪你找签名",
            "进测试\nCHK 通过\n→ 升确认",
            SOFT_G,
        ),
        (
            "INS-N01\n干净肌肤感\n证据 6",
            "需求可延伸\n品类 → 生成 DIR",
            "DIR-04\n身体与空间",
            "香氛是生活\n的底色",
            "进测试\n可被竞品替换\n→ 不升格",
            SOFT_R,
        ),
        (
            "INS-N04\n季节清透\n证据 14",
            "需求可被档期\n消化 → 不生成",
            "—\n无 DIR",
            "—",
            "停在洞察层\n不作品牌方向",
            SOFT,
        ),
    ]

    y = y0 + 80
    rh = 220
    for ins, rule, direc, prop, verdict, bg in rows:
        rr(d, [MX, y, W - MX, y + rh - 12], bg, 10)
        cells = [ins, rule, direc, prop, verdict]
        x = x0 + 20
        for cell, w in zip(cells, cols):
            for j, line in enumerate(cell.split("\n")):
                d.text((x, y + 28 + j * 40), line, font=F["body"], fill=INK)
            x += w
        y += rh

    # Formula bar
    rr(d, [MX, 1880, W - MX, 1985], SOFT_T, 10)
    d.text(
        (MX + 32, 1915),
        "转化公式：INS（命名张力） + MFK可兑现资产（作者/咨询/衣橱） − 反例风险  =  DIR；缺任何一项 → 不进漏斗。",
        font=F["body"],
        fill=INK,
    )

    footer(d, "Source: DIR-01~04 表字段「支撑洞察 / 美学命题 / MFK可兑现资产」；INS-N04 无对应 DIR 行")
    save(img, "mfk_03_03_ins_to_dir.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 4 — Five-dim × CHK kill matrix
# ═══════════════════════════════════════════════════════════
def slide_04():
    img, d = new()
    header(
        d,
        "03 / SYSTEM SCREENING  ·  4 of 5",
        "闸门 B+C：筛选矩阵——谁被杀死，谁被留下",
        "两道硬闸并行：CHK（空话 / 可替换 / 证据）× 五维压力测试。PoC「暂缓」=规模化未证，≠方向不成立；亦≠命题已市场验证。",
    )

    # Matrix — cells are pre-wrapped tuples of lines
    dims = ["空话命中", "竞品可替换", "证据充分", "品牌专属", "产品兑现", "CHK结果", "升格"]
    data = [
        (
            "DIR-01",
            [
                [("是", ORANGE)],
                [("部分", INK)],
                [("弱", ORANGE)],
                [("中", INK)],
                [("有724", INK), ("可接", INK)],
                [("需改写", ORANGE)],
                [("× 未升格", RED)],
            ],
            RED,
        ),
        (
            "DIR-02",
            [
                [("否", GREEN)],
                [("否", GREEN)],
                [("待补", GOLD)],
                [("强", TEAL)],
                [("强", TEAL)],
                [("需补证", GOLD)],
                [("→ BRD-02", TEAL)],
            ],
            TEAL,
        ),
        (
            "DIR-03",
            [
                [("否", GREEN)],
                [("否", GREEN)],
                [("是", GREEN)],
                [("中", INK)],
                [("履约", INK), ("成本高", INK)],
                [("通过", GREEN)],
                [("→ BRD-01", GOLD)],
            ],
            GOLD,
        ),
        (
            "DIR-04",
            [
                [("弱/是", ORANGE)],
                [("是", ORANGE)],
                [("待补", GOLD)],
                [("弱", ORANGE)],
                [("客单", INK), ("偏低", INK)],
                [("需补证", GOLD)],
                [("× 未升格", RED)],
            ],
            RED,
        ),
    ]

    label_w = 280
    col_w = (W - 2 * MX - label_w) // len(dims)
    y = 340
    rr(d, [MX, y, W - MX, y + 72], SOFT, 8)
    d.text((MX + 24, y + 22), "候选", font=F["h3"], fill=MUTED)
    for i, dim in enumerate(dims):
        d.text((MX + label_w + i * col_w + 8, y + 22), dim, font=F["body"], fill=MUTED)

    y = 420
    for name, cells, accent in data:
        rr(d, [MX, y, W - MX, y + 200], WHITE, 10)
        d.rectangle([MX, y, MX + 10, y + 200], fill=accent)
        d.text((MX + 28, y + 80), name, font=F["h2"], fill=INK)
        for i, cell_lines in enumerate(cells):
            cx = MX + label_w + i * col_w + 8
            for j, (line, fill) in enumerate(cell_lines):
                d.text((cx, y + 60 + j * 40), line, font=F["h3"], fill=fill)
        y += 220

    # Kill rules explanation
    rr(d, [MX, 1340, W - MX, 1920], SOFT, 14)
    d.text((MX + 36, 1380), "杀伤规则（可读决策树）", font=F["h2"], fill=INK)
    rules = [
        ("杀 DIR-01", "CHK 空话命中「高级感」= 是  →  强制改写；未完成改写前不得升 BRD。词语层红海，与 PART 01「避开词语层主战场」一致。"),
        ("留 DIR-02", "空话=否，且「换成竞品仍成立」=否  →  专属成立。剩余缺口是抽象需补证，不是一票否决。故可升格，标记「主推待补证」。"),
        ("留 DIR-03", "CHK=通过；冲突在选择旅程上可运营。专属中等，故升「确认」作体验路径，不作品牌哲学主推。"),
        ("杀 DIR-04", "「换成 Byredo/Le Labo 仍成立」=是  →  身体护理延伸无品牌壁垒。需求真，但不构成 MFK 长期资产。"),
        ("PoC 暂缓", "四方向规模化均未证。机制允许：方向过闸成立 ≠ 立刻大投放；PART 06 用 90 天试点补「规模化」一维。"),
    ]
    for i, (t, body) in enumerate(rules):
        yy = 1460 + i * 80
        d.text((MX + 36, yy), t, font=F["h3"], fill=RED if t.startswith("杀") else TEAL)
        text_wrap(d, body, (MX + 280, yy + 4), F["body"], INK, W - MX - 320, 32)

    footer(d, "Source: 压力测试五维表 + CHK-001~004（空话命中 / 换成竞品仍成立 / 测试结果）")
    save(img, "mfk_03_04_gate_matrix.png")


# ═══════════════════════════════════════════════════════════
# SLIDE 5 — Why BRD-02 wins (decision formula)
# ═══════════════════════════════════════════════════════════
def slide_05():
    img, d = new()
    header(
        d,
        "03 / SYSTEM SCREENING  ·  5 of 5",
        "闸门 D：主推「精准的感性」——看稀缺×难复制，不看条数",
        "内部证据链裁定：主方向进入真人概念验证，备选保留。证据条数只决定是否进漏斗，不决定主推。",
    )

    # Chain strip
    rr(d, [MX, 330, W - MX, 470], SOFT_T, 12)
    chain = "CF-03 奢华×不炫耀  →  INS-C03 贵气×低调（5条）  →  DIR-02 嗅觉精准主义  →  CHK-002 需补证但不可替换  →  BRD-02 精准的感性【主推】"
    d.text((MX + 36, 360), "主推完整因果链（请按箭头读）", font=F["label"], fill=TEAL)
    text_wrap(d, chain, (MX + 36, 400), F["body"], INK, W - 2 * MX - 72, 36)

    # Three columns: counterintuitive / formula / dual structure
    # Col1
    x = MX
    rr(d, [x, 510, x + CW, 1480], WHITE, 14)
    d.rectangle([x, 510, x + CW, 520], fill=ORANGE)
    d.text((x + 32, 550), "反常识点", font=F["h2"], fill=INK)
    d.text((x + 32, 620), "证据最多 ≠ 主推", font=F["h3"], fill=ORANGE)
    bullets = [
        "INS-C02 有 15 条证据",
        "却只升为 BRD-01「确认」",
        "",
        "INS-C03 只有 5 条",
        "反而升为 BRD-02「主推」",
        "",
        "原因：C02 解决的是",
        "选择恐惧（旅程问题）",
        "C03 解决的是",
        "品牌判断标准（哲学问题）",
        "",
        "旅程可运营，但可被",
        "咨询台流程模仿；",
        "哲学若绑定调香师署名，",
        "竞品难以平移。",
    ]
    for i, b in enumerate(bullets):
        d.text((x + 32, 700 + i * 42), b, font=F["body"], fill=INK if b else MUTED)

    # Col2
    x = MX + CW + GAP
    rr(d, [x, 510, x + CW, 1480], WHITE, 14)
    d.rectangle([x, 510, x + CW, 520], fill=RED)
    d.text((x + 32, 550), "主推评分（1–5）", font=F["h2"], fill=INK)
    d.text((x + 32, 620), "稀缺×难复制 决定主推", font=F["h3"], fill=RED)

    scores = [
        ("稀缺（竞品未占位）", 5, 4),
        ("难复制（大师/机制）", 5, 4),
        ("可运营（可记录复用）", 3, 5),
        ("复利（档案/转化）", 4, 5),
    ]
    d.text((x + 32, 700), "维度", font=F["small"], fill=MUTED)
    d.text((x + 420, 700), "02", font=F["small"], fill=RED)
    d.text((x + 520, 700), "01", font=F["small"], fill=TEAL)
    for i, (name, a, b) in enumerate(scores):
        yy = 760 + i * 120
        d.text((x + 32, yy), name, font=F["body"], fill=INK)
        # bars
        rr(d, [x + 32, yy + 45, x + 32 + a * 70, yy + 75], RED, 4)
        rr(d, [x + 32, yy + 82, x + 32 + b * 70, yy + 105], TEAL, 4)
        d.text((x + 400, yy + 45), str(a), font=F["h3"], fill=RED)
        d.text((x + 400, yy + 78), str(b), font=F["h3"], fill=TEAL)

    d.text((x + 32, 1280), "红=BRD-02  青=BRD-01", font=F["small"], fill=MUTED)
    d.text((x + 32, 1330), "主推取前两维最高；", font=F["body"], fill=INK)
    d.text((x + 32, 1375), "后两维交给确认方向补齐。", font=F["body"], fill=INK)

    # Col3
    x = MX + 2 * (CW + GAP)
    rr(d, [x, 510, x + CW, 1480], WHITE, 14)
    d.rectangle([x, 510, x + CW, 520], fill=TEAL)
    d.text((x + 32, 550), "双方向编排", font=F["h2"], fill=INK)
    d.text((x + 32, 620), "哲学 + 旅程，不是二选一", font=F["h3"], fill=TEAL)

    rr(d, [x + 32, 700, x + CW - 32, 980], SOFT_R, 12)
    d.text((x + 56, 730), "BRD-02 主推 · 哲学层", font=F["h3"], fill=RED)
    for j, line in enumerate(
        [
            "主张：精准的感性",
            "逻辑：要的不是更浓，",
            "      是更准的克制",
            "资产：Francis 署名判断",
            "咬合：PART01 场景层+",
            "      PART02 选择权威缺口",
        ]
    ):
        d.text((x + 56, 790 + j * 28), line, font=F["small"], fill=INK)

    rr(d, [x + 32, 1020, x + CW - 32, 1300], SOFT_T, 12)
    d.text((x + 56, 1050), "BRD-01 确认 · 旅程层", font=F["h3"], fill=TEAL)
    for j, line in enumerate(
        [
            "主张：从试香到签名",
            "逻辑：样本→正装的选择",
            "      恐惧由咨询闭环",
            "资产：可运营试香路径",
            "角色：把哲学落到柜台/",
            "      内容/会员触点",
        ]
    ):
        d.text((x + 56, 1110 + j * 28), line, font=F["small"], fill=INK)

    d.text((x + 32, 1360), "下一章：找最能建立", font=F["body"], fill=MUTED)
    d.text((x + 32, 1405), "「选择权威」的进入点。", font=F["body"], fill=MUTED)

    # Bottom conclusion
    rr(d, [MX, 1530, W - MX, 1920], SOFT_G, 14)
    d.text((MX + 40, 1570), "第三章收束：系统筛选通过 → 进入真人概念验证", font=F["h2"], fill=INK)
    closing = [
        "① 配置只研香水，竞品对照 Le Labo / Byredo（P-001）",
        "② 语料用 26 标签编码；CF 冲突标签决定谁能进战场（闸门 A）——标签数≠证据转化率",
        "③ 5 个洞察簇中，4 个生成 DIR；N04 因「可被档期消化」不生成（转化规则，非空话闸）",
        "④ CHK+五维：空话杀 DIR-01；可替换杀 DIR-04；留下 02/03（闸门 B+C）",
        "⑤ 主推看稀缺×难复制 → BRD-02「精准的感性」母题；BRD-01「从试香到签名」体验确认（闸门 D）",
        "⑥ 裁定力度：内部证据链通过，进入真人验证；禁止写「命题成立 / 市场已验证」",
    ]
    for i, line in enumerate(closing):
        d.text((MX + 40, 1650 + i * 40), line, font=F["body"], fill=INK)

    footer(d, "证据状态：语料信号+策略推断 · 章节=系统筛选与方向收敛 · 下一步=真人概念验证（非市场独占宣称）")
    save(img, "mfk_03_05_why_brd02.png")


if __name__ == "__main__":
    slide_01()
    slide_02()
    slide_03()
    slide_04()
    slide_05()
    print("ALL PART 03 MECHANISM SLIDES DONE")
