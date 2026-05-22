# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import os

WORKSPACE = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")
sys.path.insert(0, str(WORKSPACE))
os.chdir(str(WORKSPACE))

from db.db import get_items_by_date, get_all_dates
from datetime import date, timedelta
from collections import Counter

today = date.today().isoformat()
items = get_items_by_date(today)
print(f'今日({today})数据条数: {len(items)}')

for i in range(7):
    d = (date.today() - timedelta(days=i)).isoformat()
    itms = get_items_by_date(d)
    print(f'  {d}: {len(itms)}条')

srcs = Counter(it.get('source_type','unknown') or 'unknown' for it in items)
print(f'今日来源分布: {dict(srcs)}')

all_dates = get_all_dates()
if all_dates:
    latest = all_dates[0]['date_key']
    sample = get_items_by_date(latest)[:5]
    for s in sample:
        print(f'\n标题: {s.get("title","")[:60]}')
        desc = str(s.get("description","") or "").strip()
        print(f'描述: {desc[:100]}')
        print(f'来源: {s.get("source_type","")} / {s.get("original_source","")}')
        url = str(s.get("url","") or "")
        print(f'URL: {url[:70]}')
        print(f'score: {s.get("score")} hot_value: {s.get("hot_value")}')