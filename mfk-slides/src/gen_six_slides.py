#!/usr/bin/env python3
"""
Deliver 6 slides:
  Part 01 × 1 — 核心问题 + 为何需要方向构建（一页收束）
  Part 03 × 5 — 验证第二章命题的推理链 + 系统机制
"""
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
        "title": ImageFont.truetype(s, 64, index=2),
        "title_sm": ImageFont.truetype(s, 52, index=2),
        "h2": ImageFont.truetype(s, 38, index=2),
        "h3": ImageFont.truetype(b, 28, index=2),
        "body": ImageFont.truetype(n, 26, index=2),
        "small": ImageFont.truetype(n, 22, index=2),
        "tiny": ImageFont.truetype(n, 18, index=2),
        "sub": ImageFont.truetype(n, 28, index=2),
        "label": ImageFont.truetype(b, 20, index=2),
        "num": ImageFont.truetype(ib, 48),
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
    d.text((MX, 138), title, font=F["title"], fill=INK)
    d.rectangle([MX, 225, MX + 110, 231], fill=GOLD)
    d.text((MX, 250), question, font=F["sub"], fill=MUTED)


def footer(d, src):
    d.line([(MX, FY - 18), (W - MX, FY - 18)], fill=LINE, width=2)
    d.text((MX, FY), src, font=F["tiny"], fill=MUTED)
    d.text(
        (W - MX - 420, FY),
        "MFK Brand Strategy  |  CONFIDENTIAL",
        font=F["tiny"],
        fill=MUTED,
    )


def rr(d, box, fill, r=14):
    d.rounded_rectangle(box, radius=r, fill=fill)


def wrap(d, text, xy, font, fill, max_w, lh=36):
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


# ═══════════════════════════════════════════════════════════
# PART 01 — 1 page: 核心问题 + 为何需要方向构建
# ═══════════════════════════════════════════════════════════
def p01():
    img, d = new()
    header(
        d,
        "01 / CORE PROBLEM",
        "核心问题，与一次方向构建的必要性",
        "先钉住要回答的问题，再解释为什么现在必须构建——而不是先做传播再找证据。",
    )

    # Left: Core problem
    rr(d, [MX, 340, MX + CW * 2 + GAP, 1180], WHITE, 16)
    d.rectangle([MX, 340, MX + 14, 1180], fill=RED)
    d.text((MX + 48, 380), "核心问题", font=F["h2"], fill=RED)
    problem = (
        "在高端香水选择更加丰富、情绪叙事和生活方式表达日趋同质化的环境下，"
        "MFK 如何把消费者对品牌调香水准和高级感的欣赏，转化为对"
        "「哪一支适合我、为什么适合我」的确定选择，并形成竞品难以替代的品牌拥有理由？"
    )
    wrap(d, problem, (MX + 48, 480), F["h3"], INK, CW * 2 + GAP - 120, 48)

    d.line([(MX + 48, 820), (MX + CW * 2 + GAP - 48, 820)], fill=LINE, width=2)
    d.text((MX + 48, 860), "问题拆成两段缺口", font=F["label"], fill=GOLD)
    gaps = [
        ("欣赏 → 确定选择", "调香与高级感已被看见，但选购仍停在「感觉不错」。"),
        ("确定选择 → 拥有理由", "即使买下，也缺一句竞品难以平移的「为什么是 MFK」。"),
    ]
    for i, (t, b) in enumerate(gaps):
        x = MX + 48 + i * (CW + 20)
        rr(d, [x, 920, x + CW - 20, 1120], SOFT_R if i == 0 else SOFT_G, 12)
        d.text((x + 28, 950), t, font=F["h3"], fill=RED if i == 0 else TEAL)
        wrap(d, b, (x + 28, 1020), F["body"], INK, CW - 80, 34)

    # Right: Why now
    x = MX + 2 * (CW + GAP)
    rr(d, [x, 340, W - MX, 1180], WHITE, 16)
    d.rectangle([x, 340, x + 14, 1180], fill=TEAL)
    d.text((x + 40, 380), "为何需要一次方向构建", font=F["h2"], fill=TEAL)
    d.text((x + 40, 450), "（不是换口号，是建决策系统）", font=F["small"], fill=MUTED)

    whys = [
        ("01 市场", "选择过载 + 情绪叙事同质化，词语层已红海。"),
        ("02 集团", "零增长周期要求：选择效率 × 样品到正装转化。"),
        ("03 品牌", "已有作者性 / 衣橱哲学 / 嗅觉咨询，缺统一选择逻辑。"),
        ("04 方法", "本案不是先设情绪概念再找语料证明；要从冲突与资产倒推入场层。"),
    ]
    for i, (t, b) in enumerate(whys):
        yy = 520 + i * 150
        d.text((x + 40, yy), t, font=F["label"], fill=TEAL)
        wrap(d, b, (x + 40, yy + 40), F["body"], INK, CW - 100, 34)

    # Bottom: what this chapter will decide + handoff
    rr(d, [MX, 1240, W - MX, 1920], SOFT, 16)
    d.text((MX + 48, 1280), "本章要完成的判断", font=F["h2"], fill=INK)
    d.text(
        (MX + 48, 1360),
        "增长问题落在哪一层？ → 词语 / 场景 / 资产 三者里，主攻哪一层、配套哪一层、避开哪一层。",
        font=F["body"],
        fill=INK,
    )

    boxes = [
        (SOFT_T, TEAL, "本案定义", "建立品牌决策系统：\n从市场·冲突·竞品·资产\n判断入场层，而非做一场 campaign。"),
        (SOFT_G, GOLD, "范围", "Maison Francis Kurkdjian\n仅研究香水品类\n竞品对照：Le Labo / Byredo"),
        (SOFT_R, RED, "成功标准", "欣赏能转化为确定选择；\n拥有理由竞品难以替代；\n逻辑可理解·可记录·可运营。"),
    ]
    bw = (W - 2 * MX - 2 * GAP - 96) // 3
    for i, (bg, accent, t, b) in enumerate(boxes):
        bx = MX + 48 + i * (bw + GAP)
        rr(d, [bx, 1460, bx + bw, 1840], bg, 12)
        d.rectangle([bx, 1460, bx + bw, 1472], fill=accent)
        d.text((bx + 28, 1500), t, font=F["h3"], fill=accent)
        for j, line in enumerate(b.split("\n")):
            d.text((bx + 28, 1580 + j * 42), line, font=F["body"], fill=INK)

    footer(
        d,
        "Source: 项目核心问题原文 + 竞赛命题与品牌范围；对齐后续战场分层判断",
    )
    save(img, "mfk_01_core_problem.png")


