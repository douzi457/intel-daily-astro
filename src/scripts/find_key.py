"""查找 ai_score.py 中的 API key 配置"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
with open('ai_score.py', 'r', encoding='utf-8') as f:
    t = f.read()
# 搜索 API key 相关配置
patterns = [
    r'API_KEY\s*=\s*["\']([^"\']+)["\']',
    r'api_key\s*=\s*["\']([^"\']+)["\']',
    r'minimax.*?["\']([a-zA-Z0-9_-]{20,})["\']',
    r'Bearer\s+["\']([^"\']+)["\']',
]
for p in patterns:
    m = re.search(p, t, re.I)
    if m:
        print(f"Found: {m.group(0)[:80]}")
print("---")
# 也检查环境变量方式
if 'os.environ' in t or 'getenv' in t:
    print("Uses os.environ for key lookup")
