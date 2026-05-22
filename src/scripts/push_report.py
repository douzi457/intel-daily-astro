import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3

conn = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")
c = conn.cursor()
today = '2026-05-20'

# 按平台均衡抽取：每个平台最多2条，确保多样性
rows = c.execute("""
    SELECT title, url, original_source, hot_value
    FROM items
    WHERE DATE(created_at) = ? AND title != ''
    ORDER BY original_source,
             CASE WHEN hot_value IS NOT NULL AND hot_value != '' THEN CAST(hot_value AS INTEGER) ELSE 0 END DESC
""", (today,)).fetchall()

# 按平台分组，每组取前2
from collections import defaultdict
by_src = defaultdict(list)
for title, url, src, hv in rows:
    by_src[src].append((title, url, hv, src))

selected = []
for src in by_src:
    selected.extend(by_src[src][:2])

# 取前16条
selected = selected[:16]

# 各平台条数
platforms = c.execute("""
    SELECT original_source, COUNT(*) as cnt
    FROM items WHERE DATE(created_at) = ?
    GROUP BY original_source ORDER BY cnt DESC
""", (today,)).fetchall()

msg = f"📡 情报日报 {today}\n"
msg += f"共 {sum(p[1] for p in platforms)} 条 | {len(platforms)} 个平台\n"
msg += f"今日头条/抖音 URL已修复✅\n\n"

msg += "🔥 今日热点（前16条）\n"
for i, (title, url, hv, src) in enumerate(selected, 1):
    short_src = (url.split('/')[2] if url and url.startswith('http') else '').replace('www.','').replace('com','').replace('cn','')[:10]
    if not short_src:
        short_src = (src or '')[:10]
    display_title = title[:36] + '…' if len(title) > 36 else title
    msg += f"{i}. {display_title}\n"
    if url and url.startswith('http'):
        msg += f"   🔗 {url[:55]}\n"
    else:
        msg += f"   🔗 {url or '(无链接)'}\n"

msg += f"\n📊 平台分布\n"
for name, cnt in platforms[:10]:
    short = (name or '?')[:16]
    msg += f"  {short:<16} {cnt}条\n"

print(msg)
