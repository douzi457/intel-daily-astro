import sys
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

conn = get_conn()
c = conn.cursor()

c.execute("""
    SELECT original_source, COUNT(*), 
           SUM(CASE WHEN score > 0 THEN 1 ELSE 0 END) as scored
    FROM items
    WHERE source_type IN ('github', 'producthunt', 'hackernews')
    GROUP BY original_source
""")
print("=== GitHub/HackerNews/ProductHunt ===")
for r in c.fetchall():
    print(f"  {r[0]}: total={r[1]}, scored={r[2]}")

c.execute("""
    SELECT original_source, title, score
    FROM items
    WHERE source_type = 'github'
    ORDER BY score DESC
    LIMIT 5
""")
print("\n=== GitHub sample ===")
for r in c.fetchall():
    print(f"  score={r[2]} | {r[1][:60]}")

c.execute("""
    SELECT original_source, title, score
    FROM items
    WHERE source_type = 'producthunt'
    ORDER BY score DESC
    LIMIT 5
""")
print("\n=== ProductHunt sample ===")
for r in c.fetchall():
    print(f"  score={r[2]} | {r[1][:60]}")

c.execute("""
    SELECT original_source, title, score
    FROM items
    WHERE original_source = 'hackernews'
    ORDER BY score DESC
    LIMIT 5
""")
print("\n=== HackerNews sample ===")
for r in c.fetchall():
    print(f"  score={r[2]} | {r[1][:60]}")

c.close()
conn.close()
