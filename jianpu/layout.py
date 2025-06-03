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

        if (note.get("rest") or note.get("key") or note.get("time_signature") or note.get("tempo")) and not note.get("lyric"):
            continue

        if not note.get("pitch") and not note.get("lyric") and not note.get("rest"):
            continue  # 避免空 note 被绘制

        draw_note(c, x, y, note)
        note_positions.append((x, y, note))
        x += DURATION_WIDTH_MAP.get(note.get("duration", 1), NOTE_STEP)

        if x > PAGE_WIDTH - RIGHT_MARGIN:
            x = LEFT_MARGIN
            y -= LINE_HEIGHT

    # 连音
    for i in range(len(note_positions) - 1):
        x1, y1, note = note_positions[i]
        x2, _, _ = note_positions[i + 1]
        if note.get("tie"):
            y1a = y1 + TIE_ARC_BASE
            y2a = y1a + TIE_ARC_HEIGHT
            c.arc(x1 - 6, y1a, x2 + 6, y2a, 0, 180)

    # 连线（beam）
    beams = defaultdict(list)
    for x, y, note in note_positions:
        if "beam" in note:
            beams[note["beam"]].append((x, y))
    for group in beams.values():
        if len(group) >= 2:
            x_start = group[0][0] - 6
            x_end = group[-1][0] + 6
            y_beam = group[0][1] - BEAM_LINE_OFFSET
            c.line(x_start, y_beam, x_end, y_beam)

    c.save()