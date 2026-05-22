import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from db.db import get_conn

html_path = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统\output\day\2026-05-19.html")
html = html_path.read_text(encoding='utf-8')

# 各源在HTML中出现的次数
srcs = ['36kr','ithome','wallstreetcn','toutiao','producthunt','github',
        'hackernews','douyin','bilibili','v2ex','tencent','reddit',
        'LocalLLaMA','MachineLearning','github','Python','technology']
print("各源在HTML中出现次数：")
for s in srcs:
    cnt = html.count(s)
    if cnt > 0:
        print(f"  {s:20s} → {cnt}次")

print("\n检查五板块是否存在：")
for label in ['TOP10', 'AI技术', '开发工具', '行业', '中国平台']:
    found = label in html
    print(f"  {'✅' if found else '❌'} {label}")
