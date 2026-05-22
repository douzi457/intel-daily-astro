import subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
r = subprocess.run(
    [sys.executable, r"C:\Users\douzi457\.qclaw\workspace\skills\weibo-trending\scripts\fetch-hot-search.py"],
    capture_output=True, text=True, timeout=30, cwd=r"C:\Users\douzi457\.qclaw\workspace\skills\weibo-trending"
)
print("RC:", r.returncode)
print("STDERR:", r.stderr[-1000:])
