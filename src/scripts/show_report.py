import json
from pathlib import Path

data = json.load(open(r"C:\Users\douzi457\.qclaw\workspace\情报系统\intelligence_data.json", encoding="utf-8"))
items = data.get("items", [])

print("=" * 50)
print("📡 今日情报汇总 (2026-05-17)")
print("=" * 50)
print(f"总数据: {len(items)} 条")
print()

for i, item in enumerate(items[:15], 1):
    title = item.get("title", "")[:50]
    source = item.get("source", "")
    score = item.get("score", 0)
    freq = item.get("frequency", 1)
    print(f"{i}. [{source}] {title}")
    print(f"   分数:{score} | 出现:{freq}次")
    print()
