# 🎵 Python 简谱生成系统（Jianpu Renderer）

本项目是一个基于 Python 和 ReportLab 的简谱排版系统，支持生成带歌词、节拍、力度、连音等要素的简谱 PDF。适合用于诗歌、圣诗、音乐教学等场景。

---

## 📁 项目目录结构

```
your_project/
├── main.py                 # 启动入口
├── jianpu/
│   ├── cli.py             # 命令行入口
│   ├── constants.py       # 所有全局样式与符号定义
│   ├── input_loader.py    # 加载 JSON 输入文件
│   ├── layout.py          # 简谱整体排版与绘制控制
│   ├── renderer.py        # 单个音符绘制（数字、歌词、附点、装饰音等）
│   └── symbols.py         # 音符、力度、装饰音等符号映射
└── 美好的时刻_notes.json   # 示例输入 JSON
```

---

## 🚀 使用方法

### ✅ 方式 1：命令行运行

```bash
python main.py --input 美好的时刻_notes.json --output output.pdf
python -m streamlit run jianpu_web_ui.py
```

### ✅ 方式 2：在 IDE 中运行（如 VSCode / Spyder）

运行 `main.py` 即可自动处理默认输入/输出路径。

---

## 📝 输入文件格式说明（JSON）

每首曲子以 JSON 数组形式输入：

### ✅ 基础字段说明

| 字段       | 类型    | 说明                                     |
|------------|---------|------------------------------------------|
| `pitch`    | int     | 音高。0 = 休止符，1~7 = 中音，8+ = 高音，负数 = 低音 |
| `duration` | float   | 音长。1=四分音符，0.5=八分，2=二分等      |
| `lyric`    | str     | 对应歌词文字                             |
| `dot`      | bool    | 是否附点（节奏点）                        |
| `tie`      | bool    | 是否为连音起点                           |
| `beam`     | str     | 同组节拍连接 ID（如 "a", "b"）             |
| `dynamics` | str     | 力度：pp/p/mp/mf/f/ff                     |
| `ornament` | str     | 装饰音：trill/mordent/turn                |
| `rest`     | bool    | 是否为休止符                             |
| `accent`   | bool    | 是否为强音                               |
| `is_grace` | bool    | 是否为倚音                               |
| `repeat`   | str     | 重复记号："start" 或 "end"               |

### ✅ 元信息字段

```json
[
  {"key": "G"},
  {"time": "4/4"},
  {"tempo": 80},
  ...
]
```

---

## 📄 输出效果支持

- ✅ 简谱数字（1~7）、高低音点
- ✅ 附点、歌词对齐
- ✅ 连音线（tie）、节拍连接线（beam）
- ✅ 力度符号（𝆐~𝆔）、装饰音（𝆗~𝆙）
- ✅ 休止符（𝄽）、重复符号（𝄆𝄇）
- ✅ 标题、调号、拍号、速度显示
- ✅ 多页自动换行排版

---

## 🧪 测试方案

你可以使用：

```bash
python jianpu_tests/run_all_tests.py
```

自动测试以下功能：

- `test_tie_beam.json`: 连音与节拍线
- `test_octave.json`: 高低音点位置
- `test_symbols.json`: 力度与装饰音
- `test_meta.json`: 调号拍号节奏
- `test_repeat_rest.json`: 重复记号与休止符

---

## 🛠 调整与定制

所有布局和样式参数统一在：

```python
jianpu/constants.py
```

中集中设置，包括：

- 字体大小、边距
- 行间距、附点位置
- 连音弧线、歌词偏移
- 节奏宽度映射

---

## 📌 拓展建议

| 功能              | 状态 | 说明                     |
|-------------------|------|--------------------------|
| 多声部            | 🚧    | 可通过分层实现            |
| Key 图形显示       | 🚧    | 支持调号五线谱位置辅助符号 |
| MIDI → 简谱解析    | 🚧    | 可结合 MIDI 库开发         |
| Web 可视化排版界面 | 🚧    | Flask/Streamlit 可搭建交互系统 |

---

## 📬 联系与贡献

欢迎反馈建议或提交 PR！此项目致力于构建现代化的中文简谱渲染工具，适用于诗歌/教育/研究等场景。
