import sys, requests
sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.toutiao.com/',
}

# 测试不同的今日头条 API
urls = [
    ("PC热榜API", "https://www.toutiao.com/api/pc/feed/?tab_name=hot_online&max_behot_time=0&count=5"),
    ("hot_board", "https://www.toutiao.com/api/pc/feed/?tab_name=hot_board&max_behot_time=0&count=5"),
]

for name, url in urls:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        data = resp.json()
        items = data.get('data', [])[:2]
        print(f"\n=== {name} ===")
        for item in items:
            print(f"  title: {item.get('title','')[:40]}")
            print(f"  url: [{item.get('url','')}]")
            print(f"  article_url: [{item.get('article_url','')}]")
            print(f"  item_url: [{item.get('item_url','')}]")
            print(f"  mid: [{item.get('mid','')}]")
            print(f"  group_id: [{item.get('group_id','')}]")
            print(f"  all keys: {list(item.keys())}")
    except Exception as e:
        print(f"{name} 失败: {e}")
