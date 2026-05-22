"""导出待翻译的国外内容条目"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

c = get_conn()
rows = c.execute(
    "SELECT id, source_type, original_source, title, description "
    "FROM items "
    "WHERE source_type IN ('reddit','hackernews','github','producthunt')"
).fetchall()

items = []
for row in rows:
    items.append({
        'id': row[0],
        'source_type': row[1],
        'original_source': row[2],
        'title': row[3] or '',
        'description': row[4] or '',
    })

with open('to_translate.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print(f"共导出 {len(items)} 条到 to_translate.json")
