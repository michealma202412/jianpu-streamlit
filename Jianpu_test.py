# 执行环境重置，重新创建测试样本 JSON 文件夹和自动测试脚本

import os
import json

# 测试样本目录结构
base_dir = "jianpu_tests"
tests_dir = os.path.join(base_dir, "tests")
output_dir = os.path.join(base_dir, "out")

os.makedirs(tests_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

# 测试用例定义
test_cases = {
    "test_tie_beam.json": [
        {"pitch": 1, "duration": 1, "lyric": "在", "dot": True},
        {"pitch": 6, "duration": 0.5, "lyric": "一", "tie": True, "beam": "a"},
        {"pitch": 6, "duration": 0.5, "lyric": "起", "beam": "a"},
        {"pitch": 5, "duration": 1, "lyric": "，"},
        {"pitch": 3, "duration": 1, "lyric": "敬"}
    ],
    "test_octave.json": [
        {"pitch": -3, "duration": 1, "lyric": "低"},
        {"pitch": 1, "duration": 1, "lyric": "中"},
        {"pitch": 9, "duration": 1, "lyric": "高"}
    ],
    "test_symbols.json": [
        {"pitch": 5, "duration": 1, "lyric": "大", "dynamics": "f", "ornament": "trill"},
        {"pitch": 6, "duration": 1, "lyric": "声", "dynamics": "p", "ornament": "mordent"}
    ],
    "test_meta.json": [
        {"key": "G"},
        {"time": "3/4"},
        {"tempo": 100},
        {"pitch": 1, "duration": 1, "lyric": "调"},
        {"pitch": 2, "duration": 1, "lyric": "拍"},
        {"pitch": 3, "duration": 1, "lyric": "速"}
    ],
    "test_repeat_rest.json": [
        {"repeat": "start"},
        {"pitch": 1, "duration": 1, "lyric": "重"},
        {"pitch": 2, "duration": 1, "lyric": "复"},
        {"repeat": "end"},
        {"pitch": 0, "duration": 1, "rest": True, "lyric": "休"}
    ]
}

# 写入 JSON 文件
for filename, content in test_cases.items():
    with open(os.path.join(tests_dir, filename), "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

# 自动测试执行脚本内容
runner_script = f"""#!/usr/bin/env python3
import os
import subprocess

tests = {list(test_cases.keys())}
base = "{base_dir}"
for test in tests:
    input_path = os.path.join(base, "tests", test)
    output_path = os.path.join(base, "out", test.replace(".json", ".pdf"))
    cmd = f"python main.py --input '{{input_path}}' --output '{{output_path}}'"
    print(f"Running: {{cmd}}")
    subprocess.run(cmd, shell=True)
"""

# 写入 run_all_tests.py
runner_path = os.path.join(base_dir, "run_all_tests.py")
with open(runner_path, "w", encoding="utf-8") as f:
    f.write(runner_script)

base_dir
