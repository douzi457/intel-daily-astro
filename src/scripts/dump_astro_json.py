# dump_astro_json.py
# 2026 Pro Intelligence Engine - Data Exporter
import sqlite3, json, os, re
from pathlib import Path
from difflib import SequenceMatcher

BASE_DIR = Path(__file__).parent
DB = BASE_DIR / "db" / "intel.db"
OUT_BASE = BASE_DIR.parent.parent / "src" / "data" / "rewrite"

# 映射配置：让每个源都有自己的“名片”
PLATFORM_META = {
    "36kr":         {"label": "36Kr",    "color": "#4A90E2", "icon": "📊"},
    "wallstreetcn": {"label": "华尔街见闻", "color": "#3395FF", "icon": "📈"},
    "ithome":       {"label": "IT之家",  "color": "#0090D8", "icon": "💻"},
    "github":       {"label": "GitHub",  "color": "#6CCB5F", "icon": "🐙"},
    "hackernews":   {"label": "HN",      "color": "#FF6600", "icon": "⚡"},
    "toutiao":      {"label": "今日头条", "color": "#E63946", "icon": "📰"},
    "weibo":        {"label": "微博热搜", "color": "#FF9500", "icon": "🔥"},
    "douyin":       {"label": "抖音热搜", "color": "#00F2EA", "icon": "🎵"},
    "v2ex":         {"label": "V2EX",    "color": "#4CAF50", "icon": "💬"},
    "producthunt":  {"label": "ProductHunt", "color": "#DA5430", "icon": "🚀"},
    "bilibili":     {"label": "B站",     "color": "#FB7299", "icon": "📺"},
    "zhihu":        {"label": "知乎",    "color": "#0066FF", "icon": "💡"},
    "baidu":        {"label": "百度热搜", "color": "#2932E1", "icon": "🔍"},
    "tieba":        {"label": "百度贴吧", "color": "#4B90E0", "icon": "📋"},
    "cailianshe":   {"label": "财联社",  "color": "#C71A1A", "icon": "📡"},
    "pengpai":      {"label": "澎湃新闻", "color": "#E60012", "icon": "📱"},
    "guancha":      {"label": "观察者网", "color": "#2B5797", "icon": "👁️"},
    "163":          {"label": "网易新闻", "color": "#DE1A1A", "icon": "📰"},
    "chuangye":     {"label": "创业邦",  "color": "#FF6B35", "icon": "🚀"},
}

def _clean_title(title):
    """去掉常见来源后缀，保留核心标题用于相似度匹配"""
    title = re.sub(r'\s*[-–—|]\s*(36氪|知乎|B站|IT之家|华尔街见闻|今日头条|腾讯新闻|网易新闻|澎湃新闻|观察者网|创业邦|财联社|百度贴吧|贴吧|微博|抖音|V2EX|GitHub|HackerNews|ProductHunt).*$', '', title)
    title = re.sub(r'\s*[-–—|]\s*(36Kr|IT Home|WallStreetCN|TouTiao|Tencent News|NetEase|The Paper|Guancha|Cyzone|Cailianshe|Baidu Tieba|Baidu|Zhihu|Bilibili).*$', '', title)
    title = re.sub(r'[^\w一-鿿]', '', title)  # 去标点，只留字母数字中文
    return title.strip().lower()[:50]

def _normalize_url(url):
    """标准化 URL：去协议、去尾斜杠、去跟踪参数、去片段"""
    if not url:
        return ''
    from urllib.parse import urlparse, urlencode, parse_qs
    parsed = urlparse(url)
    # 只去掉常见跟踪参数，保留有意义的 query（如 weibo?q=关键词）
    tracking_params = {'utm_source','utm_medium','utm_campaign','utm_term','utm_content','ref','from','cps_key','redirect','scene','source','tab'}
    clean_query = '&'.join(f'{k}={v}' for k, v in parse_qs(parsed.query).items() if k.lower() not in tracking_params)
    path = parsed.path.rstrip('/').lower() if parsed.path else ''
    host = parsed.netloc.lower()
    if clean_query:
        return f'{host}{path}?{clean_query}'
    return f'{host}{path}'