# ═══════════════════════════════════════════════════════════
# PART 03 — 5 pages validating Part 02
# Part 02 conclusion to validate:
#   「可按时刻编排的大师香氛衣柜」
#   主攻场景层 / 配套资产重组 / 避开词语红海
#   缺口：统一的个人香气选择逻辑
# ═══════════════════════════════════════════════════════════


def p03_1():
    """验证契约：第二章命题 → 第三章要证明什么"""
    img, d = new()
    header(
        d,
        "03 / VALIDATE P02  ·  1 of 5",
        "第三章任务：用系统验证第二章命题，而不是另起炉灶",
        "第二章已收束命题；本章只回答一件事——这命题有没有资格成为长期资产。",
    )

    # Part 02 claim box
    rr(d, [MX, 340, W - MX, 620], SOFT_R, 14)
    d.text((MX + 40, 370), "第二章结论（待验证假设）", font=F["label"], fill=RED)
    d.text(
        (MX + 40, 420),
        "把 MFK 从「一支爆款的代名词」，收成「可按时刻编排的大师香氛衣柜」。",
        font=F["h2"],
        fill=INK,
    )
    triad = [
        ("主攻", "场景层", "此刻该用哪一支的选择剧本"),
        ("配套", "资产重组", "540 等产品重新分工进衣橱"),
        ("避开", "词语红海", "不把「小众/高级感」当主战场"),
    ]
    for i, (k, v, note) in enumerate(triad):
        x = MX + 40 + i * 1100
        d.text((x, 520), f"{k} · {v}", font=F["h3"], fill=RED)
        d.text((x, 570), note, font=F["body"], fill=MUTED)

    # Three validation questions
    d.text((MX, 680), "第三章必须逐条给出证据的验证问题", font=F["h2"], fill=INK)
    d.rectangle([MX, 740, MX + 100, 746], fill=GOLD)

    qs = [
        (
            "Q1",
            "场景层冲突是否真实存在？",
            "若语料只有偏好、没有对立张力，\n「时刻衣柜」就只是概念，不能当战场。",
            "→ 看冲突编码与洞察簇",
        ),
        (
            "Q2",
            "词语层是否真该避开？",
            "若空话主张能过闸，说明词语仍可主攻；\n若被禁用闸杀死，则印证第二章「避开」。",
            "→ 看空话闸与 DIR-01",
        ),
        (
            "Q3",
            "选择逻辑能否落到资产？",
            "命题要变成「可理解·可记录·可运营」的\n判断标准 + 试香路径，才算进入真人验证。",
            "→ 看 BRD-02 + BRD-01",
        ),
    ]
    qw = (W - 2 * MX - 2 * GAP) // 3
    for i, (qid, title, body, nexts) in enumerate(qs):
        x = MX + i * (qw + GAP)
        rr(d, [x, 780, x + qw, 1480], WHITE, 14)
        d.rectangle([x, 780, x + qw, 792], fill=TEAL if i < 2 else RED)
        d.text((x + 32, 820), qid, font=F["label"], fill=TEAL if i < 2 else RED)
        d.text((x + 32, 870), title, font=F["h3"], fill=INK)
        for j, line in enumerate(body.split("\n")):
            d.text((x + 32, 960 + j * 42), line, font=F["body"], fill=INK)
        d.line([(x + 32, 1220), (x + qw - 32, 1220)], fill=LINE, width=2)
        d.text((x + 32, 1260), nexts, font=F["body"], fill=MUTED)

    # Mechanism teaser
    rr(d, [MX, 1540, W - MX, 1920], SOFT_T, 14)
    d.text((MX + 40, 1580), "验证工具：飞书「MFK香水品牌洞察系统」", font=F["h3"], fill=TEAL)
    d.text(
        (MX + 40, 1650),
        "机制不是装饰流水线，而是四道闸：冲突优先 → 空话禁用 → 可替换性 → 主推排序（稀缺×难复制）。",
        font=F["body"],
        fill=INK,
    )
    d.text(
        (MX + 40, 1720),
        "下一页讲清系统怎么跑；随后三页按 Q1→Q2→Q3 把推理走完；第 5 页把结论映射回第二章「时刻衣柜」。",
        font=F["body"],
        fill=INK,
    )
    d.text(
        (MX + 40, 1800),
        "读法约定：每页结尾必须出现「对第二章命题的含义」，不允许只报系统字段。",
        font=F["body"],
        fill=RED,
    )

    footer(d, "Source: PART 02 命题页；验证问题由诊断缺口（统一选择逻辑）反推")
    save(img, "mfk_03_v1_contract.png")


