"""检查 items 表结构"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
c = sqlite3.connect('db/intel.db')
cols = c.execute("PRAGMA table_info(items)").fetchall()
print("items 表字段:")
for col in cols:
    print(f"  {col[1]} ({col[2]})")
