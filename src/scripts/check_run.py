import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

root = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")

# 查看 run.py 内容
run_py = root / "run.py"
if run_py.exists():
    content = run_py.read_text(encoding='utf-8')
    print("=== run.py 内容（前30行）===")
    for i, line in enumerate(content.split('\n')[:30], 1):
        print(f"  {i:2d}: {line.rstrip()}")

# 查看 root collector.py 里 collect_douyin 函数
col_root = root / "collector.py"
if col_root.exists():
    content = col_root.read_text(encoding='utf-8')
    for i, line in enumerate(content.split('\n'), 1):
        if 'link' in line.lower() or 'def collect_douyin' in line:
            print(f"  collector.py:{i}: {line.rstrip()}")

# 查看 collect/collector.py
col_collect = root / "collect" / "collector.py"
if col_collect.exists():
    content = col_collect.read_text(encoding='utf-8')
    for i, line in enumerate(content.split('\n'), 1):
        if 'link' in line.lower() or 'def collect_douyin' in line:
            print(f"  collect/collector.py:{i}: {line.rstrip()}")
