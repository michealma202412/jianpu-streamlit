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

    # 歌词宽度测量：支持多行
    lyrics = token.get("lyric") or token.get("lyrics")
    if lyrics:
        if isinstance(lyrics, (list, tuple)):
            widths = [stringWidth(str(line), FONT_LYRIC, FONT_SIZE_LYRIC) for line in lyrics]
            max_text_w = max(widths)
            pad = FONT_SIZE_LYRIC * (len(lyrics) * 0.10)
        else:
            lines = str(lyrics).split("\n")
            widths = [stringWidth(line, FONT_LYRIC, FONT_SIZE_LYRIC) for line in lines]
            max_text_w = max(widths)
            pad = FONT_SIZE_LYRIC * (len(lines) * 0.10)
        base = max(base, max_text_w + pad)
    else:
        base = max(base, NOTE_STEP * 1.5)
    # dash
    if dur in (2, 3, 4):
        dash_cnt = int(dur) - 1
        dw = dash_width()  # 单个 '-' 宽度
        gap = FONT_SIZE_NOTE/3
        base += dash_cnt * (dw + gap)

    return base

def draw_sheet(notes, output_path):
    # —— 一次扫 metadata ——  
    meta = {"title": None, "key": "-", "time": "-/-", "tempo": 0,
            "composer": None, "lyricist": None, "translator": None}
    real_notes = []
    for token in notes:
        if "title" in token:
            meta["title"] = token["title"]
        elif "key" in token:
            meta["key"] = token["key"]
        elif "time" in token:
            meta["time"] = token["time"]
        elif "tempo" in token:
            try:
                meta["tempo"] = int(token["tempo"])
            except:
                meta["tempo"] = 0
        elif "composer" in token:
            meta["composer"] = token["composer"]
        elif "lyricist" in token:
            meta["lyricist"] = token["lyricist"]
        elif "translator" in token:
            meta["translator"] = token["translator"]
        else:
            real_notes.append(token)

    # —— 打开画布，写页眉 ——  
    c = canvas.Canvas(output_path, pagesize=A4)
    # 若 TXT 中解析到 title，则显示，否则用默认常量
    display_title = meta.get("title") or TITLE
    c.setFont(FONT_LYRIC, 18)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT-TOP_MARGIN, display_title)
    c.setFont(FONT_LYRIC,12)
    # 先画调式
    x = LEFT_MARGIN
    c.setFont(FONT_LYRIC, 12)
    text = f"调式: {meta['key']}"
    c.drawString(x, META_Y, text)
    # 用 stringWidth 测量这段文字的真实宽度，再加上一个固定间隔
    x += stringWidth(text, FONT_LYRIC, 12) + 20

    # 然后画节拍
    text = f"节拍: {meta['time']}"
    c.drawString(x, META_Y, text)
    x += stringWidth(text, FONT_LYRIC, 12) + 20

    # 如果有速度才画，并且才推进游标
    if meta.get("tempo", 0) > 0:
        text = f"速度: {meta['tempo']}"
        c.drawString(x, META_Y, text)
        x += stringWidth(text, FONT_LYRIC, 12) + 20

    # 作词
    if meta.get("lyricist"):
        text = f"作词: {meta['lyricist']}"
        c.drawString(x, META_Y, text)
        x += stringWidth(text, FONT_LYRIC, 12) + 20

    # 翻译
    if meta.get("translator"):
        text = f"翻译: {meta['translator']}"
        c.drawString(x, META_Y, text)
        x += stringWidth(text, FONT_LYRIC, 12) + 20

    # 作曲
    if meta.get("composer"):
        text = f"作曲: {meta['composer']}"
        c.drawString(x, META_Y, text)
        x += stringWidth(text, FONT_LYRIC, 12) + 20
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
        # —— 1) 先算本行最多有几行歌词 ——  
        max_rows = 1
        for token, _ in line:
            raw = token.get("lyric") or token.get("lyrics") or ""
            if isinstance(raw, (list, tuple)):
                rows = len(raw)
            else:
                rows = str(raw).count("\n") + 1
            max_rows = max(max_rows, rows)

        total_min = sum(w for _, w in line)
        # 给每个 gap 打权重：bar 前/后 和 带 dash 的“不分配额外空白”，其它 gap=1
        # === 改进版 gap 权重 & 限制最大拉伸 ===
        # 普通 gap 权重 1，bar/dash gap 权重 EPS（≈0.2）
        EPS = 0.2  
        gap_weights = []
        for i in range(len(line)-1):
            curr, _ = line[i]
            nxt,  _ = line[i+1]
            if not nxt.get("lyric"):
                gap_weights.append(EPS)  # 而不是 1
            elif curr.get("bar") or nxt.get("bar") or curr.get("duration") in (1.5, 2, 3, 4):
                gap_weights.append(EPS)
            else:
                gap_weights.append(1)
        total_weight = sum(gap_weights)
        if total_weight <= 0:
            extra_unit = 0
        else:
            # 计算每个 weight 单位对应的额外空间
            raw_extra = max(0, (max_w - total_min) / total_weight)
            # 给每个 gap 的额外空间加上一个上限，比如不超过 NOTE_STEP * 1.5
            max_extra_per_unit = NOTE_STEP * 1.5
            extra_unit = min(raw_extra, max_extra_per_unit)

        x = LEFT_MARGIN
        for idx, (token, min_w) in enumerate(line):

            # 小节线
            if token.get("bar"):
                 # 如果不是这一行的第一个 token，就减掉它前面的空白（extra_unit * gap_weights[idx-1]）
                prev_extra = extra_unit * gap_weights[idx-1] if idx > 0 else 0
                # 2) 动态偏移：上一元素 min_w 的 40%（如果有上一元素），否则默认半个 NOTE_STEP
                if idx > 0:
                    shift = NOTE_STEP/3
                else:
                    shift = NOTE_STEP * 0.5
                
                # 最终 x 坐标
                bar_x = x - shift - prev_extra
                c.line(bar_x, y-5, bar_x, y+15)
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
                this_extra = extra_unit * gap_weights[idx]
                this_extra = min(this_extra, NOTE_STEP*1.2)
                x += this_extra

        # —— 2) 画完这一行之后，下移：取 LINE_HEIGHT 与歌词底部到下行基线的最小安全距离二者最大，再加上多行歌词占用的高度
        extra_v = (max_rows - 1) * (FONT_SIZE_LYRIC + 2)
        # 计算从音符中心到歌词底部的距离，再加上一个小缓冲
        min_gap = abs(LYRIC_OFFSET_Y) + max(FONT_SIZE_LYRIC , FONT_SIZE_NOTE)*2
        # 最终行距 = max(标准行高, min_gap) + 额外行高
        row_gap = max(LINE_HEIGHT, min_gap) + extra_v
        y -= row_gap

    # ————————————————————
    # 连音 (tie) & 跨行半连音线
    # ————————————————————
    tie_groups = defaultdict(list)
    for idx, (x0, y0, n0) in enumerate(note_positions):
        if n0.get("tie"):
            # 直接使用 idx 生成显式组，或复用已有 tie_group_id
            gid = n0.get("tie_group_id", f"implicit_tie_{idx}")
            tie_groups[gid].append((x0, y0, n0))
            # 与下一 note 连
            if idx + 1 < len(note_positions):
                tie_groups[gid].append(note_positions[idx + 1])

    # 2. 渲染每组 tie（同行画，跨行跳过）
    for group in tie_groups.values():
        # 检查本组是否含有高音点（pitch ≥8）
        has_high_dot = any(n.get("pitch", 0) >= 8 for x0, y0, n in group)
        # 根据是否含高音点，动态调整弧线起始高度和高度
        if has_high_dot:
            arc_base   = TIE_ARC_BASE
            arc_height = TIE_ARC_HEIGHT
        else:
            arc_base   = TIE_ARC_BASE   * 0.66
            arc_height = TIE_ARC_HEIGHT * 0.80
            
        for i in range(len(group) - 1):
            x1, y1, _ = group[i]
            x2, y2, _ = group[i + 1]
            # 同行完整连音
            if y1 == y2:
                y_base = y1 + arc_base
                c.arc(x1, y_base, x2, y_base + arc_height, 0, 180)
            else:
                # 跨行半连：行尾画半弧（从180°到270°）
                right_edge = PAGE_WIDTH - RIGHT_MARGIN
                yb1 = y1 + arc_base
                c.arc(
                    x1 - FONT_SIZE_NOTE/3, yb1,
                    right_edge, yb1 + arc_height,
                    90, 90
                )
                # 行首画半弧（从270°到360°）
                left_edge = LEFT_MARGIN
                yb2 = y2 + arc_base
                c.arc(
                    left_edge - FONT_SIZE_NOTE, yb2,
                    x2 + FONT_SIZE_NOTE/3, yb2 + arc_height,
                    0, 90
                )

    # ——— 连续 dash 连接（按累积时值≤1分组） ———
    line_len = NOTE_STEP / 2
    dash_y = lambda y0: y0 - BEAM_LINE_OFFSET

    # 1) 收集每行所有“可 beam”音符：有效时值 < 1
    rows = defaultdict(list)
    for idx, (x0, y0, n0) in enumerate(note_positions):
        dur0 = n0.get("duration", 1)
        eff = dur0 * (1.5 if n0.get("dot") else 1.0) -(1 if dur0 == 1 else 0)   # dot 算成 ×1.5
        if eff < 1.0:
            rows[y0].append((idx, x0, eff))

    # 2) 对每行，按 idx 排序，再分段：只要连续且累加 eff≤1 就画同一根 dash
    for y0, items in rows.items():
        items.sort(key=lambda t: t[0])
        group = []
        total = 0.0
        for idx, x0, eff in items:
            if group and idx == group[-1][0] + 1 and total + eff <= 1.0:
                group.append((idx, x0, eff))
                total += eff
            else:
                # 画上一段
                if len(group) >= 2:
                    xs = [p for _, p, _ in group]
                    start = xs[0] + line_len/2
                    end   = xs[-1] - line_len/2
                    if end > start:
                        c.line(start, dash_y(y0), end, dash_y(y0))
                # 重置新段
                group = [(idx, x0, eff)]
                total = eff
        # 收尾
        if len(group) >= 2:
            xs = [p for _, p, _ in group]
            start = xs[0] + line_len/2
            end   = xs[-1] - line_len/2
            if end > start:
                c.line(start, dash_y(y0), end, dash_y(y0))
    c.save()
