import sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
url = "https://weibo.com/ajax/side/hotSearch"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)',
    'Referer': 'https://weibo.com'
})
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode('utf-8'))
d = data.get('data', {})
print("realtime type:", type(d.get('realtime')))
r = d.get('realtime', [])
if isinstance(r, list):
    print("realtime items:", len(r))
    if r:
        print("first item:", str(r[0])[:200])
elif isinstance(r, dict):
    print("realtime keys:", list(r.keys()))
    for k, v in list(r.items())[:3]:
        print(f"  {k}: {str(v)[:100]}")
