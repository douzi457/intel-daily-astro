import requests
import json

url = 'https://weibo.com/ajax/statuses/hot_band'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://weibo.com',
    'Accept': 'application/json'
}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    data = resp.json()
    band_list = data.get('data', {}).get('band_list', [])
    print(f'Total items: {len(band_list)}')
    for i, item in enumerate(band_list[:20]):
        word = item.get('word', item.get('hot_word', ''))
        raw_hot = item.get('raw_hot', '')
        print(f'{i+1}. {word} - {raw_hot}')
except Exception as e:
    print(f'Error: {e}')