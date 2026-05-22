import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
from datetime import date

c = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")

rows = c.execute("""
    SELECT title, url, description
    FROM items
    WHERE original_source = 'v2ex'
    AND DATE(created_at) = ?
    AND (title LIKE '%送%' OR title LIKE '%福利%' OR title LIKE '%注册%'
         OR title LIKE '%码%' OR title LIKE '%额度%' OR title LIKE '%中转%'
         OR title LIKE '%API%' OR title LIKE '%Relay%' OR title LIKE '%Hyper%')
    ORDER BY ROWID DESC
""", (str(date.today()),)).fetchall()

print(f"找到 {len(rows)} 条赠送/额度帖子：\n")
for title, url, desc in rows:
    print(f"标题: {title}")
    print(f"链接: {url}")
    if desc:
        print(f"摘要: {desc[:100]}")
    print()
c.close()
