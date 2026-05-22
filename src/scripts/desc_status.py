from db.db import get_conn
conn = get_conn()
c = conn.cursor()
c.execute("SELECT source_type, COUNT(*) FROM items WHERE description IS NOT NULL AND description != '' GROUP BY source_type")
rows = c.fetchall()
print('Sources with description:')
for r in rows:
    print(f'  {r[0]}: {r[1]}')
total_with = sum(r[1] for r in rows)
print(f'Total with description: {total_with}')
c.execute("SELECT COUNT(*) FROM items WHERE description IS NULL OR description = ''")
print(f'Total WITHOUT description: {c.fetchone()[0]}')
conn.close()
