import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

conn = get_conn()

total = conn.execute("SELECT COUNT(*) FROM items WHERE original_source='douyin_hot'").fetchone()[0]
print(f"Current douyin items: {total}")

if total > 10:
    # Get IDs of top 10 by hot_value
    top_ids = [r[0] for r in conn.execute(
        "SELECT id FROM items WHERE original_source='douyin_hot' ORDER BY hot_value DESC LIMIT 10"
    ).fetchall()]
    
    placeholders = ','.join('?' * len(top_ids))
    deleted = conn.execute(
        f"DELETE FROM items WHERE original_source='douyin_hot' AND id NOT IN ({placeholders})",
        top_ids
    ).rowcount
    conn.commit()
    print(f"Deleted {deleted} excess douyin items, kept 10")
else:
    print("No cleanup needed")

remaining = conn.execute("SELECT COUNT(*) FROM items WHERE original_source='douyin_hot'").fetchone()[0]
print(f"Remaining douyin items: {remaining}")

rows = conn.execute(
    "SELECT title, hot_value FROM items WHERE original_source='douyin_hot' ORDER BY hot_value DESC LIMIT 5"
).fetchall()
print("\nTop 5 douyin items:")
for r in rows:
    print(f"  hot={r[1]} | {r[0][:40]}")

conn.close()
