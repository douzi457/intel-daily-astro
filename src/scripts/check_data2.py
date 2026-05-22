# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import os

WORKSPACE = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")
sys.path.insert(0, str(WORKSPACE))
os.chdir(str(WORKSPACE))

from db.db import get_items_by_date, get_all_dates, get_conn
from datetime import date, timedelta
from collections import Counter

# 看所有来源类型（不限日期，全部）
conn = get_conn()
cur = conn.execute("SELECT source_type, original_source, COUNT(*) as cnt FROM items GROUP BY source_type, original_source ORDER BY cnt DESC")
rows = cur.fetchall()
print("=== 所有来源类型 ===")
for r in rows:
    print(f"  {r['source_type']} / {r['original_source']}: {r['cnt']}条")

# 看今日所有来源
today = date.today().isoformat()
items = get_items_by_date(today)
srcs = Counter(it.get('source_type','unknown') or 'unknown' for it in items)
print(f"\n=== 今日({today})来源分布 ===")
for k, v in srcs.most_common():
    print(f"  {k}: {v}条")

# 看前10条今日数据（含完整字段）
print(f"\n=== 今日样本(10条) ===")
for s in items[:10]:
    print(f"标题: {s.get('title','')[:50]}")
    print(f"  来源: {s.get('source_type','')} / {s.get('original_source','')}")
    print(f"  score: {s.get('score')} | hot: {s.get('hot_value')} | freq: {s.get('frequency')}")
    print()