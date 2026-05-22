import sys
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn
conn = get_conn()
c = conn.cursor()
c.execute('SELECT DISTINCT original_source FROM items LIMIT 20')
print("original_source:", [r[0] for r in c.fetchall()])
c.execute('SELECT DISTINCT source_type FROM items LIMIT 20')
print("source_type:", [r[0] for r in c.fetchall()])
conn.close()
