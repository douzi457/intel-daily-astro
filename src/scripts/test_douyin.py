import sys, subprocess, json
sys.stdout.reconfigure(encoding='utf-8')

script = r"C:\Users\douzi457\.qclaw\workspace\skills\douyin-hot\scripts\douyin_json.js"
cmd = [r"C:\Program Files\nodejs\node.exe", script, "3"]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
print("STDOUT:", r.stdout[:800])
print("STDERR:", r.stderr[:300])
