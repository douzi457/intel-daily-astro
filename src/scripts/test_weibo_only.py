import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\Users\douzi457\.qclaw\workspace\情报系统")
from collect.collector import collect_weibo
r = collect_weibo()
print(f"微博: {len(r)}条")
if r:
    print(f"  第一条: {r[0]['title'][:60]}")
    print(f"  hot_value: {r[0]['hot_value']}")
