import sys, subprocess, json, time
from pathlib import Path

sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE    = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")
SKILLS_DIR   = Path(r"C:\Users\douzi457\.qclaw\workspace\skills")
FETCH_SCRIPT = SKILLS_DIR / "news-aggregator-skill" / "scripts" / "fetch_news.py"

SOURCES = ['bilibili', 'ithome', 'v2ex']

def run_py(script, *args):
    cmd = [sys.executable, str(script)] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                          encoding='utf-8', errors='replace')
        if r.returncode == 0 and r.stdout.strip():
            try:
                return json.loads(r.stdout.strip())
            except json.JSONDecodeError as e:
                print(f"  [WARN] JSON parse failed: {e}")
    except Exception as e:
        print(f"  [ERROR] {e}")
    return None

# Fetch fresh data and print it to see what we get
for src in SOURCES:
    print(f"\n=== {src} raw fetch ===")
    res = run_py(FETCH_SCRIPT, "--source", src, "--limit", "5")
    if isinstance(res, list):
        for it in res[:3]:
            print(f"  title: {repr(it.get('title','')[:50])}")
            print(f"  url: {it.get('url','')[:60]}")
    else:
        print(f"  No data returned, return type: {type(res)}")
