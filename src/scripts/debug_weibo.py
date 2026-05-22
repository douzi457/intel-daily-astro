import sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
url = "https://weibo.com/ajax/side/hotSearch"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)',
    'Referer': 'https://weibo.com',
    'Accept': 'application/json'
})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    print("ok:", data.get('ok'))
    print("data keys:", list(data.get('data', {}).keys()))
    bands = data.get('data', {}).get('bands', [])
    print("bands count:", len(bands))
    if bands:
        print("first band:", bands[0])
except Exception as e:
    print("Error:", e)
