# jianpu/layout.py
from collections import defaultdict
from jianpu.renderer import draw_note
from jianpu.constants import *
from reportlab.pdfgen import canvas

def draw_sheet(notes, output_path):
    from reportlab.pdfgen import canvas
    from jianpu.symbols import get_dynamics_symbol

    c = canvas.Canvas(output_path, pagesize=A4)
    c.setFont(FONT_LYRIC, 18)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - TOP_MARGIN, TITLE)

    # 查找调号/拍号/速度设置
    key, time_signature, tempo = "-", "-/-", 0
    for note in notes:
        if "key" in note: key = note["key"]
        if "time" in note: time_signature = note["time"]
        if "tempo" in note: tempo = note["tempo"]
        if key and time_signature and tempo: break

    c.setFont(FONT_LYRIC, 12)
    c.drawString(LEFT_MARGIN, META_Y, f"调式: {key}")
    c.drawString(LEFT_MARGIN + 120, META_Y, f"节拍: {time_signature}")
    c.drawString(LEFT_MARGIN + 240, META_Y, f"速度: ♩={tempo}")
    x, y = LEFT_MARGIN, PAGE_HEIGHT - START_Y_OFFSET
    note_positions = []

    for note in notes:
        if note.get("bar"):
            c.line(x, y - 5, x, y + 15)
            x += 10
            continue
        if note.get("repeat") in ["start", "end"]:
            c.drawString(x, y + 15, REPEAT_SYMBOLS[note["repeat"]])
            x += 10
            continue

        if (note.get("key") or note.get("time_signature") or note.get("tempo")) and not note.get("lyric"):
            continue

        if not note.get("pitch") and not note.get("lyric") and not note.get("rest"):
            continue  # 避免空 note 被绘制

        draw_note(c, x, y, note)
        note_positions.append((x, y, note))
        if note.get("lyric") and len(note["lyric"]) > 2:
            x += NOTE_STEP + len(note["lyric"]) * 2  # 或动态系数
        else:
            x += DURATION_WIDTH_MAP.get(note.get("duration", 1), NOTE_STEP)

        if x > PAGE_WIDTH - RIGHT_MARGIN:
            x = LEFT_MARGIN
            y -= LINE_HEIGHT

    # 连音
    # ----------- Tie 连音线渲染逻辑（支持 group + 跨行分段绘制） -----------
    tie_groups = defaultdict(list)

    # 1. 构建 tie 分组（支持 tie_group_id，兼容 legacy tie: true）
    for idx, (x, y, note) in enumerate(note_positions):
        if "tie_group_id" in note:
            gid = note["tie_group_id"]
            tie_groups[gid].append((x, y, note))
        elif note.get("tie"):  # legacy 单段 tie: true
            # 为每个 tie: true 的 note 自动构建一段 group（与下一个 note）
            gid = f"__implicit_tie_{idx}__"
            tie_groups[gid].append((x, y, note))
            if idx + 1 < len(note_positions):
                tie_groups[gid].append(note_positions[idx + 1])

    # 2. 渲染每组 tie（同行画，跨行跳过）
    for group in tie_groups.values():
        for i in range(len(group) - 1):
            x1, y1, note1 = group[i]
            x2, y2, note2 = group[i + 1]
            if y1 != y2:
                continue  # 跨行不连，自动断开
            y_base = y1 + TIE_ARC_BASE
            # c.setStrokeColorRGB(0.1, 0.8, 0.1)  # 绿色辅助
            c.arc(x1 - 6, y_base, x2 + 6, y_base + TIE_ARC_HEIGHT, 0, 180)
            # c.setStrokeColorRGB(0, 0, 0)  # 恢复黑色

        # 连线（beam）
        # ✅ 先分组
        beams = defaultdict(list)
        for x, y, note in note_positions:
            if "beam" in note:
                beam_id = note["beam"]
                beams[beam_id].append((x, y, note))

        # ✅ 然后绘制 beam 连线
        for beam_id, group in beams.items():
            if len(group) < 2:
                continue  # 单个音符不能连线

            # ⛳ 按 Y 值（行号）分组，避免跨行连接
            lines = defaultdict(list)
            for x, y, note in group:
                lines[y].append((x, y, note))

            for y, line_group in lines.items():
                if len(line_group) < 2:
                    continue

                x_start = line_group[0][0] - 6
                x_end = line_group[-1][0] + 6

                # ⛳ 决定 beam 横线层数（0.5 = 八分 = 一条；0.25 = 十六分 = 两条）
                durations = [n.get("duration", 1) for _, _, n in line_group]
                beam_level = max(2 if d == 0.25 else 1 for d in durations)

                for i in range(beam_level):
                    y_beam = y - BEAM_LINE_OFFSET - i * 3
                    c.setLineWidth(1.2)
                    c.line(x_start, y_beam, x_end, y_beam)
        # 调试时添加
        # for group in beams.values():
        #     if len(group) >= 2:
        #         x1, y1 = group[0]
        #         x2, y2 = group[-1]
        #         c.setStrokeColorRGB(1, 0, 0)
        #         c.rect(x1 - 10, y1 - 10, x2 - x1 + 20, 20, stroke=1, fill=0)

    c.save()