def p03_2():
    """系统机制"""
    img, d = new()
    header(
        d,
        "03 / SYSTEM MECHANISM  ·  2 of 5",
        "系统机制：方向如何被「推」出来，而不是被「感觉」出来",
        "飞书多维表把语料变成可复核决策：每一步有输入、规则、输出；跳步无效。",
    )

    # Pipeline with rules
    steps = [
        ("①", "配置\nP-001", "只研香水\n对照 Le Labo\n/ Byredo", TEAL),
        ("②", "语料\nVL", "社媒证据池\nIG / TT / XHS", TEAL),
        ("③", "标签\n26码", "SCN/OLF/IDN\nCON/AES/CF", TEAL),
        ("④", "洞察\nINS", "冲突优先\n需求可保留", GOLD),
        ("⑤", "候选\nDIR", "绑定主冲突\n+可兑现资产", GOLD),
        ("⑥", "闸门\nCHK", "空话·可替换\n·五维压力", RED),
        ("⑦", "确认\nBRD", "主推 / 确认\n进入决策", RED),
    ]
    sw = (W - 2 * MX - 6 * 20) // 7
    for i, (n, name, rule, col) in enumerate(steps):
        x = MX + i * (sw + 20)
        rr(d, [x, 340, x + sw, 780], WHITE, 12)
        d.rectangle([x, 340, x + sw, 352], fill=col)
        d.text((x + 20, 380), n, font=F["num"], fill=col)
        for j, line in enumerate(name.split("\n")):
            d.text((x + 20, 470 + j * 40), line, font=F["h3"], fill=INK)
        d.line([(x + 20, 580), (x + sw - 20, 580)], fill=LINE, width=1)
        for j, line in enumerate(rule.split("\n")):
            d.text((x + 20, 610 + j * 36), line, font=F["small"], fill=MUTED)

    # Four gate rules
    d.text((MX, 840), "四道硬闸（系统真正做决策的地方）", font=F["h2"], fill=INK)
    d.rectangle([MX, 900, MX + 100, 906], fill=GOLD)

    gates = [
        ("闸 A 冲突优先", TEAL, "IF 只有偏好 → 停需求簇\nIF 形成对立张力 → INS-C*\n才允许生成 DIR", "对应验证 Q1"),
        ("闸 B 空话禁用", GOLD, "命中小众/高级感/氛围感…\n→ 需改写，不得升 BRD\n强迫落到机制表述", "对应验证 Q2"),
        ("闸 C 可替换性", RED, "换成 Byredo/Le Labo\n是否仍成立？\n是=弱；否=专属可争主推", "对应验证 Q3"),
        ("闸 D 主推排序", INK, "过闸后不比证据条数\n主推 = 稀缺 × 难复制\n最高者；条数只决定进漏斗", "决定主推/确认"),
    ]
    gw = (W - 2 * MX - 3 * GAP) // 4
    for i, (t, col, body, tag) in enumerate(gates):
        x = MX + i * (gw + GAP)
        rr(d, [x, 940, x + gw, 1580], WHITE, 12)
        d.rectangle([x, 940, x + 10, 1580], fill=col)
        d.text((x + 28, 970), t, font=F["h3"], fill=col)
        for j, line in enumerate(body.split("\n")):
            d.text((x + 28, 1060 + j * 42), line, font=F["body"], fill=INK)
        rr(d, [x + 28, 1420, x + gw - 28, 1510], SOFT, 8)
        d.text((x + 48, 1450), tag, font=F["small"], fill=MUTED)

    rr(d, [MX, 1640, W - MX, 1920], SOFT_G, 12)
    d.text((MX + 40, 1680), "对第二章命题的含义", font=F["label"], fill=GOLD)
    wrap(
        d,
        "若系统能把「时刻衣柜」拆成可过闸的冲突与资产，而把「高级感叙事」挡在空话闸外，"
        "则第二章「主攻场景 / 避开词语」就被机制证实，而不是被口头重申。下一页起按推理顺序走证据。",
        (MX + 40, 1740),
        F["body"],
        INK,
        W - 2 * MX - 80,
        40,
    )

    footer(d, "Source: 飞书 P-001 / TAG / BW / INS / DIR / CHK / BRD 字段结构")
    save(img, "mfk_03_v2_mechanism.png")


