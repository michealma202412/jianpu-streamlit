# jianpu/cli.py
import argparse
from jianpu.input_loader import load_notes_from_json
from jianpu.layout import draw_sheet

def run_cli():
    parser = argparse.ArgumentParser(description="简谱生成器 CLI")
    parser.add_argument("--input",default="美好的时刻_notes.json", help="输入 JSON 文件")
    parser.add_argument("--output", default="美好的时刻.pdf", help="输出 PDF 文件")
    #parser.add_argument("--input",default=r"jianpu_tests\tests\test_tie_beam.json", help="输入 JSON 文件")
    #parser.add_argument("--input",default=r"jianpu_tests\tests\test_octave.json", help="输入 JSON 文件")
    #parser.add_argument("--input",default=r"jianpu_tests\tests\test_symbols.json", help="输入 JSON 文件")
    #parser.add_argument("--input",default=r"jianpu_tests\tests\test_meta.json", help="输入 JSON 文件")
    #parser.add_argument("--input",default="jianpu_tests\\tests\\test_repeat_rest.json", help="输入 JSON 文件")
    #parser.add_argument("--output", default="jianpu_tests\\out\\test_meta.pdf", help="输出 PDF 文件")
    args = parser.parse_args()
    notes = load_notes_from_json(args.input)
    draw_sheet(notes, args.output)
