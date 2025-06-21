# jianpu/input_loader.py
from jianpu.constants import *
import shlex

def txt_to_json(txt: str):
    # """
    # 支持两类行：
    #   1) 元信息行：<key> <value>，如
    #      key G
    #      time 4/4
    #      tempo 80
    #      title "美好的时刻"
    #   2) 音符行：<pitch> <duration> <lyric...> [dot] [tie] [rest] [其他meta...]
    #      例：5 1 附点 dot
    #          6 0.5 连 tie
    # """
    lines = [line.strip() for line in txt.strip().splitlines() if line.strip()]
    result = []
    beat_counter = 0.0  # 拍子累加器，用于自动加 bar
    beats_per_bar = 4     # 默认每小节4拍，见 time: "4/4"

    for line in lines:
        parts = shlex.split(line)  # 支持用引号包 lyric
        if not parts:
            continue

        # —— 1. 元信息行 ——  
        field = parts[0].lower()
        if field in ("title","composer","lyricist","translator"):
            # 支持：title 美好的时刻  或  title "美好的 时刻"
            result.append({field: " ".join(parts[1:]).strip('"')})
            continue
        if field == "key":
            result.append({"key": parts[1]})
            continue
        if field == "time":
            v = parts[1]
            result.append({"time": v})
            try:
                beats_per_bar = int(v.split("/")[0])
            except:
                beats_per_bar = 4
            continue
        if field == "tempo":
            try:
                result.append({"tempo": int(parts[1])})
            except:
                result.append({"tempo": 0})
            continue
        if field == "repeat" and parts[1].lower() in ("start","end"):
            result.append({"repeat": parts[1].lower()})
            continue

        # —— 2. 音符行 ——  
        # 期望至少 pitch 和 duration 两列
        try:
            pitch = int(parts[0])
            duration = float(parts[1])
        except ValueError:
            # 不是元信息也不是音符行，跳过
            continue

        note = {"pitch": pitch, "duration": duration}
        # lyric 可能由多个 token 组成：取第 3 列开始，遇到 dot/tie/rest/dynamics/ornament 等关键字就算 flag
        flags = set(tok.lower() for tok in parts[2:] if tok.lower() in ("dot","tie","rest"))
        lyric_tokens = [tok for tok in parts[2:] if tok.lower() not in flags 
                        and not tok.lower() in DYNAMICS.keys()
                        and not tok.lower() in ORNAMENT_SYMBOLS.keys()]
        if lyric_tokens:
            raw = " ".join(lyric_tokens)
            note["lyric"] = raw
            # 优先按 | 切分
            if "|" in raw:
                note["lyric"] = [seg.strip() for seg in raw.split("|")]

        if "dot" in flags:
            note["dot"] = True
        if "tie" in flags:
            note["tie"] = True
        # rest 行可以显式写 rest，也可 pitch==0 自动识别
        if "rest" in flags or pitch == 0:
            note["rest"] = True

        # dynamics / ornament 仍可按原格式写在末尾，例如 f/trill
        for tok in parts[2:]:
            if tok.lower() in DYNAMICS:
                note["dynamics"] = tok.lower()
            if tok.lower() in ORNAMENT_SYMBOLS:
                note["ornament"] = tok.lower()

        # 拍子累加 & 自动加小节
        dur = duration * (1.5 if note.get("dot") else 1.0)
        beat_counter += dur
        result.append(note)
        if beat_counter >= beats_per_bar:
            result.append({"bar": True})
            beat_counter -= beats_per_bar

    return result