def p03_3():
    """Q1 inference: conflict → INS — validates scene-layer battlefield"""
    img, d = new()
    header(
        d,
        "03 / INFERENCE Q1  ·  3 of 5",
        "推理①：场景层冲突是否真实——从 CF 标签到洞察簇",
        "验证问题 Q1：若冲突不成立，「时刻衣柜」只是美化说法。",
    )

    # Reasoning steps horizontal
    steps = [
        ("输入", "语料进入标签层\nCF = 核心冲突词典", SOFT_T, TEAL),
        ("规则", "同时出现对立两端\n才编码为冲突；\n单边偏好进需求簇", SOFT_G, GOLD),
        ("产出", "3 冲突 + 2 需求\n系统优先捕捉张力", SOFT_R, RED),
        ("判定", "冲突可命名且\n跨平台可回溯\n→ Q1 通过门槛", WHITE, INK),
    ]
    sw = (W - 2 * MX - 3 * GAP) // 4
    for i, (t, b, bg, col) in enumerate(steps):
        x = MX + i * (sw + GAP)
        rr(d, [x, 340, x + sw, 620], bg, 12)
        d.text((x + 28, 370), t, font=F["label"], fill=col)
        for j, line in enumerate(b.split("\n")):
            d.text((x + 28, 430 + j * 40), line, font=F["body"], fill=INK)
        if i < 3:
            d.polygon(
                [
                    (x + sw + 6, 470),
                    (x + sw + GAP - 10, 490),
                    (x + sw + 6, 510),
                ],
                fill=LINE,
            )

    # CF → INS mapping
    d.text((MX, 680), "关键映射：哪条冲突喂给哪条洞察（条数≠主推）", font=F["h2"], fill=INK)
    rows = [
        ("CF-01 存在感×不浓烈", "INS-C01 存在感×得体", "8", "→ DIR-01", "公共场合选择张力"),
        ("CF-02 独特×怕选错", "INS-C02 独特×安全", "15", "→ DIR-03", "试香到正装恐惧"),
        ("CF-03 奢华×不炫耀", "INS-C03 贵气×低调", "5", "→ DIR-02", "判断标准/哲学张力"),
        ("需求 N01 干净肌肤", "INS-N01", "6", "→ DIR-04", "品类延伸，非主战场"),
        ("需求 N04 季节清透", "INS-N04", "14", "不生成 DIR", "档期可消化，非哲学"),
    ]
    y = 760
    rr(d, [MX, y, W - MX, y + 56], SOFT, 6)
    for i, h in enumerate(["冲突/需求标签", "洞察簇", "证据条", "转化", "对「时刻衣柜」的含义"]):
        d.text((MX + 24 + i * 700, y + 14), h, font=F["small"], fill=MUTED)

    for i, (a, b, n, c, m) in enumerate(rows):
        yy = 830 + i * 110
        bg = WHITE if i % 2 == 0 else SOFT
        rr(d, [MX, yy, W - MX, yy + 100], bg, 6)
        vals = [a, b, n + " 条", c, m]
        for j, v in enumerate(vals):
            col = RED if (j == 2 and n == "5") or (j == 3 and "DIR-02" in c) else INK
            d.text((MX + 24 + j * 700, yy + 32), v, font=F["body"], fill=col)

    rr(d, [MX, 1410, W - MX, 1920], SOFT_T, 14)
    d.text((MX + 40, 1450), "本步推理结论 → 对第二章命题的含义", font=F["h3"], fill=TEAL)
    lines = [
        "1. 冲突真实存在，且集中在「此刻如何得体 / 如何独特又不选错 / 如何贵气又不炫耀」——正是场景层选择剧本要处理的张力。",
        "2. 证据最多的 N04（季节清透）不生成方向：证明系统不会被热度带跑；热度需求 ≠ 品牌战场。",
        "3. 证据最少的 C03 仍进入候选：因为它咬合 MFK 作者性（奢华×低调），这是「衣柜」需要的判断标准，不是货架陈列。",
        "→ Q1 通过：场景层作为主攻层，有冲突编码支撑；「时刻衣柜」不是空概念。",
    ]
    for i, line in enumerate(lines):
        wrap(d, line, (MX + 40, 1530 + i * 85), F["body"], INK, W - 2 * MX - 80, 34)

    footer(d, "Source: TAG·CF-01~04；INS 平台分布字段（C02=15 / N04=14 / C01=8 / N01=6 / C03=5）")
    save(img, "mfk_03_v3_q1_conflict.png")


