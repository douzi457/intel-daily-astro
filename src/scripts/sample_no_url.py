import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
conn = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")
c = conn.cursor()

# 今日头条样本
rows = c.execute("SELECT title, url, description FROM items WHERE original_source='toutiao' LIMIT 2").fetchall()
print("=== 今日头条样本 ===")
for r in rows:
    print(f"标题: {r[0][:50]}")
    print(f"URL: [{r[1]}]")
    print(f"描述: {str(r[2])[:100]}")
    print()

# 抖音样本
rows2 = c.execute("SELECT title, url, description FROM items WHERE source_type='douyin' LIMIT 2").fetchall()
print("=== 抖音样本 ===")
for r in rows2:
    print(f"标题: {r[0][:50]}")
    print(f"URL: [{r[1]}]")
    print(f"描述: {str(r[2])[:100]}")
