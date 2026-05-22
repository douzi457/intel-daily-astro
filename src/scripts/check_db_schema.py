import sys, sqlite3
sys.path.insert(0, '.')
from db.db import get_conn

conn = get_conn()

# Check table schema
print("=== items schema ===")
schema = conn.execute("PRAGMA table_info(items)")
for col in schema.fetchall():
    print(f"  {col[1]}: {col[2]}")

# Check what sources we have
print("\n=== sources ===")
rows = conn.execute("SELECT original_source, COUNT(*) FROM items GROUP BY original_source ORDER BY COUNT(*) DESC").fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]}")

conn.close()
