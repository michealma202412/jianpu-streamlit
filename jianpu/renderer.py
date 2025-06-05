# jianpu/renderer.py
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from jianpu.constants import *
from jianpu.symbols import get_pitch_symbol, get_ornament_symbol, get_dynamics_symbol

# 字体注册
pdfmetrics.registerFont(TTFont(FONT_LYRIC, FONT_PATH))

def draw_note(c, x, y, note):
    pitch_num = note.get("pitch", 0)
    pitch = get_pitch_symbol(pitch_num)

    # 判断八度
    if pitch_num >= 8:
        octave = 1
    elif -7 <= pitch_num <= -1:
        octave = -1
    else:
        octave = 0

    # 设置音符字体（先处理倚音 / 重音样式）
    font_size = FONT_SIZE_NOTE
    if note.get("is_grace"):
        font_size -= 4
    if note.get("accent"):
        font_size += 2
    c.setFont(FONT_NOTE, font_size)

    # 主音符
    c.drawCentredString(x, y, pitch)

    # 高低音点
    # 高低音点应在数字正上/正下方，可适当微调横向偏移为 -1 ~ +1 之间
    if octave == 1:
        c.circle(x, y + FONT_SIZE_NOTE * HIGH_DOT_Y_OFFSET_RATIO, DOT_RADIUS, fill=1)
    elif octave == -1:
        c.circle(x, y - FONT_SIZE_NOTE * LOW_DOT_Y_OFFSET_RATIO, DOT_RADIUS, fill=1)

    # 附点
    if note.get("dot"):
        c.circle(
            x + FONT_SIZE_NOTE * DOT_OFFSET_X_RATIO,
            y + FONT_SIZE_NOTE * DOT_OFFSET_Y_RATIO,
            DOT_RADIUS,
            fill=1
        )
    # 装饰音
    ornament = get_ornament_symbol(note.get("ornament"))
    if ornament:
        c.setFont("Helvetica", 10)
        c.drawCentredString(x, y + 12, ornament)

    # 休止符（pitch = 0）
    if note.get("rest"):
        c.setFont(FONT_NOTE, font_size)
        c.drawCentredString(x, y, "0")  # 避免显示不出的休止符 𝄽

    # 歌词
    lyric = note.get("lyric", "")
    if lyric:
        c.setFont(FONT_LYRIC, FONT_SIZE_LYRIC)
        c.drawCentredString(x, y + LYRIC_OFFSET_Y, lyric)

    # 力度
    dynamics = note.get("dynamics")
    if dynamics:
        sym = get_dynamics_symbol(dynamics)
        c.setFont(FONT_NOTE, 10)
        c.drawCentredString(x, y + 24, sym)

    # # 🎵 中横线节奏辅助线（简谱风格专用）
    # if ENABLE_NOTE_MIDLINE:
    #     duration = note.get("duration", 1)
    #     dot = note.get("dot", False)
    #     line_length = NOTE_STEP * 0.9
    #     c.setLineWidth(1)

    #     # 中横线应位于歌词下方（lyric 相对 y - 22，再往下移动 6）
    #     line_y_base = y + LYRIC_OFFSET_Y - 6

    #     if duration == 2:
    #         c.line(x - line_length / 2, line_y_base, x + line_length / 2, line_y_base)
    #     elif duration == 4:
    #         c.line(x - line_length / 2, line_y_base + 2, x + line_length / 2, line_y_base + 2)
    #         c.line(x - line_length / 2, line_y_base - 2, x + line_length / 2, line_y_base - 2)
    #         if dot:
    #             c.line(x - line_length / 2, line_y_base, x + line_length / 2, line_y_base)

