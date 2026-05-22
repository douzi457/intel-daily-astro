"""检查待翻译条目"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

c = get_conn()
r = c.execute(
    "SELECT id, source_type, original_source, title, description FROM items "
    "WHERE source_type IN ('reddit','hackernews','github','producthunt')"
).fetchall()

print(f"待翻译条目总数: {len(r)}")
print(f"{'ID':<6} {'来源':<12} {'原始源':<20} {'标题(前50)'}")
print("-" * 100)
for row in r:
    tid, st, osrc, title, desc = row
    title_str = (title or '')[:60]
    print(f"{tid:<6} {st:<12} {(osrc or '')[:20]:<20} {title_str}")
