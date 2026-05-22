import sys
sys.path.insert(0, '.')
from db.db import get_conn

conn = get_conn()
rows = conn.execute('SELECT original_source, COUNT(*) FROM items GROUP BY original_source ORDER BY COUNT(*) DESC').fetchall()
print('=== SOURCE BREAKDOWN ===')
for r in rows:
    print(f'{r[0]}: {r[1]}')
conn.close()
