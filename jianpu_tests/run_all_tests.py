#!/usr/bin/env python3
import os
import subprocess

tests = ['test_tie_beam.json', 'test_octave.json', 'test_symbols.json', 'test_meta.json', 'test_repeat_rest.json']
base = "jianpu_tests"
for test in tests:
    input_path = os.path.join(base, "tests", test)
    output_path = os.path.join(base, "out", test.replace(".json", ".pdf"))
    cmd = f"python main.py --input '{input_path}' --output '{output_path}'"
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True)
