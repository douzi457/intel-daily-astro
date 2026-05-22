"""导出所有待翻译条目的title"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

conn = get_conn()
c = conn.cursor()
c.execute("""
    SELECT id, source_type, original_source, title
    FROM items
    WHERE source_type IN ('reddit','hackernews','github','producthunt')
    AND title IS NOT NULL
""")
rows = c.fetchall()
items = [{'id': r[0], 'source': r[1], 'sub': r[2], 'title': r[3]} for r in rows]
with open('titles_to_translate.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
print(f"共 {len(items)} 条")
conn.close()
