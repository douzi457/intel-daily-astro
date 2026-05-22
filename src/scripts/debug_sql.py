import sys
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

conn = get_conn()
c = conn.cursor()

# 直接测试 github 查询
c.execute("""
    SELECT id, COALESCE(description, title), title, url, source_type, original_source
    FROM items
    WHERE original_source IN ('github', 'producthunt', 'hackernews')
    ORDER BY created_at DESC
    LIMIT 5
""")
rows = c.fetchall()
print(f"工具类查询返回: {len(rows)} 条")
for r in rows:
    print(f"  r[0]={r[0]}, r[1]={str(r[1])[:40]}, r[2]={str(r[2])[:40]}, r[3]={str(r[3])[:60]}")

# 测试 douyin 查询
c.execute("""
    SELECT id, COALESCE(description, title), title, url, source_type, original_source
    FROM items
    WHERE original_source IN ('douyin_hot', 'ithome', 'bilibili')
    ORDER BY created_at DESC
    LIMIT 5
""")
rows = c.fetchall()
print(f"\n中国平台查询返回: {len(rows)} 条")
for r in rows:
    print(f"  r[0]={r[0]}, r[1]={str(r[1])[:40]}, r[2]={str(r[2])[:40]}")

c.close()
conn.close()
