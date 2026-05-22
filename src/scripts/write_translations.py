"""翻译完成后，将中文写入数据库description字段"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

conn = get_conn()
c = conn.cursor()

with open('translations.json', 'r', encoding='utf-8') as f:
    translations = json.load(f)

updated = 0
for item_id, zh_desc in translations.items():
    c.execute("UPDATE items SET description = ? WHERE id = ?", (zh_desc, int(item_id)))
    if c.rowcount > 0:
        updated += 1

conn.commit()
print(f"数据库更新完成：{updated} 条")

# 验证
c.execute("SELECT COUNT(*) FROM items WHERE description IS NOT NULL AND description != ''")
count = c.fetchone()[0]
print(f"当前有 description 的条目：{count} 条")
conn.close()
