import urllib.request
import json

# Test Reddit JSON API
subs = ['technology', 'programming', 'MachineLearning']
for s in subs:
    url = f'https://www.reddit.com/r/{s}/hot/.json?limit=10'
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        r = urllib.request.urlopen(req, timeout=10)
        data = json.load(r)
        posts = data['data']['children']
        print(f'=== r/{s} ({len(posts)} posts) ===')
        for p in posts[:3]:
            d = p['data']
            score = d.get('score', '?')
            print(f'  [{score}] {d["title"]}')
            print(f'    url: https://reddit.com{d.get("permalink","")}')
    except Exception as e:
        print(f'r/{s}: ERROR - {e}')