def p03_4():
    """Q2+ partial Q3: DIR conversion + kill matrix"""
    img, d = new()
    header(
        d,
        "03 / INFERENCE Q2  ·  4 of 5",
        "推理②：词语层为何被杀死，场景/资产候选如何过闸",
        "验证问题 Q2：空话闸是否印证「避开词语红海」；顺带看谁能进 BRD。",
    )

    # Conversion mini + kill
    d.text((MX, 340), "四条候选如何生成，又如何被闸门处理", font=F["h2"], fill=INK)

    cards = [
        (
            "DIR-01",
            "日常可穿高端香",
            "← C01",
            "空话命中「高级感」",
            "需改写",
            "× 未升格",
            RED,
            "印证：词语层主攻不可行",
        ),
        (
            "DIR-02",
            "嗅觉精准主义",
            "← C03",
            "无空话 · 竞品不可替换",
            "需补证",
            "→ BRD-02 主推",
            TEAL,
            "判断标准：精准克制",
        ),
        (
            "DIR-03",
            "从试到拥有",
            "← C02",
            "无空话 · 旅程可运营",
            "通过",
            "→ BRD-01 确认",
            GOLD,
            "选择路径：试香→签名",
        ),
        (
            "DIR-04",
            "身体与空间",
            "← N01",
            "可被 Byredo/Le Labo 替换",
            "需补证",
            "× 未升格",
            ORANGE,
            "需求真但无 MFK 壁垒",
        ),
    ]
    cw = (W - 2 * MX - 3 * GAP) // 4
    for i, (code, name, src, gate, chk, out, col, mean) in enumerate(cards):
        x = MX + i * (cw + GAP)
        rr(d, [x, 420, x + cw, 1180], WHITE, 12)
        d.rectangle([x, 420, x + cw, 432], fill=col)
        d.text((x + 24, 460), code, font=F["h3"], fill=col)
        d.text((x + 24, 520), name, font=F["body"], fill=INK)
        d.text((x + 24, 580), src, font=F["small"], fill=MUTED)
        d.line([(x + 24, 640), (x + cw - 24, 640)], fill=LINE, width=1)
        d.text((x + 24, 680), "闸门观察", font=F["label"], fill=MUTED)
        wrap(d, gate, (x + 24, 730), F["body"], INK, cw - 48, 34)
        d.text((x + 24, 860), "CHK", font=F["label"], fill=MUTED)
        d.text((x + 24, 910), chk, font=F["h3"], fill=col)
        d.text((x + 24, 980), out, font=F["h3"], fill=col)
        rr(d, [x + 16, 1060, x + cw - 16, 1140], SOFT, 8)
        wrap(d, mean, (x + 28, 1085), F["small"], INK, cw - 56, 28)

    # Decision tree strip
    rr(d, [MX, 1240, W - MX, 1920], SOFT, 14)
    d.text((MX + 40, 1280), "本步推理结论 → 对第二章命题的含义", font=F["h3"], fill=INK)
    lines = [
        "Q2 通过：DIR-01 因「高级感」被空话闸杀死——与第二章「避开词语红海」同向；系统用规则复现了战场判断，不是事后圆场。",
        "DIR-04 虽有真实需求，但「换成竞品仍成立」= 是 → 不能当长期资产；印证第二章「缺口在选择逻辑，不在再做一个品类故事」。",
        "存活的只有两条：DIR-02（哲学判断）与 DIR-03（试香旅程）。它们正是把「欣赏」变成「确定选择」所需的一对机制。",
        "→ 下一页完成 Q3：这两条如何拼回「可按时刻编排的大师香氛衣柜」，并解释为何主推是证据更少的那条。",
    ]
    for i, line in enumerate(lines):
        wrap(d, line, (MX + 40, 1360 + i * 120), F["body"], INK, W - 2 * MX - 80, 36)

    footer(d, "Source: DIR-01~04；CHK-001~004（空话命中 / 竞品可替换 / 结果）；压力测试五维")
    save(img, "mfk_03_v4_q2_gates.png")


