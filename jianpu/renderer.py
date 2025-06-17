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
    has_one_dash = note.get("duration", 1) == 0.5
    has_two_dash = note.get("duration", 1) == 0.25

    if octave == 1:
        c.circle(x, y + FONT_SIZE_NOTE * HIGH_DOT_Y_OFFSET_RATIO, DOT_RADIUS, fill=1)
    elif octave == -1:
        dot_y = y
        if has_one_dash:
            dot_y = y - FONT_SIZE_NOTE * LOW_DOT_Y_OFFSET_RATIO
        elif has_two_dash:
            dot_y = y - FONT_SIZE_NOTE * LOW_DOT_Y_OFFSET_RATIO * 1.5
        else:
            dot_y = y - FONT_SIZE_NOTE * LOW_DOT_Y_OFFSET_RATIO * 0.5
        c.circle(x, dot_y, DOT_RADIUS, fill=1)

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

    # 歌词：支持单行或多行（字符串里的 '\n' 或 list）
    raw = note.get("lyric") or note.get("lyrics")
    if raw is not None:
        # 先把 "\\n" 形式也替换
        text = raw.replace("\\\\n", "\n") if isinstance(raw, str) else raw
        if isinstance(text, (list, tuple)):
            lines = [str(l) for l in text]
        else:
            lines = str(text).split("\n")
        c.setFont(FONT_LYRIC, FONT_SIZE_LYRIC)
        for i, ln in enumerate(lines):
            # 第一行用原偏移，后续行依次再往下
            dy = LYRIC_OFFSET_Y - i * (FONT_SIZE_LYRIC + 2)
            c.drawCentredString(x, y + dy, ln)
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
    if duration in (0.25, 0.5):
        # 线数：十六分 2 条，八分 1 条
        line_cnt = 2 if duration == 0.25 else 1
        line_len = FONT_SIZE_NOTE * 0.7          # 横线长度
        # 基准 y：数字底部稍下
        base_y = y - BEAM_LINE_OFFSET
        for i in range(line_cnt):
            offset = i * BEAM_LINE_OFFSET                     # 多条线垂直间距
            c.line(x - line_len/2, base_y - offset,
                x + line_len/2, base_y - offset)

    # ---------- ② 中横线 dash（二分 & 全音符） ----------
    elif duration in (2, 3, 4):
        dash_cnt = int(duration) - 1
        # 计算数字宽度，用来偏移横线起点
        pitch_symbol = get_pitch_symbol(pitch_num)
        symbol_w = stringWidth(pitch_symbol, FONT_NOTE, font_size)
        # 从数字右侧稍微偏移
        start_x = x + symbol_w/2 + 2
        # 横线总长（每个 dash 同 NOTE_DASH_OFFSET），间隔 gap
        dash_len = NOTE_DASH_OFFSET
        gap = NOTE_STEP/3
        # 纵向居中：在 note 中心 (y)
        dash_y = y + FONT_SIZE_NOTE * DOT_OFFSET_Y_RATIO


        c.setLineWidth(1.2)
        for i in range(dash_cnt):
            seg_x = start_x + i * (dash_len + gap)
            c.line(seg_x, dash_y, seg_x + dash_len, dash_y)
    # ---------- ③ 四分音符 duration==1: 无需标识 ----------
    # 不做任何处理
