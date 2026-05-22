import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
c = sqlite3.connect(r"C:\Users\douzi457\.qclaw\workspace\情报系统\db\intel.db")
cols = [r[1] for r in c.execute("PRAGMA table_info(items)")]
print("数据库字段:", cols)
c.close()
