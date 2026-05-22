import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

conn = get_conn()
rows = conn.execute('SELECT original_source, COUNT(*) FROM items GROUP BY original_source ORDER BY COUNT(*) DESC').fetchall()
total = sum(r[1] for r in rows)
print(f'Total items: {total}\n')
for r in rows:
    pct = r[1] / total * 100
    bar = '█' * int(pct / 2)
    print(f'{r[0]:<25} {r[1]:>4} ({pct:>5.1f}%) {bar}')
conn.close()
