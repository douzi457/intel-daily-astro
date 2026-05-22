import sys
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

conn = get_conn()
c = conn.cursor()

# 测试 GitHub/ProductHunt/HackerNews
c.execute("SELECT original_source, COUNT(*) FROM items GROUP BY original_source")
print("=== 全部来源 ===")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

# 测试 github/producthunt/hackernews 有多少条
c.execute("SELECT COUNT(*) FROM items WHERE original_source IN ('github','producthunt','hackernews')")
print(f"\ngithub/producthunt/hackernews 总数: {c.fetchone()[0]}")

# 列出前5条 github
c.execute("SELECT title, original_source FROM items WHERE original_source='github' LIMIT 3")
print("\n=== GitHub ===")
for r in c.fetchall():
    print(f"  {r}")

# 列出前5条 hackernews
c.execute("SELECT title, original_source FROM items WHERE original_source='hackernews' LIMIT 3")
print("\n=== HackerNews ===")
for r in c.fetchall():
    print(f"  {r}")

# 列出前5条 douyin_hot
c.execute("SELECT title, original_source FROM items WHERE original_source='douyin_hot' LIMIT 3")
print("\n=== 抖音 ===")
for r in c.fetchall():
    print(f"  {r}")

# 列出前5条 ithome
c.execute("SELECT title, original_source FROM items WHERE original_source='ithome' LIMIT 3")
print("\n=== IT之家 ===")
for r in c.fetchall():
    print(f"  {r}")

c.close()
conn.close()
