import sys
sys.stdout.reconfigure(encoding='utf-8')
import subprocess, json

node = r"C:\Program Files\nodejs\node.exe"
script = r"C:\Users\douzi457\.qclaw\workspace\skills\douyin-hot\scripts\douyin_json.js"
r = subprocess.run([node, script, "3"], capture_output=True, text=True, timeout=15, errors='replace')
data = json.loads(r.stdout)
for i in data:
    print(f"title: {i.get('title','')[:30]}")
    print(f"  link: {i.get('link','')}")
    print()
