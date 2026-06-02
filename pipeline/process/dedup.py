# dedup.py — 去重模块（URL + 标题相似度）
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse, parse_qs
from ..config import PLATFORM_META


def normalize_url(url):
    """URL 归一化：去协议、尾斜杠、追踪参数。"""
    if not url:
        return ""
    parsed = urlparse(url)
    tracking = {'utm_source','utm_medium','utm_campaign','utm_term','utm_content','ref','from','cps_key','redirect','scene','source','tab'}
    clean_query = '&'.join(f'{k}={v}' for k, v in parse_qs(parsed.query).items() if k.lower() not in tracking)
    path = parsed.path.rstrip('/').lower() if parsed.path else ''
    host = parsed.netloc.lower()
    return f'{host}{path}?{clean_query}' if clean_query else f'{host}{path}'


def clean_title(title):
    """清洗标题，用于相似度匹配。"""
    t = re.sub(r'\s*[-–—|]\s*(36氪|知乎|B站|IT之家|华尔街见闻|今日头条|腾讯新闻|网易新闻|澎湃新闻|观察者网|创业邦|财联社|百度贴吧|贴吧|微博|抖音|V2EX|GitHub|HackerNews|ProductHunt).*$', '', title)
    t = re.sub(r'[^\w\一-鿿]', '', t)
    return t.strip().lower()[:50]


def dedup_items(items):
    """两阶段去重：URL 合并 + 标题相似度聚类。"""
    # Stage 1: URL 级合并
    url_map = {}
    for item in items:
        nu = normalize_url(item.get('url', ''))
        if nu:
            url_map.setdefault(nu, []).append(item)

    used_urls = set()
    url_deduped = []
    for item in items:
        nu = normalize_url(item.get('url', ''))
        if not nu or nu not in url_map or len(url_map[nu]) == 1:
            url_deduped.append(item)
        elif nu not in used_urls:
            used_urls.add(nu)
            cluster = sorted(url_map[nu], key=lambda x: x.get('score', 0), reverse=True)
            primary = dict(cluster[0])
            seen = set()
            merged = []
            for ci in cluster:
                src = ci.get('platform', '')
                if src and src not in seen:
                    seen.add(src)
                    merged.append({
                        'platform': src,
                        'label': PLATFORM_META.get(src, {}).get('label', src),
                        'color': PLATFORM_META.get(src, {}).get('color', '#94A3B8'),
                        'icon': PLATFORM_META.get(src, {}).get('icon', '📌'),
                        'url': ci.get('url', ''),
                    })
            primary['merged_sources'] = merged
            url_deduped.append(primary)

    # Stage 2: 同平台内标题相似度聚类
    items = url_deduped
    by_group = {}
    for item in items:
        group_key = f"{item.get('platform', 'unknown')}|{item.get('category', '其他')}"
        by_group.setdefault(group_key, []).append(item)

    result = []
    for group_key, cat_items in by_group.items():
        cat_items.sort(key=lambda x: x.get('score', 0), reverse=True)
        used = set()
        for i, primary in enumerate(cat_items):
            if i in used:
                continue
            used.add(i)
            cluster = [primary]
            clean_i = clean_title(primary.get('title', ''))
            for j, other in enumerate(cat_items):
                if j in used or i == j:
                    continue
                clean_j = clean_title(other.get('title', ''))
                min_len = min(len(clean_i), len(clean_j))
                threshold = 0.5 if min_len < 15 else 0.55
                if SequenceMatcher(None, clean_i, clean_j).ratio() > threshold:
                    cluster.append(other)
                    used.add(j)
            if len(cluster) > 1:
                cluster.sort(key=lambda x: x.get('score', 0), reverse=True)
                primary = dict(cluster[0])
                seen = set()
                merged = []
                for ci in cluster:
                    src = ci.get('platform', '')
                    if src and src not in seen:
                        seen.add(src)
                        merged.append({
                            'platform': src,
                            'label': PLATFORM_META.get(src, {}).get('label', src),
                            'color': PLATFORM_META.get(src, {}).get('color', '#94A3B8'),
                            'icon': PLATFORM_META.get(src, {}).get('icon', '📌'),
                            'url': ci.get('url', ''),
                        })
                primary['merged_sources'] = merged
                result.append(primary)
            else:
                result.append(primary)
    return result
