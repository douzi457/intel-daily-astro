"""
GitHub项目搜索 - 找热点聚合类项目
"""
import requests
import json
import sys

# 强制UTF-8输出
sys.stdout.reconfigure(encoding='utf-8')

def search_github(query, per_page=10):
    url = f'https://api.github.com/search/repositories?q={requests.utils.quote(query)}&sort=stars&per_page={per_page}'
    r = requests.get(url, headers={'Accept': 'application/vnd.github.v3+json'}, timeout=15)
    if r.status_code == 200:
        return r.json().get('items', [])
    else:
        print(f'Error {r.status_code}')
        return []

results = []

# 搜索各种热点聚合相关项目
queries = [
    ('weibo_scraper', 'weibo hot search api scraper'),
    ('zhihu_api', 'zhihu hot questions api scraper'),
    ('news_aggregator', 'news aggregator china open source'),
    ('rss_server', 'self-hosted rss server aggregator'),
    ('trending_api', 'trending topics api aggregator'),
    ('social_media_tools', 'social media monitoring tools'),
]

for cat, query in queries:
    print(f'Searching: {query}', flush=True)
    items = search_github(query)
    for repo in items[:5]:
        results.append({
            'category': cat,
            'name': repo['full_name'],
            'stars': repo['stargazers_count'],
            'description': repo.get('description', ''),
            'url': repo.get('html_url', ''),
            'topics': repo.get('topics', []),
            'language': repo.get('language', ''),
        })

# 按stars排序
results.sort(key=lambda x: x['stars'], reverse=True)

# 保存结果
output_path = r'C:\Users\douzi457\.qclaw\workspace\情报系统\github_projects.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f'\n保存了 {len(results)} 个项目到 {output_path}')
for r in results[:10]:
    print(f"  [{r['stars']}] {r['name']} - {r['description'][:60] if r['description'] else 'N/A'}")
