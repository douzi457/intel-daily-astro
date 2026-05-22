import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3

conn = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")
c = conn.cursor()

# 昨天今日头条的URL情况
yesterday = '2026-05-19'
y_tt = c.execute("SELECT COUNT(*) FROM items WHERE DATE(created_at)=? AND original_source='toutiao'", (yesterday,)).fetchone()[0]
y_tt_url = c.execute("SELECT COUNT(*) FROM items WHERE DATE(created_at)=? AND original_source='toutiao' AND url != ''", (yesterday,)).fetchone()[0]
print(f"昨天(05-19)今日头条: {y_tt}条, 有URL: {y_tt_url}条")

# 今天的
today = '2026-05-20'
t_tt = c.execute("SELECT COUNT(*) FROM items WHERE DATE(created_at)=? AND original_source='toutiao'", (today,)).fetchone()[0]
t_tt_url = c.execute("SELECT COUNT(*) FROM items WHERE DATE(created_at)=? AND original_source='toutiao' AND url != ''", (today,)).fetchone()[0]
print(f"今天(05-20)今日头条: {t_tt}条, 有URL: {t_tt_url}条")

# 查看昨天有URL的头条
print("\n昨天有URL的头条样本:")
rows = c.execute("SELECT title, url FROM items WHERE DATE(created_at)=? AND original_source='toutiao' AND url != '' LIMIT 5", (yesterday,)).fetchall()
for title, url in rows:
    print(f"  [{url[:70]}] {title[:40]}")
