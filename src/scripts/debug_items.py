import sys
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

conn = get_conn()
c = conn.cursor()

# 看看哪些中文平台条目有 description
c.execute("""
    SELECT original_source, title, LENGTH(description) as dl
    FROM items
    WHERE original_source IN ('ithome','v2ex','bilibili','36kr','tencent','toutiao','wallstreetcn')
      AND title IS NOT NULL
    ORDER BY dl DESC
    LIMIT 10
""")
rows = c.fetchall()
print("=== 中文平台条目示例 ===")
for r in rows:
    print(f"[{r[0]}] len={r[2]} | {r[1][:50]}")

# 看看 douyin 的 description
c.execute("""
    SELECT original_source, title, description, LENGTH(description)
    FROM items
    WHERE original_source = 'douyin_hot'
      AND description IS NOT NULL
    ORDER BY hot_value DESC
    LIMIT 5
""")
rows = c.fetchall()
print("\n=== 抖音条目（description非空）===")
for r in rows:
    print(f"[{r[0]}] dl={r[3]} | title={r[1][:40]}")
    print(f"  desc={r[2][:80] if r[2] else 'None'}")

# 看看 reddit 的 description（中文）
c.execute("""
    SELECT original_source, title, description
    FROM items
    WHERE score > 0 AND score < 10
    LIMIT 5
""")
rows = c.fetchall()
print("\n=== Reddit 7-9分区间 ===")
for r in rows:
    print(f"[{r[0]}] score<10 | {r[1][:50]}")
    print(f"  desc={r[2][:80] if r[2] else 'None'}")

c.close()
conn.close()
