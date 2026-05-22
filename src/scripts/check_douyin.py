import sys
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

conn = get_conn()
c = conn.cursor()

# 查抖音乱码条目
c.execute("""
    SELECT id, title, LENGTH(description) as dl, created_at
    FROM items
    WHERE original_source = 'douyin_hot'
    ORDER BY hot_value DESC, id DESC
    LIMIT 20
""")
rows = c.fetchall()
print(f"=== 抖音共 {len(rows)} 条 ===")
for r in rows:
    print(f"  id={r[0]} dl={r[2]} | {str(r[1])[:50]}")

# 统计乱码条数（description为NULL或极短）
c.execute("SELECT COUNT(*) FROM items WHERE original_source='douyin_hot' AND (description IS NULL OR LENGTH(description) < 5)")
bad = c.fetchone()[0]
total = c.execute("SELECT COUNT(*) FROM items WHERE original_source='douyin_hot'").fetchone()[0]
print(f"\n抖音乱码条目: {bad}/{total}")

c.close()
conn.close()
