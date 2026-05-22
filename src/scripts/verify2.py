import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

conn = get_conn()
check = ['toutiao', 'tencent', '36kr', 'wallstreetcn', 'ithome', 'bilibili', 'v2ex']
print('=== ENCODING VERIFY ===')
for src in check:
    rows = conn.execute(
        'SELECT title FROM items WHERE original_source=? LIMIT 2', (src,)
    ).fetchall()
    print(f'\n[{src}]')
    for r in rows:
        t = r[0] if r[0] else '(empty)'
        print(f'  {t[:60]}')
conn.close()
