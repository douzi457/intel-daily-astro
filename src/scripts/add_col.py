from db.db import get_conn
conn = get_conn()
try:
    conn.execute('ALTER TABLE items ADD COLUMN ai_summary TEXT DEFAULT ""')
    print('添加 ai_summary 列成功')
except Exception as e:
    print(f'ai_summary 列: {e}')
try:
    conn.execute('ALTER TABLE items ADD COLUMN comments INTEGER DEFAULT 0')
    print('添加 comments 列成功')
except Exception as e:
    print(f'comments 列: {e}')
conn.commit()
conn.close()
print('Done')
