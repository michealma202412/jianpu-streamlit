# jianpu/constants.py
TITLE = "\u300a\u7f8e\u597d\u7684\u65f6\u523b\u300b\u7b80\u8c03\u6392\u7248\u793a\u4f8b"
FONT_NOTE = "Helvetica-Bold"
FONT_LYRIC = "Chinese"
FONT_PATH = "方正粗黑宋简体.ttf"

from reportlab.lib.pagesizes import A4
PAGE_SIZE = A4
PAGE_WIDTH, PAGE_HEIGHT = A4

# ========================
# 🎨 全局样式与排版参数（含注释说明）
# ========================

FONT_SIZE_NOTE = 16        # 音符数字的字号（建议 14~18）
FONT_SIZE_LYRIC = 14       # 歌词的字号（建议比音符略小）

NOTE_STEP = 40             # 每个音符之间的水平间距（点数）
LINE_HEIGHT = 50           # 每行简谱之间的垂直间距（点数）

TOP_MARGIN = 50            # 页面顶部边距（点数）
LEFT_MARGIN = 60           # 页面左边距
RIGHT_MARGIN = 60          # 页面右边距

START_Y_OFFSET = 120       # 简谱内容起始 Y 坐标与页顶之间的距离（越大简谱越下）

LYRIC_OFFSET_Y = -22       # 歌词相对于音符中心点的垂直偏移（负值表示下方）

DOT_RADIUS = 1.5
DOT_OFFSET_X_RATIO = 0.5
DOT_OFFSET_Y_RATIO = 0.35   # 附点（节奏点）相对字体高度的垂直偏移比例
                           # 实际偏移 = FONT_SIZE_NOTE * 该比例
               

TIE_ARC_HEIGHT = 12        # 连音线弧形的垂直高度（越大越弯）
TIE_ARC_BASE = 5           # 连音线与音符中心点之间的起始高度偏移

BEAM_LINE_OFFSET = 24      # 节拍连接横线（beam）距离音符中心的垂直偏移（负值表示下方）


HIGH_DOT_X_OFFSET = -1.5   # 高音点（上点）相对于音符的左右偏移（负值偏左）
HIGH_DOT_Y_OFFSET_RATIO = 1  # 高音点垂直偏移比例（相对字号）
LOW_DOT_Y_OFFSET_RATIO = 0.25    # 低音点垂直偏移比例（相对字号）

META_Y = PAGE_HEIGHT - 80  # 元信息（调式、节拍、速度）显示位置 Y 坐标（接近页顶）


# 增加节奏时值比例映射（相对单位）
# duration 值含义：
# 4: 四分音符，2: 二分音符，1: 全音符，0.5: 八分音符，0.25: 十六分音符
DURATION_WIDTH_MAP = {
    4: NOTE_STEP * 4,    # 四分音符延长宽度
    2: NOTE_STEP * 2,
    1: NOTE_STEP,
    0.5: NOTE_STEP / 2,
    0.25: NOTE_STEP / 4
}

# 增加节奏标记样式支持（用于未来绘制节奏符号）
RHYTHM_STYLE = {
    1: "quarter",
    0.5: "eighth",
    0.25: "sixteenth",
    2: "half",
    4: "whole"
}

KEY_SIGNATURES = {
    "C": [], "G": ["F#"], "D": ["F#", "C#"],
    "F": ["Bb"], "Bb": ["Bb", "Eb"], "Am": [], "Em": ["F#"],
}

TIME_SIGNATURES = {
    "4/4": (4, 4),
    "3/4": (3, 4),
    "6/8": (6, 8),
}

DYNAMICS = {
    "pp": "𝆏", "p": "𝆐", "mp": "𝆑", "mf": "𝆒", "f": "𝆓", "ff": "𝆔"
}

ORNAMENT_SYMBOLS = {
    "trill": "𝆗", "mordent": "𝆘", "turn": "𝆙"
}

REPEAT_SYMBOLS = {
    "start": "𝄆", "end": "𝄇"
}