def p03_5():
    """Q3 + map back to Part 02 wardrobe"""
    img, d = new()
    header(
        d,
        "03 / INFERENCE Q3  ·  5 of 5",
        "推理③：过闸方向如何验证「时刻衣柜」，并决定主推",
        "验证问题 Q3：选择逻辑能否落到可运营资产；主推公式 = 稀缺 × 难复制。",
    )

    # Causal chain
    rr(d, [MX, 330, W - MX, 480], SOFT_T, 12)
    d.text((MX + 36, 355), "主推因果链（请按箭头读）", font=F["label"], fill=TEAL)
    wrap(
        d,
        "CF-03 奢华×不炫耀 → INS-C03 贵气×低调（5条） → DIR-02 嗅觉精准主义 → CHK 不可替换 → BRD-02「精准的感性」主推",
        (MX + 36, 405),
        F["body"],
        INK,
        W - 2 * MX - 72,
        36,
    )

    # Two BRDs mapped to Part 02
    rr(d, [MX, 520, MX + CW + 40, 1280], WHITE, 14)
    d.rectangle([MX, 520, MX + CW + 40, 532], fill=RED)
    d.text((MX + 32, 560), "BRD-02 主推 · 哲学层", font=F["h3"], fill=RED)
    d.text((MX + 32, 620), "精准的感性", font=F["h2"], fill=INK)
    for i, line in enumerate(
        [
            "主张：多一分则腻，少一分则寡",
            "逻辑：要的不是更浓，是更准的克制",
            "资产：Francis 署名判断标准",
            "CHK：空话=否；竞品替换=否",
            "评分：稀缺5 · 难复制5",
            "      可运营3 · 复利4",
            "",
            "验证第二章哪一句：",
            "「衣柜」需要统一选择语言",
            "——语言的内核是精准克制，",
            "不是又一套情绪形容词。",
        ]
    ):
        d.text((MX + 32, 700 + i * 40), line, font=F["body"], fill=INK)

    rr(d, [MX + CW + GAP + 40, 520, MX + 2 * CW + GAP + 80, 1280], WHITE, 14)
    d.rectangle(
        [MX + CW + GAP + 40, 520, MX + 2 * CW + GAP + 80, 532], fill=TEAL
    )
    x = MX + CW + GAP + 72
    d.text((x, 560), "BRD-01 确认 · 旅程层", font=F["h3"], fill=TEAL)
    d.text((x, 620), "从试香到签名", font=F["h2"], fill=INK)
    for i, line in enumerate(
        [
            "主张：先在肌肤上认识它",
            "逻辑：样本→正装的选择恐惧闭环",
            "资产：可运营咨询 / 档案路径",
            "CHK：通过；履约成本需试点控",
            "评分：稀缺4 · 难复制4",
            "      可运营5 · 复利5",
            "",
            "验证第二章哪一句：",
            "欣赏 → 确定选择 的转化",
            "靠旅程机制落地，把「衣橱」",
            "从货架变成可编排体验。",
        ]
    ):
        d.text((x, 700 + i * 40), line, font=F["body"], fill=INK)

    # Why not C02 as main
    x = MX + 2 * (CW + GAP) + 80
    rr(d, [x, 520, W - MX, 1280], WHITE, 14)
    d.rectangle([x, 520, W - MX, 532], fill=GOLD)
    d.text((x + 32, 560), "反常识：为何主推不是", font=F["h3"], fill=GOLD)
    d.text((x + 32, 620), "证据最多的 C02？", font=F["h2"], fill=INK)
    for i, line in enumerate(
        [
            "C02=15 条 → BRD-01 确认",
            "C03=5 条 → BRD-02 主推",
            "",
            "因为条数只决定「能否进漏斗」",
            "主推看稀缺 × 难复制：",
            "",
            "旅程可被柜台流程模仿；",
            "哲学若绑定调香师署名，",
            "竞品难以平移。",
            "",
            "故：哲学主推 + 旅程确认",
            "= 时刻衣柜的完整验证式",
        ]
    ):
        d.text((x + 32, 700 + i * 40), line, font=F["body"], fill=INK)

    # Final validation scorecard
    rr(d, [MX, 1340, W - MX, 1920], SOFT_G, 14)
    d.text((MX + 40, 1380), "第三章收束：对第二章命题的验证结果", font=F["h2"], fill=INK)
    results = [
        ("Q1 场景冲突", "通过", "冲突可命名、可回溯；时刻选择张力成立"),
        ("Q2 避开词语", "通过", "「高级感」类主张被空话闸杀死，词语层不可主攻"),
        ("Q3 选择逻辑", "通过*", "BRD-02 给判断标准，BRD-01 给试香路径；*规模化仍 PoC 暂缓"),
        ("命题映射", "成立", "「大师香氛衣柜」= 精准感性（哲学）× 试香到签名（旅程）在场景层运营"),
    ]
    for i, (k, v, note) in enumerate(results):
        yy = 1480 + i * 95
        d.text((MX + 40, yy), k, font=F["h3"], fill=TEAL)
        d.text((MX + 420, yy), v, font=F["h3"], fill=RED if v.startswith("通过") or v == "成立" else INK)
        d.text((MX + 700, yy), note, font=F["body"], fill=INK)

    footer(
        d,
        "Source: BRD-01/02 状态字段；CHK-002/003；资产四问；对齐 PART02「时刻衣柜」命题",
    )
    save(img, "mfk_03_v5_q3_validate.png")


if __name__ == "__main__":
    p01()
    p03_1()
    p03_2()
    p03_3()
    p03_4()
    p03_5()
    print("DONE: 6 slides")
