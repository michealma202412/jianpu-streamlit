# jianpu/renderer.py
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from jianpu.constants import *
from jianpu.symbols import get_pitch_symbol, get_ornament_symbol, get_dynamics_symbol
from reportlab.pdfbase.pdfmetrics import stringWidth

# 字体注册
pdfmetrics.registerFont(TTFont(FONT_LYRIC, FONT_PATH))

def dash_width():
    """返回一个 '-' 的实际渲染宽度"""
    return stringWidth("-", FONT_NOTE, FONT_SIZE_NOTE)

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

    # 🎵 中横线节奏辅助线（简谱风格专用）
    # === rhythm marker (节奏横线 / dash) ===
    duration = note.get("duration", 1)

    # ---------- ① 下横线（八分 & 十六分） ----------
    # if duration in (0.25, 0.5):
    #     # 线数：十六分 2 条，八分 1 条
    #     line_cnt = 2 if duration == 0.25 else 1
    #     line_len = FONT_SIZE_NOTE * 0.9          # 横线长度
    #     # 基准 y：数字底部稍下
    #     base_y = y - FONT_SIZE_NOTE * 0.20
    #     for i in range(line_cnt):
    #         offset = i * 2.5                     # 多条线垂直间距
    #         c.line(x - line_len/2, base_y - offset,
    #             x + line_len/2, base_y - offset)

    # ---------- ② 中横线 dash（二分 & 全音符） ----------
    if duration in (2, 3, 4):
        dash_cnt = int(duration) - 1
        dash_str = "-"
        # 1) 计算 dash 自身宽度
        dash_w = stringWidth(dash_str, FONT_NOTE, font_size)
        # 2) 计算数字本身宽度，保证 dash 紧贴数字
        pitch_symbol = get_pitch_symbol(pitch_num)
        symbol_w = stringWidth(pitch_symbol, FONT_NOTE, font_size)
        # 3) 起始 X：数字中心 + half_width + 少许 padding
        start_x = x + symbol_w/2 + 2
        # 4) 画 dash，每个 dash 之间留 2pt 微小间隔
        c.setFont(FONT_NOTE, font_size)
        for i in range(dash_cnt):
            c.drawString(start_x + i * (dash_w + 2), y, dash_str)

    # ---------- ③ 四分音符 duration==1: 无需标识 ----------
    # 不做任何处理