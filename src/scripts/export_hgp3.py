from db.db import get_conn
conn = get_conn()
c = conn.cursor()
c.execute("""
    SELECT id, title, description, original_source
    FROM items
    WHERE original_source IN ('github', 'hackernews', 'producthunt')
    ORDER BY original_source, id
""")
rows = c.fetchall()
c.close()
conn.close()

items = [{'id': r[0], 'title': r[1], 'desc': r[2], 'source': r[3]} for r in rows]
print(f"共 {len(items)} 条待翻译")
import json
with open('hgp_titles.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
