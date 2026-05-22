"""
测试：gzh 脚本把文件写到哪个目录？
"""
import subprocess, sys, json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
skill = Path(r"C:\Users\douzi457\.qclaw\workspace\skills\gzh-explosive-content-detector\scripts\fetch_gzh_trends.py")
cwd = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")

r = subprocess.run(
    [sys.executable, str(skill), "--keyword", "副业", "--max-items", "3", "--output-format", "json"],
    capture_output=True, text=True, cwd=str(cwd)
)
print("RC:", r.returncode)
print("STDERR:", r.stderr[:300] if r.stderr else "(empty)")

# 搜索生成的 json 文件
for f in cwd.glob("*爆款数据.json"):
    print(f"找到文件: {f.name} ({f.stat().st_size} bytes)")
    data = json.loads(f.read_text(encoding='utf-8'))
    print(f"  条目数: {len(data) if isinstance(data, list) else '?'}")
    if isinstance(data, list) and data:
        print(f"  第一条: {data[0].get('title','')[:50]}")
