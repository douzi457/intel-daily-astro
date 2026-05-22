import sys
sys.path.insert(0, '.')
from db.db import get_conn

conn = get_conn()
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM items WHERE score > 0")
scored = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM items")
total = c.fetchone()[0]

c.execute("SELECT original_source, COUNT(*), SUM(CASE WHEN score > 0 THEN 1 ELSE 0 END) as scored FROM items GROUP BY original_source ORDER BY scored DESC")
breakdown = c.fetchall()

print(f"Total items: {total}")
print(f"Items with AI score: {scored}")
print(f"Items without score: {total - scored}")
print()
for r in breakdown:
    status = "OK" if r[2] > 0 else "NO SCORE"
    print(f"  {r[0]}: total={r[1]}, scored={r[2]} [{status}]")

conn.close()
