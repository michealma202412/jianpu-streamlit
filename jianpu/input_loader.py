# jianpu/input_loader.py
import json
import streamlit as st
from jianpu.constants import *

def txt_to_json(txt: str):
    lines = [line.strip() for line in txt.strip().splitlines() if line.strip()]
    result = []
    beat_counter = 0.0  # 拍子累加器，用于自动加 bar
    beats_per_bar = 4     # 默认每小节4拍，见 time: "4/4"

    for line in lines:
        # 元信息行（如 key: G）
        if ":" in line and "pitch" not in line:
            try:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"')
                if k == "title":
                    # 解析歌曲标题
                    result.append({"title": v})
                    continue
                elif k == "time":
                    # 解析拍号 X/Y，取 X 作为每小节拍数
                    try:
                        beats_per_bar = int(v.split("/")[0])
                    except:
                        beats_per_bar = 4
                    result.append({k: v})
                    continue
                elif k == "tempo":
                    result.append({k: int(v)})
                    # 解析歌曲作者
                    result.append({"author": v})
                    continue
                else:
                    result.append({k: v})
            except Exception as e:
                print(f"⚠️ 无法解析元信息行: {line}")
            continue

        # 音符行
        if "pitch" in line:
            note = {}
            parts = line.split(",")
            for part in parts:
                if ":" not in part:
                    continue
                k, v = part.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"')

                # 类型判断
                if k == "pitch":
                    note[k] = int(v)
                elif k == "duration":
                    note[k] = float(v) if "." in v else int(v)
                elif k in ["dot", "tie", "rest"]:
                    note[k] = v.lower() == "true"
                else:
                    note[k] = v

            # 自动补全 rest:true
            if note.get("pitch") == 0 and "rest" not in note:
                note["rest"] = True

            # 更新拍子计数器
            note_duration = float(note.get("duration", 1))
            # # ✅ 若有附点，延长时值为原值 × 1.5
            if note.get("dot"):
                note_duration *= 1.5
                
            beat_counter += note_duration
            result.append(note)

            # 判断是否自动插入 bar
            # beats_per_bar 从前面解析 time: "X/Y" 得到 X
            if beat_counter >= beats_per_bar:
                result.append({"bar":True})
                beat_counter -= beats_per_bar

    return result
