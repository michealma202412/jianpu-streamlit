# jianpu_web_ui.py
import streamlit as st
import json
import tempfile
import os
from jianpu.layout import draw_sheet
from jianpu.input_loader import txt_to_json
import re
import atexit
from jianpu.constants import KEY_SIGNATURES, TIME_SIGNATURES
import uuid

st.set_page_config(page_title="Jianpu Generator", layout="centered")

# 放在页面开头靠前位置
if "parsed_notes" not in st.session_state:
    st.session_state["parsed_notes"] = None
if "exported_txt" not in st.session_state:
    st.session_state["exported_txt"] = ""
st.title("🎼 简谱可视化生成器（支持 JSON / TXT）")

st.markdown("""
📌 功能说明：
- 上传 JSON 或粘贴 TXT 简谱内容（支持 pitch/lyric 行）
- 系统自动解析并生成标准 PDF，包含歌词、附点、连音线、节拍连接线、力度、装饰音、重复符号、休止符等
- 可直接下载排版结果 PDF 用于打印、投影或发布
""")

# --- 方式一：“简易序列输入”区块 ---
DURATIONS = [4, 3, 2, 1, 0.5, 0.25]  # 全音、附点二分、二分、四分、八分、十六分

st.markdown("### 📝 歌曲元信息")

# —— 折叠面板 + 一行多列 ——  
title      = st.session_state.get("meta_title", "")
key_sig    = st.session_state.get("meta_key",   list(KEY_SIGNATURES)[0])
time_sig   = st.session_state.get("meta_time",  list(TIME_SIGNATURES)[0])
tempo      = st.session_state.get("meta_tempo", None)
composer   = st.session_state.get("meta_composer", "")
lyricist   = st.session_state.get("meta_lyricist", "")
translator = st.session_state.get("meta_translator", "")
with st.expander("📝 歌曲元信息 (可选)", expanded=False):
    c1, c2, c3, c4 = st.columns([3,2,2,2])
    title    = c1.text_input("标题", placeholder="如：美好的时刻", key="meta_title")
    key_sig  = c2.selectbox("调式", options=list(KEY_SIGNATURES.keys()), index=0, key="meta_key")
    time_sig = c3.selectbox("拍号", options=list(TIME_SIGNATURES.keys()), index=0, key="meta_time")
    tempo    = c4.number_input("速度", placeholder="可选", min_value=1, max_value=300, value=80, step=1, key="meta_tempo")
    # 第二行小列
    c5, c6, c7 = st.columns([2,2,2])
    composer = c5.text_input("作曲", placeholder="可选", key="meta_composer")
    lyricist = c6.text_input("作词", placeholder="可选", key="meta_lyricist")
    translator = c7.text_input("翻译", placeholder="可选", key="meta_translator")

st.markdown("---")

st.markdown("## 🚀 按行输入（网格模式，可增加多行歌词）")

# 初始化
if "seq_rows" not in st.session_state:
    st.session_state["seq_rows"] = [
        {"id":uuid.uuid4().hex, "note_str":"", "lyrics": [], "cells":[]}
    ]

