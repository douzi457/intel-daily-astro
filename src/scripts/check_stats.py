import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\Users\douzi457\.qclaw\workspace\情报系统")
from db.db import get_conn
with get_conn() as c:
    rows = c.execute("SELECT source_type, COUNT(*) FROM items GROUP BY source_type ORDER BY COUNT(*) DESC").fetchall()
    for s, n in rows:
        print(f"{s}: {n}")
    print(f"Total: {sum(n for _, n in rows)}")
