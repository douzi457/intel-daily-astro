import sys, requests
sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.toutiao.com/',
}

url = "https://www.toutiao.com/api/pc/feed/?tab_name=hot_online&max_behot_time=0&count=3"
resp = requests.get(url, headers=HEADERS, timeout=8)
data = resp.json()
for item in data.get('data', [])[:3]:
    print(f"title: {item.get('title','')[:40]}")
    print(f"  source_url: {item.get('source_url','')}")
    print(f"  tag_url: {item.get('tag_url','')}")
    print(f"  item_id: {item.get('item_id','')}")
    print(f"  group_id: {item.get('group_id','')}")
    print()
