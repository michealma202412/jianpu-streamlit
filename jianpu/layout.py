# jianpu/layout.py
from collections import defaultdict
from jianpu.renderer import draw_note
from jianpu.constants import *
from reportlab.pdfgen import canvas

# —————————————————————————————————————————
# 计算任意 token（音符 / bar / repeat）在页面上需占的水平宽度
# —————————————————————————————————————————
def get_token_width(token):
    # 1) 小节线 / repeat
    if token.get("bar") or token.get("repeat") in ("start", "end"):
        return BAR_WIDTH

    # 2) 普通音符
    width = DURATION_WIDTH_MAP.get(token.get("duration", 1), NOTE_STEP)

    # 长歌词补偿
    lyric = token.get("lyric", "")
    if lyric and len(lyric) > 2:
        width += len(lyric) * 2  # 自行调系数

    # dash
    if token.get("duration") in (2,3,4):
        dash_cnt = token["duration"] - 1
        width += NOTE_DASH_OFFSET * dash_cnt

    return width


# —————————————————————————————————————————
# 主要绘制函数
# —————————————————————————————————————————
def draw_sheet(notes, output_path):
    # —— 一次扫 metadata ——  
    meta = {"key": "-", "time": "-/-", "tempo": 0}
    real_notes = []
    for token in notes:
        if "key" in token:
            meta["key"] = token["key"]
        elif "time" in token:
            meta["time"] = token["time"]
        elif "tempo" in token:
            try:
                meta["tempo"] = int(token["tempo"])
            except:
                meta["tempo"] = 0
        else:
            real_notes.append(token)

    # —— 打开画布，写页眉 ——  
    c = canvas.Canvas(output_path, pagesize=A4)
    c.setFont(FONT_LYRIC,18)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT-TOP_MARGIN, TITLE)
    c.setFont(FONT_LYRIC,12)
    c.drawString(LEFT_MARGIN, META_Y, f"调式: {meta['key']}")
    c.drawString(LEFT_MARGIN+120, META_Y, f"节拍: {meta['time']}")
    c.drawString(LEFT_MARGIN+240, META_Y, f"速度: ♩={meta['tempo']}")

    # ② 主循环
    x, y = LEFT_MARGIN, PAGE_HEIGHT - START_Y_OFFSET
    note_positions = []

    for token in real_notes:
        # --------- 1) 计算本 token 宽度 ---------
        tok_w = get_token_width(token)

        # --------- 2) 换行判定 ---------
        if x + tok_w > PAGE_WIDTH - RIGHT_MARGIN:
            x = LEFT_MARGIN
            y -= LINE_HEIGHT

        # --------- 3) 绘制 ---------
        if token.get("bar"):
            c.line(x, y - 5, x, y + 15)
        elif token.get("repeat") in ("start", "end"):
            c.drawString(x, y + 15, REPEAT_SYMBOLS[token["repeat"]])
        else:
            draw_note(c, x, y, token)
            note_positions.append((x, y, token))

        # --------- 4) 光标右移 ---------
        x += tok_w

    # ————————————————————
    # 连音 (tie)
    # ————————————————————
    tie_groups = defaultdict(list)
    for idx, (x0, y0, n0) in enumerate(note_positions):
        if "tie_group_id" in n0:
            tie_groups[n0["tie_group_id"]].append((x0, y0, n0))
        elif n0.get("tie"):
            # 为每个 tie: true 的 note 自动构建一段 group（与下一个 note）
            gid = f"implicit_tie_{idx}"
            tie_groups[gid].append((x0, y0, n0))
            if idx + 1 < len(note_positions):
                tie_groups[gid].append(note_positions[idx + 1])

    # 2. 渲染每组 tie（同行画，跨行跳过）
    for group in tie_groups.values():
        for i in range(len(group) - 1):
            x1, y1, _ = group[i]
            x2, y2, _ = group[i + 1]
            if y1 != y2:
                continue  # 跨行不连，自动断开
            y_base = y1 + TIE_ARC_BASE
            # c.setStrokeColorRGB(0.1, 0.8, 0.1)  # 绿色辅助
            c.arc(x1 - 6, y_base, x2 + 6, y_base + TIE_ARC_HEIGHT, 0, 180)
            # c.setStrokeColorRGB(0, 0, 0)  # 恢复黑色

    # ————————————————————
    # beam（八分 / 十六分连接线）
    # ————————————————————
    beams = defaultdict(list)
    for x0, y0, n0 in note_positions:
        if "beam" in n0 and n0.get("duration", 1) <= 0.5:
            beams[n0["beam"]].append((x0, y0, n0))

    for _, group in beams.items():
        # 按行分组，防跨行
        rows = defaultdict(list)
        for x0, y0, n0 in group:
            rows[y0].append((x0, n0))

        for y0, row in rows.items():
            if len(row) < 2:
                continue
            x_start = row[0][0] - 6
            x_end = row[-1][0] + 6
            level = max(2 if n.get("duration", 1) == 0.25 else 1
                        for _, n in row)
            for i in range(level):
                c.setLineWidth(1.2)
                c.line(x_start,
                       y0 - BEAM_LINE_OFFSET - i * 3,
                       x_end,
                       y0 - BEAM_LINE_OFFSET - i * 3)

    c.save()