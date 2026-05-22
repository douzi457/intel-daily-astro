import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from datetime import datetime

root = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")

print("=== 关键文件最后修改时间 ===")
key_files = [
    root / "collector.py",
    root / "run.py",
    root / "gen_report2.py",
    root / "collect" / "collector.py",
    root / "collect" / "collector_reddit.py",
]
for f in sorted(set(key_files)):
    if f.exists():
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        rel = str(f.relative_to(root))
        print(f"  {rel:<35} {mtime.strftime('%m-%d %H:%M')}")
    else:
        rel = str(f.relative_to(root))
        print(f"  {rel:<35} 不存在")

print("\n=== cron jobs 检查 ===")
oc_jobs = Path(r"C:\Users\douzi457\.qclaw\jobs.json")
if oc_jobs.exists():
    import json
    jobs = json.loads(oc_jobs.read_text(encoding='utf-8'))
    intel_jobs = [j for j in jobs if '情报' in j.get('name','') or 'intell' in j.get('name','').lower()]
    print(f"  openclaw jobs.json: 存在，共{len(jobs)}个任务")
    for j in intel_jobs:
        print(f"    {j.get('name')} | {j.get('schedule')} | {j.get('state')}")
else:
    print("  openclaw jobs.json: 不存在")