for row in st.session_state["seq_rows"]:
    rid = row["id"]
    header, delete_btn = st.columns([9,1])
    header.markdown(f"**第 {rid[:6]} 行**")
    if delete_btn.button("🗑 删除行", key=f"del_{rid}"):
        # 更新 session_state 后直接 continue
        st.session_state["seq_rows"] = [
            r for r in st.session_state["seq_rows"] if r["id"] != rid
        ]
        continue

    # 1) 原始序列输入
    row["note_str"]   = st.text_input("音符序列（空格分隔）", row["note_str"], key=f"ns_{rid}")
    # 2) 可增删的多行歌词
    for j, ly in enumerate(row["lyrics"]):
        row["lyrics"][j] = st.text_input(f"歌词行 {j+1}", ly, key=f"ly_{rid}_{j}")
    if st.button("➕ 添加歌词行", key=f"add_lyric_{rid}"):
        row["lyrics"].append("")
        continue

    st.markdown("---")

    # 3) 构造 grid
    pitches = row["note_str"].split()
    n = max(len(pitches), len(row["lyrics"]))
    key_cells = f"cells_{rid}"
    if key_cells not in st.session_state:
        st.session_state[key_cells] = [
            {"pitch":"", "lyrics":[""]*len(row["lyrics"]), "duration":1, "dot":False, "tie":False}
            for _ in range(n)
        ]
    cells = st.session_state[key_cells]
    # 扩容 / 裁剪
    if len(cells) < n:
        for _ in range(n-len(cells)):
            cells.append({"pitch":"", "lyrics":[""]*len(row["lyrics"]), "duration":1, "dot":False, "tie":False})
    else:
        st.session_state[key_cells] = cells = cells[:n]

    # 如果歌词行数变了，要同步每个 cell["lyrics"] 长度
    for cell in cells:
        if len(cell["lyrics"]) < len(row["lyrics"]):
            cell["lyrics"] += [""]*(len(row["lyrics"]) - len(cell["lyrics"]))
        elif len(cell["lyrics"]) > len(row["lyrics"]):
            cell["lyrics"] = cell["lyrics"][:len(row["lyrics"])]

    lyrics_tokens = [ly.strip().split() for ly in row["lyrics"]]
    # 遍历每个格子，把对应列的词填进去
    for i, cell in enumerate(cells):
        for j, tokens in enumerate(lyrics_tokens):
            # tokens[i] 如果越界就填空字符串
            cell["lyrics"][j] = tokens[i] if i < len(tokens) else ""


    # 渲染每一列格子
    for i in range(n):
        cols = st.columns([1, *([1]*len(row["lyrics"])), 1, 1, 1])
        k = 0
        # 音高
        cells[i]["pitch"] = cols[k].text_input(
            f"Pitch {i+1}", value=(pitches[i] if i < len(pitches) else ""), key=f"{rid}_p_{i}"
        ); k+=1
        # 多行歌词
        for j in range(len(row["lyrics"])):
            cells[i]["lyrics"][j] = cols[k].text_input(
                f"Lyric{j+1}", value=cells[i]["lyrics"][j], key=f"{rid}_l{j}_{i}"
            ); k+=1
        # 时值
        dur_idx = DURATIONS.index(cells[i]["duration"]) if cells[i]["duration"] in DURATIONS else 3
        cells[i]["duration"] = cols[k].selectbox(
            "Duration", options=DURATIONS, index=dur_idx, key=f"{rid}_d_{i}"
        ); k+=1
        # 附点
        cells[i]["dot"] = cols[k].checkbox("Dot", value=cells[i]["dot"], key=f"{rid}_dot_{i}"); k+=1
        # 连音
        cells[i]["tie"] = cols[k].checkbox("Tie", value=cells[i]["tie"], key=f"{rid}_tie_{i}")

    row["cells"] = cells
    st.markdown("—")

# 增加行
if st.button("➕ 添加音符行", key="add_row"):
    st.session_state["seq_rows"].append(
        {"id":uuid.uuid4().hex, "note_str":"", "lyrics":[], "cells":[]}
    )

txt_lines = []
# 解析并生成 TXT
if st.button("🔀 解析网格内容", key="parse_grid"):
    st.session_state.pop("parsed_notes", None)
    st.session_state.pop("exported_txt", None)
    all_tokens = []
    # —— metadata ——  
    if title:     all_tokens.append({"title": title})
    all_tokens.append({"key":    key_sig})
    all_tokens.append({"time":   time_sig})
    all_tokens.append({"tempo":  tempo or 0})
    if composer:  all_tokens.append({"composer":  composer})
    if lyricist:  all_tokens.append({"lyricist": lyricist})
    if translator:all_tokens.append({"translator":translator})
    # —— token body ——  
    for row in st.session_state["seq_rows"]:
        for cell in st.session_state[f"cells_{row['id']}"]:
            if not cell["pitch"]:
                continue
            tok = {
                "pitch":    int(cell["pitch"]),
                "duration": cell["duration"],
                # "lyric":    "|".join(cell["lyrics"])
            }
            # 多行歌词
            if len(cell["lyrics"]) > 1:
                tok["lyrics"] = cell["lyrics"]
            else:
                tok["lyric"]  = cell["lyrics"][0]

            if cell["dot"]: tok["dot"] = True
            if cell["tie"]: tok["tie"] = True
            all_tokens.append(tok)
        all_tokens.append({"bar": True})

    # 存入 session，供后续下载 TXT / 生成 PDF 使用
    st.session_state["parsed_notes"] = all_tokens


    # metadata
    if title:     txt_lines.append(f'title {title}')
    txt_lines.append(f'key {key_sig}')
    txt_lines.append(f'time {time_sig}')
    txt_lines.append(f'tempo {tempo or "-"}')
    if composer:  txt_lines.append(f'composer {composer}')
    if lyricist:  txt_lines.append(f'lyricist {lyricist}')
    if translator:txt_lines.append(f'translator {translator}')
    txt_lines.append("")  # 分隔

    for tok in st.session_state["parsed_notes"]:
        if tok.get("bar"):
            txt_lines.append("")     # 小节分隔空行
        elif "pitch" in tok:
            parts = [
                str(tok["pitch"]),
                str(tok["duration"]),
                tok.get("lyric", "")
            ]
            if tok.get("dot"):
                parts.append("dot")
            if tok.get("tie"):
                parts.append("tie")
            txt_lines.append(" ".join(parts))
        else:
            # 跳过 title/key/time 等元数据
            continue
    st.session_state["exported_txt"] = "\n".join(txt_lines)
    st.success("✅ 解析完成！现在可以下载 TXT 或生成 PDF。")

