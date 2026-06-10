#!/usr/bin/env python3
"""
cleanup_data.py — 删除 7 天前的数据文件（按文件名中的日期判断）
在 GH Actions workflow 中每次采集后执行，保持仓库数据为滚动 7 天窗口。
"""
import os, glob
from datetime import datetime, timezone, timedelta

cutoff = datetime.now(timezone.utc) - timedelta(days=7)
for pattern in [
    'src/data/v4/daily-*.json',
    'src/data/rewrite/zh/*.json',
    'src/data/rewrite/en/*.json',
    'public/data/daily-*.json',
]:
    for f in glob.glob(pattern):
        base = os.path.basename(f).replace('daily-', '').replace('.json', '')
        try:
            fd = datetime.strptime(base[:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            if fd < cutoff:
                os.remove(f)
                print(f'  Removed old: {f}')
        except Exception:
            pass
