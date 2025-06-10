# jianpu/layout.py
from collections import defaultdict
from reportlab.pdfbase.pdfmetrics import stringWidth
from jianpu.renderer import draw_note
from jianpu.constants import *
from reportlab.pdfgen import canvas
from jianpu.renderer import dash_width

def get_min_token_width(token):
    """计算 token 的‘最小’宽度，不加任何行拉伸"""
    # 小节线 / repeat
    if token.get("bar") or token.get("repeat") in ("start", "end"):
        return BAR_WIDTH

    # 基于时值的基本宽度
    dur = token.get("duration", 1)
    if dur in (2, 3, 4):
        # 半拍/附点半拍/全音符：先给一拍的宽度
        base = NOTE_STEP
    else:
        base = DURATION_WIDTH_MAP.get(dur, NOTE_STEP)

    # 歌词宽度测量（加一点 padding）
    lyric = token.get("lyric", "")
    if lyric:
        text_w = stringWidth(lyric, FONT_LYRIC, FONT_SIZE_LYRIC)
        base = max(base, text_w + 6)   # 歌词留 6pt 缓冲

    # dash
    if dur in (2, 3, 4):
        dash_cnt = int(dur) - 1
        dw = dash_width()  # 单个 '-' 宽度
        gap = 2
        base += dash_cnt * (dw + gap)

    return base

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

    # —— 分行 & 计算最小宽度 —
    max_w = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    lines = []
    cur_line = []
    acc_w = 0
    for token in real_notes:
        w = get_min_token_width(token)
        # 如果放不下，就换行
        if cur_line and acc_w + w > max_w:
            lines.append(cur_line)
            cur_line = []
            acc_w = 0
        cur_line.append((token, w))
        acc_w += w
    if cur_line:
        lines.append(cur_line)

    # 逐行绘制
    y = PAGE_HEIGHT - START_Y_OFFSET
    note_positions = []
    for line in lines:
        total_min = sum(w for _, w in line)
        # 1) 给每个 gap 打权重：dash 前的 gap=0，其它 gap=1
        gap_weights = []
        for i in range(len(line)-1):
            tok, _ = line[i]
            gap_weights.append(0 if tok.get("duration") in (2,3,4) else 1)
        total_weight = sum(gap_weights) or 1
        # 2) 按权重分配剩余空间
        extra_unit = max(0, (max_w - total_min) / total_weight)

        x = LEFT_MARGIN
        for idx, (token, min_w) in enumerate(line):

            # 小节线
            if token.get("bar"):
                c.line(x, y-5, x, y+15)
            elif token.get("repeat") in ("start","end"):
                c.drawString(x, y+15, REPEAT_SYMBOLS[token["repeat"]])
            else:
                draw_note(c, x, y, token)
                note_positions.append((x, y, token))

            # —— 光标右移 ——  
            # 先移动最小宽度
            x += min_w
            # 再根据 weight 分配 extra（dash 前 weight=0，就不会加空白）
            if idx < len(line) - 1:
                x += extra_unit * gap_weights[idx]

        y -= LINE_HEIGHT

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