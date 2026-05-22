import sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

db_path = r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

today = '2026-05-19'

# 全部条数
total = c.execute("SELECT COUNT(*) FROM items").fetchone()[0]
print(f"总条数: {total}")

# 今天日期格式
rows = c.execute("SELECT created_at FROM items LIMIT 3").fetchall()
print(f"created_at样本: {rows}")

# DATE(created_at) = today
today_rows = c.execute("SELECT COUNT(*) FROM items WHERE DATE(created_at) = ?", (today,)).fetchone()[0]
print(f"DATE(created_at)={today}: {today_rows}条")

# 按平台统计今天数据
src_today = c.execute(f"""
    SELECT source_type, original_source, COUNT(*) 
    FROM items 
    WHERE DATE(created_at) = ?
    GROUP BY source_type, original_source
    ORDER BY COUNT(*) DESC
""", (today,)).fetchall()
print(f"\n今天各平台条数:")
for s, o, n in src_today:
    print(f"  {s} / {o}: {n}")
