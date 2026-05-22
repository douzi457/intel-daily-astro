from db.db import get_conn
conn = get_conn()
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM items")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM items WHERE description IS NOT NULL AND description != ''")
with_desc = c.fetchone()[0]
print(f"Total items: {total}")
print(f"With description: {with_desc}")
print(f"Without description: {total - with_desc}")
conn.close()
