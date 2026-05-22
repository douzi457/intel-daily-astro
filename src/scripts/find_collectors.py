import sys
sys.stdout.reconfigure(encoding='utf-8')

# 检查 collector.py 里今日头条和抖音的 collect 函数
content = open(r"C:\Users\douzi457\.qclaw\workspace\情报系统\collect\collector.py", encoding='utf-8', errors='replace').read()
# 找 toutiao 和 douyin 相关行
lines = content.split('\n')
for i, line in enumerate(lines):
    if any(k in line.lower() for k in ['toutiao', 'douyin', 'gzh', 'weibo']):
        print(f"{i+1}: {line.rstrip()}")
