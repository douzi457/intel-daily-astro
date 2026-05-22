import sys
sys.stdout.reconfigure(encoding='utf-8')

content = open(r"C:\Users\douzi457\.qclaw\workspace\情报系统\collect\collector.py", encoding='utf-8', errors='replace').read()
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'def run_py' in line or 'run_py(' in line:
        start = max(0, i-2)
        for j in range(start, min(i+15, len(lines))):
            print(f"{j+1}: {lines[j].rstrip()}")
        print("---")
