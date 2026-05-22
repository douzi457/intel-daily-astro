import sys
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

conn = get_conn()
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM items WHERE score IS NOT NULL AND score > 0')
print('有评分的条目:', c.fetchone()[0])

c.execute('SELECT COUNT(*) FROM items WHERE (score IS NULL OR score = 0) AND description IS NOT NULL AND description != ""')
print('无评分但有描述:', c.fetchone()[0])

c.execute('SELECT original_source, COUNT(*) FROM items WHERE score IS NOT NULL AND score > 0 GROUP BY original_source')
print('\n评分来源分布:')
for r in c.fetchall():
    print(f'  {r[0]}: {r[1]}')

c.execute('SELECT original_source, COUNT(*) FROM items GROUP BY original_source')
print('\n各源总数:')
for r in c.fetchall():
    print(f'  {r[0]}: {r[1]}')

c.close()
conn.close()
