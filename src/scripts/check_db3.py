import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
db_path = r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT id, title, source_type, original_source FROM items WHERE source_type='reddit' LIMIT 3")
for row in cur.fetchall():
    print(f"  id={row[0]} title={row[1][:30]} source_type={row[2]} original_source={row[3]}")
conn.close()
