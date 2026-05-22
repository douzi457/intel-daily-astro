"""
搜索GitHub上的Docker部署情报项目
"""
import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def search_github(query, per_page=15):
    url = f'https://api.github.com/search/repositories?q={requests.utils.quote(query)}&sort=stars&per_page={per_page}'
    r = requests.get(url, headers={'Accept': 'application/vnd.github.v3+json'}, timeout=15)
    if r.status_code == 200:
        return r.json().get('items', [])
    return []

results = []

# Docker部署的情报项目
queries = [
    ('rss_server_docker', 'rss server aggregator docker self-hosted'),
    ('news_aggregator_docker', 'news aggregator docker self-hosted'),
    ('social_media_docker', 'weibo zhihu scraper docker api'),
    ('tech_trends_docker', 'tech trends monitoring docker'),
    ('osint_docker', 'osint docker social media monitoring'),
    ('ai_news_docker', 'AI news aggregator docker'),
    ('media_monitor_docker', 'media monitoring docker self-hosted'),
]

for cat, query in queries:
    print(f'搜索: {query}', flush=True)
    items = search_github(query)
    for repo in items[:5]:
        # 检查是否有Docker相关topics或描述
        topics = repo.get('topics', [])
        desc = repo.get('description', '').lower()
        has_docker = any('docker' in str(t).lower() or 'container' in str(t).lower() for t in topics) or 'docker' in desc
        
        results.append({
            'category': cat,
            'name': repo['full_name'],
            'stars': repo['stargazers_count'],
            'description': repo.get('description', ''),
            'url': repo.get('html_url', ''),
            'topics': topics,
            'language': repo.get('language', ''),
            'has_docker': has_docker,
            'dockerfile_url': f"https://raw.githubusercontent.com/{repo['full_name']}/main/Dockerfile" if has_docker else None
        })

# 按stars排序
results.sort(key=lambda x: x['stars'], reverse=True)

# 保存
output_path = r'C:\Users\douzi457\.qclaw\workspace\情报系统\docker_projects.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f'\n保存了 {len(results)} 个项目到 {output_path}')
for r in results[:15]:
    docker标记 = '[Docker]' if r['has_docker'] else ''
    print(f"  [{r['stars']}] {r['name']} {docker标记}")
    print(f"    {r['description'][:80] if r['description'] else 'N/A'}")
