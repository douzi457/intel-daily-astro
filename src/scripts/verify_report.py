import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3, html

conn = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")
c = conn.cursor()
today = '2026-05-20'

# 各平台URL情况
rows = c.execute(f"""
    SELECT original_source,
           COUNT(*) as total,
           SUM(CASE WHEN url IS NULL OR url = '' THEN 1 ELSE 0 END) as no_url
    FROM items
    WHERE DATE(created_at) = ?
    GROUP BY original_source
    ORDER BY total DESC
""", (today,)).fetchall()

print(f"=== 今日({today})数据概况 ===")
total_all, total_url = 0, 0
for o, tot, no in rows:
    print(f"  {o:<22} {tot:>3}条  {'⚠️'+str(no) if no else '✅':<8} 无链接")
    total_all += tot
    total_url += no
print(f"  {'合计':<22} {total_all:>3}条  {total_url}条无链接")
print()

# 今日头条：看9条有URL的样本
tt_with_url = c.execute("SELECT title, url FROM items WHERE DATE(created_at)=? AND original_source='toutiao' AND url != '' LIMIT 3", (today,)).fetchall()
print("今日头条有URL的样本:")
for t, u in tt_with_url:
    print(f"  [{u}]\n    {t[:50]}")
