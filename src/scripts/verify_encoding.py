import sys
sys.path.insert(0, '.')
from db.db import get_conn

conn = get_conn()
for src in ['bilibili', 'ithome', 'v2ex']:
    c = conn.execute('SELECT title FROM items WHERE original_source=? LIMIT 3', (src,))
    rows = c.fetchall()
    print(f'\n=== {src} ===')
    for r in rows:
        title = r[0] if r[0] else '(empty)'
        print(f'  {title[:70]}')
conn.close()
