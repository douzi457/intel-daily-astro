import os, sys
sys.stdout.reconfigure(encoding='utf-8')
day_dir = r"C:\Users\douzi457\.qclaw\workspace\情报系统\output\day"
files = sorted(os.listdir(day_dir), reverse=True)[:5]
print('\n'.join(files))
