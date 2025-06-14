# jianpu/symbols.py
from jianpu.constants import DYNAMICS
from jianpu.constants import ORNAMENT_SYMBOLS
# 音高：支持 低音/中音/高音 各7个（范围可根据需要扩展）
pitch_map = {
    -7: "7", -6: "6", -5: "5", -4: "4", -3: "3", -2: "2", -1: "1",  # 低音区
     0: "0",  # 休止符
     1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7",        # 中音区
     8: "1", 9: "2", 10: "3", 11: "4", 12: "5", 13: "6", 14: "7"    # 高音区
}

# 升降音符号（可用于未来音高标注，如调式或半音）
accidentals = {
    "sharp": "♯",     # 升音
    "flat": "♭",      # 降音
    "natural": "♮",   # 还原
}

# 节拍时值定义（用于可视化支持或节拍分析）
duration_map = {
    0.25: "十六分音符",
    0.5: "八分音符",
    1: "四分音符",
    1.5: "附点四分音符",
    2: "二分音符",
    3: "附点二分音符",
    4: "全音符"
}

def get_pitch_symbol(pitch: int, accidental: str = None):
    """
    获取音高符号
    :param pitch: 整数音高（支持低/中/高八度）
    :param accidental: 可选的升/降符号
    :return: 字符串表示音符，如 '♯5'、'1•'
    """
    base = pitch_map.get(pitch, "")
    if not base:
        return ""

    acc = accidentals.get(accidental, "") if accidental else ""
    return acc + base

def get_dynamics_symbol(level: str):
    return DYNAMICS.get(level, "")

def get_ornament_symbol(kind: str):
    return ORNAMENT_SYMBOLS.get(kind, "")
