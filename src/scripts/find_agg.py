import sys
sys.stdout.reconfigure(encoding='utf-8')

content = open(r"C:\Users\douzi457\.qclaw\workspace\情报系统\collect\collector.py", encoding='utf-8', errors='replace').read()
# 找 news_aggregator 相关行
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'news_agg' in line.lower() or 'fetch_news' in line.lower() or 'toutiao' in line.lower() or 'aggregator' in line.lower():
        print(f"{i+1}: {line.rstrip()}")
