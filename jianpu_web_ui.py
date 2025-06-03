# jianpu_web_ui.py
import streamlit as st
import json
import tempfile
import os
from jianpu.layout import draw_sheet
from jianpu.input_loader import txt_to_json
import re
import atexit

# 放在页面开头靠前位置
if "parsed_notes" not in st.session_state:
    st.session_state["parsed_notes"] = None

notes = st.session_state.get("parsed_notes")
st.set_page_config(page_title="Jianpu Generator", layout="centered")
st.title("🎼 简谱可视化生成器（支持 JSON / TXT）")

st.markdown("""
📌 功能说明：
- 上传 JSON 或粘贴 TXT 简谱内容（支持 pitch/lyric 行）
- 系统自动解析并生成标准 PDF，包含歌词、附点、连音线、节拍连接线、力度、装饰音、重复符号、休止符等
- 可直接下载排版结果 PDF 用于打印、投影或发布
""")

# --- 方式一：粘贴 TXT 格式 ---
st.markdown("📥 或直接粘贴简谱文本（两行格式：pitch + lyric）：")

txt_example = """key: "G"
time: "4/4"
tempo: 80
repeat: "start"
pitch: -3, duration: 1, lyric: "低"
pitch: 1, duration: 1, lyric: "中"
pitch: 9, duration: 1, lyric: "高"
pitch: 5, duration: 1, lyric: "附点", dot: True
pitch: 6, duration: 0.5, lyric: "连", tie: True, beam: "a"
pitch: 6, duration: 0.5, lyric: "音", beam: "a"
pitch: 0, duration: 1, rest: True, lyric: "休"
pitch: 5, duration: 1, lyric: "大", dynamics: "f", ornament: "trill"
pitch: 6, duration: 1, lyric: "声", dynamics: "p", ornament: "mordent"
repeat: "end"
"""

txt_input = st.text_area("🎹 简谱 TXT 格式", height=120, value=txt_example)

if txt_input and st.button("🔍 解析简谱 TXT"):
    try:
        json_notes = txt_to_json(txt_input)
        notes = json_notes
        if json_notes:
            with open("Input.json", "w", encoding="utf-8") as f:
                json.dump(json_notes, f, ensure_ascii=False, indent=2)
        st.session_state["parsed_notes"] = notes
        st.success("✅ TXT 已转换并成功解析为简谱")
        st.json(notes[:5])
    except Exception as e:
        st.error(f"❌ 解析失败: {e}")

# --- 方式二：上传 JSON ---
input_json = st.file_uploader("📤 上传 JSON 简谱配置文件（可选）", type="json")

if input_json:
    try:
        raw_notes = json.load(input_json)
        notes = raw_notes
        st.session_state["parsed_notes"] = notes
        st.success("✅ JSON 简谱配置加载成功")
        st.json(notes[:5])
    except Exception as e:
        st.error(f"❌ JSON 文件解析失败: {e}")

# --- 文件名与生成 ---
notes = st.session_state.get("parsed_notes")
if notes:
    filename = st.text_input("💾 输出 PDF 文件名：", value="jianpu_output.pdf")
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    if not filename.endswith(".pdf"):
        filename += ".pdf"
    if st.button("🎶 生成简谱 PDF"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            draw_sheet(notes, tmpfile.name)
            st.success("✅ 简谱 PDF 生成成功！")
            with open(tmpfile.name, "rb") as f:
                pdf_bytes = f.read()
                st.download_button("📥 下载 PDF 文件", data=pdf_bytes, file_name=filename)

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
