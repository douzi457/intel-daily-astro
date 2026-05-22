import sys, subprocess, json
sys.stdout.reconfigure(encoding='utf-8')

skill_dir = r"C:\Users\douzi457\.qclaw\workspace\skills\news-aggregator-skill\scripts"
script = skill_dir + r"\fetch_news.py"
cmd = [sys.executable, script, "--source", "toutiao", "--limit", "2"]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=15, encoding='utf-8', errors='replace')
print("STDOUT:", r.stdout[:1000])
print("STDERR:", r.stderr[:500])
