import sys
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

conn = get_conn()
c = conn.cursor()

# 查今天新采的抖音条目（created_at = today）
c.execute("""
    SELECT id, title, created_at
    FROM items
    WHERE original_source = 'douyin_hot'
    ORDER BY id DESC
    LIMIT 10
""")
rows = c.fetchall()
print("=== 抖音最新10条 ===")
for r in rows:
    print(f"  id={r[0]} | {r[1][:50]} | {r[2]}")

# 统计各平台今天新采多少条
c.execute("""
    SELECT original_source, COUNT(*) as cnt
    FROM items
    WHERE DATE(created_at) = DATE('now')
    GROUP BY original_source
    ORDER BY cnt DESC
""")
rows = c.fetchall()
print("\n=== 今天各平台新采条目 ===")
for r in rows:
    print(f"  {r[0]}: {r[1]}条")

# 查今天最早的条目时间
c.execute("SELECT MIN(created_at), MAX(created_at) FROM items WHERE DATE(created_at) = DATE('now')")
row = c.fetchone()
print(f"\n今天数据时间范围: {row[0]} ~ {row[1]}")

c.close()
conn.close()