def dedup_items(items):
    """两重去重：URL 级别 + 标题相似度聚合"""
    # 第一重：同 URL 合并（不同源抓了同一篇文章）
    url_map: dict[str, list] = {}
    for item in items:
        nu = _normalize_url(item.get('url', ''))
        if nu:
            url_map.setdefault(nu, []).append(item)
    
    used_urls = set()
    url_deduped = []
    for item in items:
        nu = _normalize_url(item.get('url', ''))
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
                        'label': ci.get('platform_label', ''),
                        'color': ci.get('platform_color', ''),
                        'icon': ci.get('platform_icon', ''),
                        'url': ci.get('url', ''),
                    })
            primary['merged_sources'] = merged
            url_deduped.append(primary)
    
    # 第二重：同平台+同分类内按标题相似度聚合（不再跨平台合并）
    items = url_deduped
    by_group: dict[str, list] = {}
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
            clean_i = _clean_title(primary.get('title', ''))

            for j, other in enumerate(cat_items):
                if j in used or i == j:
                    continue
                clean_j = _clean_title(other.get('title', ''))
                # 短标题放宽阈值，长标题严格一点
                min_len = min(len(clean_i), len(clean_j))
                threshold = 0.5 if min_len < 15 else 0.55
                if SequenceMatcher(None, clean_i, clean_j).ratio() > threshold:
                    cluster.append(other)
                    used.add(j)

            if len(cluster) > 1:
                # 取评分最高的为主条目
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
                            'label': ci.get('platform_label', ''),
                            'color': ci.get('platform_color', ''),
                            'icon': ci.get('platform_icon', ''),
                            'url': ci.get('url', ''),
                        })
                primary['merged_sources'] = merged
                result.append(primary)
            else:
                result.append(primary)

    return result

def dump_lang(day_str, lang='zh'):
    if not DB.exists(): return
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE date_key=? ORDER BY score DESC LIMIT 500", (day_str,))
    rows = cur.fetchall()
    conn.close()

    items = []
    for r in rows:
        # 1. 来源识别优化：优先使用 original_source 来定义卡片归属
        source_key = r["original_source"] if r["original_source"] in PLATFORM_META else r["source_type"]
        meta = PLATFORM_META.get(source_key, {"label": source_key, "color": "#94a3b8", "icon": "📌"})
        
        # 2. AI 摘要优先：如果 AI 生成了摘要，就直接作为主描述显示
        raw_desc = r["ai_summary"] or r["description"] or ""
        # 去除摘要中可能存在的“摘要：”字样
        clean_desc = raw_desc.replace("摘要：", "").replace("Summary:", "").strip()
        
        # 3. 语言适配
        if lang == 'zh':
            title = r["zh_title"] or r["title"]
            desc = clean_desc
        else:
            title = r["en_title"] or r["title"]
            desc = r["en_summary"] or clean_desc
        
        items.append({
            "id": r["id"],
            "title": title,
            "desc": desc,
            "url": r["url"],
            "platform": source_key,
            "platform_label": meta["label"],
            "platform_color": meta["color"],
            "platform_icon": meta["icon"],
            "hot": r["hot_value"] or 0,
            "date": r["date_key"],
            "score": r["score"] or 0,
            "category": r["category"] or "其他"
        })

    # ── 同事件多源合并 ──
    total = len(items)
    items = dedup_items(items)
    deduped = total - len(items)

    out_dir = OUT_BASE / lang
    out_dir.mkdir(exist_ok=True, parents=True)
    with open(out_dir / f"{day_str}.json", "w", encoding="utf-8") as f:
        json.dump({"date": day_str, "items": items}, f, ensure_ascii=False, indent=2)
    print(f"  {lang} - {day_str}: {len(items)} items (deduped {deduped}) exported.")

def dump_all():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT date_key FROM items ORDER BY date_key DESC LIMIT 30")
    dates = [r[0] for r in cur.fetchall()]
    conn.close()
    for d in dates:
        dump_lang(d, 'zh')
        dump_lang(d, 'en')

if __name__ == "__main__":
    dump_all()
