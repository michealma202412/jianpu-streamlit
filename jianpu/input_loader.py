# jianpu/input_loader.py
import json
import streamlit as st

def txt_to_json(txt: str):
    lines = [line.strip() for line in txt.strip().splitlines() if line.strip()]
    result = []

    for line in lines:
        if line.startswith("pitch:"):
            # 音符行
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
            result.append(note)
        else:
            # 非音符行（如 key, time, tempo, repeat 等）
            try:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip('，').strip(',')  # 去掉中英文逗号
                if k == "tempo":
                    result.append({k: int(v)})
                else:
                    result.append({k: v})
            except Exception as e:
                print(f"⚠️ 无法解析元信息行: {line}")
                continue

    return result
