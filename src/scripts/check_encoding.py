from db.db import get_conn
conn = get_conn()
c = conn.cursor()

# 检查三个来源的乱码情况
for src in ['bilibili', 'ithome', 'v2ex']:
    c.execute(f"""
        SELECT id, title, url
        FROM items
        WHERE original_source = '{src}' OR source_type = '{src}'
        LIMIT 3
    """)
    rows = c.fetchall()
    print(f"\n=== {src} ===")
    for r in rows:
        print(f"ID:{r[0]} | {repr(r[1][:60])}")

# 检查所有来源的乱码情况
c.execute("SELECT original_source, COUNT(*) FROM items GROUP BY original_source ORDER BY COUNT(*) DESC")
print("\n=== 所有来源 ===")
for r in c.fetchall():
    print(f"{r[0]}: {r[1]}")
conn.close()
