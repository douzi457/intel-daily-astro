import json
from pathlib import Path
from collections import Counter

data = json.load(open(r"C:\Users\douzi457\.qclaw\workspace\情报系统\intelligence_data.json", encoding="utf-8"))
items = data.get("items", [])

# 按来源统计
sources = Counter(item.get("source", "unknown") for item in items)
print("=" * 60)
print("📊 情报来源分布")
print("=" * 60)
for src, cnt in sources.most_common():
    print(f"  {src}: {cnt}条")

print()
print("=" * 60)
print("🔥 高频机会 (出现3次以上)")
print("=" * 60)
high_freq = [i for i in items if i.get("frequency", 1) >= 3]
for item in sorted(high_freq, key=lambda x: -x.get("score", 0))[:15]:
    print(f"\n[{item.get('source', '')}] {item.get('title', '')[:60]}")
    print(f"  分数:{item.get('score', 0)} | 出现:{item.get('frequency', 1)}次")

print()
print("=" * 60)
print("🛠️ 工具/开源项目 (GitHub)")
print("=" * 60)
github = [i for i in items if "github" in i.get("source", "").lower() or "GitHub" in i.get("title", "")]
for item in sorted(github, key=lambda x: -x.get("score", 0))[:10]:
    print(f"\n⭐ {item.get('title', '')[:70]}")
    print(f"  分数:{item.get('score', 0)} | {item.get('url', '')}")

print()
print("=" * 60)
print("💰 商业/赚钱相关")
print("=" * 60)
money_kw = ["变现", "赚钱", "副业", "收入", "创业", "商业", "GPT", "AI工具", "Token", "API"]
money_items = [i for i in items if any(kw in i.get("title", "") + i.get("desc", "") for kw in money_kw)]
for item in sorted(money_items, key=lambda x: -x.get("score", 0))[:10]:
    print(f"\n[{item.get('source', '')}] {item.get('title', '')[:60]}")
    print(f"  {item.get('desc', '')[:80]}")

print()
print("=" * 60)
print("📈 科技/投资趋势")
print("=" * 60)
trend_kw = ["英伟达", "英特尔", "芯片", "AI", "投资", "增持", "板块"]
trend = [i for i in items if any(kw in i.get("title", "") + i.get("desc", "") for kw in trend_kw)]
for item in sorted(trend, key=lambda x: -x.get("score", 0))[:10]:
    print(f"\n[{item.get('source', '')}] {item.get('title', '')[:60]}")
