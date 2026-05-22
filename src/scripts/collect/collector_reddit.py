"""
Reddit 采集器 - collector_reddit.py
支持多个热门技术/AI社区
"""
import urllib.request, json, time, sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.db import upsert_item, get_conn

# 订阅技术社区列表
SUBREDDITS = [
    ('technology', '科技'),
    ('programming', '编程'),
    ('MachineLearning', '机器学习'),
    ('artificial', 'AI'),
    ('github', 'GitHub'),
    ('Python', 'Python'),
    ('LocalLLaMA', '本地LLM'),
]

BASE_URL = 'https://www.reddit.com/r/{sub}/hot/.json?limit=25'


def fetch_subreddit(sub, label, collected_at):
    """采集单个 subreddit"""
    url = BASE_URL.format(sub=sub)
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        r = urllib.request.urlopen(req, timeout=15)
        data = json.load(r)
        posts = data['data']['children']
    except Exception as e:
        sys.stderr.write(f'  [{sub}] 请求失败: {e}\n')
        return 0

    count = 0
    for p in posts:
        d = p['data']
        title = d.get('title', '').strip()
        if not title:
            continue

        reddit_url = f"https://reddit.com{d.get('permalink', '')}"
        desc = d.get('selftext', '').strip()[:500]
        score = d.get('score', 0)
        comments = d.get('num_comments', 0)
        flair = d.get('link_flair_text', '') or ''
        author = d.get('author', '')

        item = {
            'title': title,
            'url': reddit_url,
            'description': desc,
            'source_type': 'reddit',
            'original_source': f'reddit/{sub}',
            'hot_value': score,
            'frequency': 1,
            'pub_time': d.get('created_utc', ''),
            'author': author,
            'flair': flair,
        }

        added, skipped = upsert_item(item, collected_at[:10])
        if added:
            count += 1

    sys.stderr.write(f'  [{sub}] +{count}条 (共{len(posts)}条热帖)\n')
    return count


def collect_reddit():
    """主采集函数"""
    collected_at = time.strftime('%Y-%m-%d')
    total = 0

    sys.stderr.write('=== Reddit 采集开始 ===\n')
    for sub, label in SUBREDDITS:
        n = fetch_subreddit(sub, label, collected_at)
        total += n
        time.sleep(1.5)  # 礼貌延迟，避免限流

    sys.stderr.write(f'=== Reddit 完成: 总计 +{total}条 ===\n')
    return total
    return total


if __name__ == '__main__':
    total = collect_reddit()
    # 输出 JSON 供 collector.py 的 run_py() 解析
    import json
    print(json.dumps({'done': True, 'total': total}), flush=True)
