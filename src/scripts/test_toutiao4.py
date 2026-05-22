import sys
sys.stdout.reconfigure(encoding='utf-8')
import subprocess, json

script = r"C:\Users\douzi457\.qclaw\workspace\skills\news-aggregator-skill\scripts\fetch_news.py"
cmd = [sys.executable, script, "--source", "toutiao", "--limit", "3"]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=15, encoding='utf-8', errors='replace')
data = json.loads(r.stdout)
for item in data:
    print(f"title: {item['title'][:40]}")
    print(f"url: {item['url']}")
    print()
