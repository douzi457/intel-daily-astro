import sys, os
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3

db_dir = r'C:\Users\douzi457\.qclaw\workspace\情报系统\db'
files = [f for f in os.listdir(db_dir) if f.endswith('.db')]

for f in files:
    path = os.path.join(db_dir, f)
    print(f'\n=== {f} ===')
    conn = sqlite3.connect(path)
    c = conn.cursor()
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f'表: {tables}')
    
    for tn in tables:
        try:
            cnt = c.execute(f'SELECT COUNT(*) FROM {tn}').fetchone()[0]
            cols = [col[1] for col in c.execute(f'PRAGMA table_info({tn})').fetchall()]
            print(f'  {tn}: {cnt}行, 列: {cols[:10]}')
        except Exception as e:
            print(f'  {tn}: {e}')
    
    # 如果有 items 或 intelligence 表，做详细分析
    for tn in tables:
        if tn == 'items':
            print(f'\n  【items 详细】')
            c2 = conn.cursor()
            # 今日
            c2.execute("SELECT COUNT(*) FROM items WHERE DATE(created_at)=date('now','localtime')")
            print(f'  今日: {c2.fetchone()[0]}')
            # 近7天
            c2.execute("SELECT COUNT(*) FROM items WHERE DATE(created_at)>=date('now','-7 days','localtime')")
            print(f'  近7天: {c2.fetchone()[0]}')
            # 平台分布
            c2.execute('SELECT original_source, COUNT(*) FROM items GROUP BY original_source ORDER BY COUNT(*) DESC')
            for src, cnt in c2.fetchall():
                print(f'    {src}: {cnt}')
    
    conn.close()