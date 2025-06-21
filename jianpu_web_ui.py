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
- 粘贴 TXT 简谱内容
- 系统自动解析并生成标准 PDF，包含歌词、附点、连音线、节拍连接线、力度、装饰音、重复符号、休止符等
- 可直接下载排版结果 PDF 用于打印、投影或发布
""")

#  --- 方式二：粘贴或使用「方式一」生成的 TXT 格式 ---
st.markdown("📥 直接粘贴简谱文本（格式：pitch duration lyric dot tie ）：")

txt_example = """title 名称
key "G"
time "4/4"
tempo 80
lyricist -
translator -
composer -
repeat start
-3 1  低|低
1 1  中|中
9 1  高|高
5 1  附点,|附点, dot 
6 0.5  连 tie
6 0.5  音
0 1, rest   休
5 1  大
6 1  声
repeat end
"""

txt_input = st.text_area("🎹 简谱 TXT 格式", height=120, value=txt_example,key="txt_input_area")
if txt_input and st.button("🔍 解析简谱 TXT", key="btn_parse_txt"):
    try:
        json_notes = txt_to_json(txt_input)
        st.session_state["parsed_notes"] = json_notes
        st.success("✅ TXT 已转换并成功解析为简谱")
        st.json(json_notes[:])

        # # 直接提供 JSON 下载
        # st.download_button(
        #     label="📥 下载解析后 JSON",
        #     data=json.dumps(json_notes, ensure_ascii=False, indent=2),
        #     file_name="jianpu_parsed.json",
        #     mime="application/json",
        #     key="download_json"
        # )
    except Exception as e:
        st.error(f"❌ 解析失败: {e}")

# # --- 方式三：上传 JSON ---
# input_json = st.file_uploader("📤 上传 JSON 简谱配置文件（可选）", type="json")

# if input_json:
#     try:
#         raw_notes = json.load(input_json)
#         st.session_state["parsed_notes"] = raw_notes
#         st.success("✅ JSON 简谱配置加载成功")
#         st.json(raw_notes[:5])
#     except Exception as e:
#         st.error(f"❌ JSON 解析失败: {e}")

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
