from db.db import get_conn
conn = get_conn()
c = conn.cursor()

# 检查各来源的 description 填充情况
c.execute("""
    SELECT source_type, original_source,
           COUNT(*) as total,
           SUM(CASE WHEN description IS NOT NULL AND description != '' THEN 1 ELSE 0 END) as has_desc
    FROM items
    GROUP BY source_type, original_source
""")
rows = c.fetchall()
print("各来源 description 填充情况：")
for r in rows:
    print(f"  {r[0]:12s} | {r[1]:30s} | 共{r[2]:4d}条 | 已翻译{r[3]:4d}条")

# 找还没有 description 的国外来源
c.execute("""
    SELECT id, source_type, original_source, title, description
    FROM items
    WHERE (description IS NULL OR description = '')
      AND source_type IN ('hackernews', 'github', 'producthunt')
    LIMIT 20
""")
pending = c.fetchall()
print(f"\n待翻译（hackernews/github/producthunt）：{len(pending)} 条")
for r in pending[:5]:
    print(f"  id={r[0]}, {r[1]}, {r[2]}, title={r[3][:60]}")

conn.close()