#  --- 方式二：粘贴或使用「方式一」生成的 TXT 格式 ---
st.markdown("📥 或直接粘贴简谱文本（两行格式：pitch + lyric）：")

txt_example = """key "G"
time "4/4"
tempo 80
repeat start
-3 1  低
1 1  中
9 1  高
5 1  附点, dot 
6 0.5  连 tie
6 0.5  音
0 1, rest   休
5 1  大 dynamics f ornament trill
6 1  声 dynamics p ornament mordent
repeat end
"""

# 优先使用方式一生成的 TXT
if txt_lines:
    txt_input = txt_lines
else:
    txt_input = st.text_area("🎹 简谱 TXT 格式", height=120, value=txt_example,key="txt_input_area")

if txt_input and st.button("🔍 解析简谱 TXT", key="btn_parse_txt"):
    try:
        json_notes = txt_to_json(txt_input)
        st.session_state["parsed_notes"] = json_notes
        st.success("✅ TXT 已转换并成功解析为简谱")
        st.json(json_notes[:5])

        # 直接提供 JSON 下载
        st.download_button(
            label="📥 下载解析后 JSON",
            data=json.dumps(json_notes, ensure_ascii=False, indent=2),
            file_name="jianpu_parsed.json",
            mime="application/json",
            key="download_json"
        )
    except Exception as e:
        st.error(f"❌ 解析失败: {e}")

# --- 方式三：上传 JSON ---
input_json = st.file_uploader("📤 上传 JSON 简谱配置文件（可选）", type="json")

if input_json:
    try:
        raw_notes = json.load(input_json)
        st.session_state["parsed_notes"] = raw_notes
        st.success("✅ JSON 简谱配置加载成功")
        st.json(raw_notes[:5])
    except Exception as e:
        st.error(f"❌ JSON 解析失败: {e}")

# --- 文件名与生成 ---
parsed_notes = st.session_state.get("parsed_notes", [])
exported_txt  = st.session_state.get("exported_txt", "")

if parsed_notes:
    # 只有 parse_grid 按过后，exported_txt 才非空
    if exported_txt:
        st.download_button(
            "📥 下载生成的 TXT 输入文件",
            data=exported_txt,
            file_name="jianpu_input.txt",
            mime="text/plain",
            key="download_txt"
        )

    # PDF 文件名输入
    filename = st.text_input("💾 输出 PDF 文件名：", value="jianpu_output.pdf")
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    if not filename.endswith(".pdf"):
        filename += ".pdf"

    if st.button("🎶 生成简谱 PDF", key="btn_gen_pdf"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            draw_sheet(parsed_notes, tmpfile.name)
            st.success("✅ 简谱 PDF 生成成功！")
            with open(tmpfile.name, "rb") as f:
                pdf_bytes = f.read()
                st.download_button(
                    "📥 下载 PDF 文件",
                    data=pdf_bytes,
                    file_name=filename,
                    key="download_pdf"
                )
            atexit.register(lambda: os.remove(tmpfile.name))
# --- 示例 JSON 展示 ---
if st.checkbox("📄 查看完整示例 JSON 格式（涵盖所有功能）"):
    example = [
        {"key": "G"},
        {"time": "4/4"},
        {"tempo": 80},
        #{"repeat": "start"},
        {"pitch": -3, "duration": 1, "lyric": "低"},
        {"pitch": 1, "duration": 1, "lyric": "中"},
        {"pitch": 9, "duration": 1, "lyric": "高"},
        {"pitch": 5, "duration": 1, "lyric": "附点", "dot": True},
        {"pitch": 6, "duration": 0.5, "lyric": "连", "tie": True, "beam": "a"},
        {"pitch": 6, "duration": 0.5, "lyric": "音", "beam": "a"},
        {"pitch": 0, "duration": 1, "rest": True, "lyric": "休"},
        {"pitch": 5, "duration": 1, "lyric": "大", "dynamics": "f", "ornament": "trill"},
        {"pitch": 6, "duration": 1, "lyric": "声", "dynamics": "p", "ornament": "mordent"},
        #{"repeat": "end"}
    ]
    st.code(json.dumps(example, indent=2, ensure_ascii=False), language="json")
