# collect_rss.py
# RSS-based intelligence collector for intel-daily-astro
# Uses newsnow RSS feed as primary source + supplementary direct RSS feeds
import os, json, re, time, hashlib, random
from datetime import datetime, timezone, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET
from difflib import SequenceMatcher
from urllib.parse import urlparse, parse_qs
import requests

BASE_DIR = Path(__file__).parent
OUT_BASE = BASE_DIR.parent.parent / "src" / "data" / "rewrite"

API_KEY = os.environ.get("ZHIPU_API_KEY")
BAIDU_APP_ID = os.environ.get("BAIDU_TRANSLATE_APP_ID", "")
BAIDU_SECRET_KEY = os.environ.get("BAIDU_TRANSLATE_SECRET_KEY", "")
DAILY_TRANSLATE_LIMIT = 30000

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

PLATFORM_META = {
    "36kr":         {"label": "36Kr",       "color": "#4A90E2", "icon": "📊"},
    "wallstreetcn": {"label": "华尔街见闻", "color": "#3395FF", "icon": "📈"},
    "ithome":       {"label": "IT之家",     "color": "#0090D8", "icon": "💻"},
    "github":       {"label": "GitHub",     "color": "#6CCB5F", "icon": "🐙"},
    "hackernews":   {"label": "HackerNews", "color": "#FF6600", "icon": "⚡"},
    "toutiao":      {"label": "今日头条",   "color": "#E63946", "icon": "📰"},
    "weibo":        {"label": "微博热搜",   "color": "#FF9500", "icon": "🔥"},
    "douyin":       {"label": "抖音热搜",   "color": "#00F2EA", "icon": "🎵"},
    "v2ex":         {"label": "V2EX",       "color": "#4CAF50", "icon": "💬"},
    "producthunt":  {"label": "ProductHunt","color": "#DA5430", "icon": "🚀"},
    "bilibili":     {"label": "B站",        "color": "#FB7299", "icon": "📺"},
    "zhihu":        {"label": "知乎",       "color": "#0066FF", "icon": "💡"},
    "baidu":        {"label": "百度热搜",   "color": "#2932E1", "icon": "🔍"},
    "tieba":        {"label": "百度贴吧",   "color": "#4B90E0", "icon": "📋"},
    "cailianshe":   {"label": "财联社",     "color": "#C71A1A", "icon": "📡"},
    "pengpai":      {"label": "澎湃新闻",   "color": "#E60012", "icon": "📱"},
    "guancha":      {"label": "观察者网",   "color": "#2B5797", "icon": "👁️"},
    "163":          {"label": "网易新闻",   "color": "#DE1A1A", "icon": "📰"},
    "chuangye":     {"label": "创业邦",     "color": "#FF6B35", "icon": "🚀"},
    "juejin":       {"label": "掘金",       "color": "#0078F0", "icon": "💎"},
    "sspai":        {"label": "少数派",     "color": "#D33A2C", "icon": "📱"},
    "solidot":      {"label": "Solidot",    "color": "#555555", "icon": "🔗"},
    "coolapk":      {"label": "酷安",       "color": "#56B4E9", "icon": "📲"},
    "freebuf":      {"label": "FreeBuf",    "color": "#333333", "icon": "🛡️"},
    "hupu":         {"label": "虎扑",       "color": "#D32F2F", "icon": "🏀"},
    "tencent":      {"label": "腾讯新闻",   "color": "#1E90FF", "icon": "📺"},
    "ifeng":        {"label": "凤凰网",     "color": "#FF6600", "icon": "📰"},
    "zaobao":       {"label": "联合早报",   "color": "#B22222", "icon": "📰"},
    "chongbuluo":   {"label": "虫部落",     "color": "#4A90E2", "icon": "🔍"},
    "xueqiu":       {"label": "雪球",       "color": "#FF6B35", "icon": "📊"},
    "news_aggregator": {"label": "新闻聚合", "color": "#94A3B8", "icon": "📡"},
}

# URL → platform key mapping
URL_PLATFORM_MAP = [
    (r'ithome\.com', 'ithome'),
    (r'news\.ycombinator\.com', 'hackernews'),
    (r'hackernews', 'hackernews'),
    (r'github\.com', 'github'),
    (r'v2ex\.com', 'v2ex'),
    (r'36kr\.com', '36kr'),
    (r'wallstreetcn\.com', 'wallstreetcn'),
    (r'toutiao\.com', 'toutiao'),
    (r'weibo\.com', 'weibo'),
    (r'zhihu\.com', 'zhihu'),
    (r'baidu\.com/s', 'baidu'),
    (r'tieba\.baidu\.com', 'tieba'),
    (r'cls\.cn', 'cailianshe'),
    (r'thepaper\.cn', 'pengpai'),
    (r'guancha\.cn', 'guancha'),
    (r'163\.com', '163'),
    (r'cyzone\.cn', 'chuangye'),
    (r'juejin\.cn', 'juejin'),
    (r'sspai\.com', 'sspai'),
    (r'solidot\.org', 'solidot'),
    (r'coolapk\.com', 'coolapk'),
    (r'freebuf\.com', 'freebuf'),
    (r'hupu\.com', 'hupu'),
    (r'news\.qq\.com', 'tencent'),
    (r'ifeng\.com', 'ifeng'),
    (r'zaobao\.com', 'zaobao'),
    (r'chongbuluo\.com', 'chongbuluo'),
    (r'xueqiu\.com', 'xueqiu'),
    (r'producthunt\.com', 'producthunt'),
    (r'bilibili\.com', 'bilibili'),
    (r'douyin\.com', 'douyin'),
    (r'zaochenbao\.com', 'news_aggregator'),
]

# Supplementary direct RSS feeds (sources not reliably in newsnow feed)
SUPPLEMENTARY_RSS = [
    ("ruanyifeng",  "阮一峰",   "http://feeds.feedburner.com/ruanyifeng",        "📡"),
    ("sspai",       "少数派",   "https://sspai.com/feed",                         "📱"),
    ("geekpark",    "GeekPark", "https://www.geekpark.net/rss",                   "🚀"),
]

PER_SOURCE_LIMIT = 15  # max items per source for diversity
MAX_TOTAL = 300        # total items before hit AI processing


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def detect_platform(url):
    """Map URL to platform key using domain patterns."""
    if not url:
        return "news_aggregator"
    for pattern, key in URL_PLATFORM_MAP:
        if re.search(pattern, url, re.IGNORECASE):
            return key
    return "news_aggregator"


def parse_rss_items(xml_content, source="newsnow"):
    """Parse RSS 2.0 XML and return items with source info."""
    items = []
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        log(f"  RSS parse failed for {source}")
        return items

    for item_elem in root.findall('.//item'):
        title = ""
        title_elem = item_elem.find('title')
        if title_elem is not None and title_elem.text:
            title = title_elem.text.strip()

        link = ""
        link_elem = item_elem.find('link')
        if link_elem is not None and link_elem.text:
            link = link_elem.text.strip()

        pub_date = ""
        pub_date_elem = item_elem.find('pubDate')
        if pub_date_elem is not None and pub_date_elem.text:
            pub_date = pub_date_elem.text.strip()

        if not title or not link:
            continue

        platform = detect_platform(link)
        items.append({
            "title": title,
            "url": link,
            "pubDate": pub_date,
            "platform": platform,
        })

    return items


def fetch_newsnow_rss():
    """Fetch and parse newsnow RSS feed."""
    url = "https://news.zhinengtech.dpdns.org/api/feed.xml"
    log(f"Fetching newsnow RSS: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            log(f"  newsnow RSS: HTTP {resp.status_code}")
            return []
        items = parse_rss_items(resp.content)
        log(f"  newsnow RSS: {len(items)} items")
        return items
    except Exception as e:
        log(f"  newsnow RSS error: {e}")
        return []


def fetch_direct_rss():
    """Fetch supplementary direct RSS feeds."""
    all_items = []
    for key, name, feed_url, icon in SUPPLEMENTARY_RSS:
        try:
            log(f"  RSS {name}: {feed_url}")
            resp = requests.get(feed_url, headers=HEADERS, timeout=20)
            if resp.status_code != 200:
                log(f"    HTTP {resp.status_code}, skip")
                continue

            items = []
            try:
                root = ET.fromstring(resp.content)
                for item_elem in (root.findall('.//item') or root.findall('.//entry')):
                    title = ""
                    title_elem = item_elem.find('title')
                    if title_elem is not None and title_elem.text:
                        title = title_elem.text.strip()

                    link = ""
                    link_elem = item_elem.find('link')
                    if link_elem is not None:
                        link = link_elem.get('href', '') or link_elem.text or ''

                    if not title or not link:
                        continue

                    items.append({
                        "title": title, "url": link, "pubDate": "",
                        "platform": key,
                    })
                    if len(items) >= 10:
                        break
            except ET.ParseError:
                log(f"    XML parse failed, skip")
                continue

            for it in items:
                all_items.append(it)
            log(f"    {len(items)} items")
        except Exception as e:
            log(f"    Error: {e}")
            continue
    return all_items


def normalize_url(url):
    """Normalize URL for dedup: strip protocol, trailing slash, tracking params."""
    if not url:
        return ""
    parsed = urlparse(url)
    tracking = {'utm_source','utm_medium','utm_campaign','utm_term','utm_content','ref','from','cps_key','redirect','scene','source','tab'}
    clean_query = '&'.join(f'{k}={v}' for k, v in parse_qs(parsed.query).items() if k.lower() not in tracking)
    path = parsed.path.rstrip('/').lower() if parsed.path else ''
    host = parsed.netloc.lower()
    if clean_query:
        return f'{host}{path}?{clean_query}'
    return f'{host}{path}'


def clean_title(title):
    """Clean title for similarity matching."""
    t = re.sub(r'\s*[-–—|]\s*(36氪|知乎|B站|IT之家|华尔街见闻|今日头条|腾讯新闻|网易新闻|澎湃新闻|观察者网|创业邦|财联社|百度贴吧|贴吧|微博|抖音|V2EX|GitHub|HackerNews|ProductHunt).*$', '', title)
    t = re.sub(r'[^\w\一-鿿]', '', t)
    return t.strip().lower()[:50]


def dedup_items(items):
    """Two-stage dedup: URL merge + title similarity."""
    # Stage 1: URL-level merge
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

    # Stage 2: Title similarity within same platform
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


# ---- AI Processing (same prompts as original) ----

def call_zhipu(model, prompt, temperature=0.2):
    if not API_KEY:
        return None
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": temperature}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        return resp.json()['choices'][0]['message']['content']
    except Exception as e:
        log(f"  AI API Error: {e}")
        return None


def get_dual_language_data(title, content):
    prompt = f"""
    You are an expert intelligence analyst.

    Title: {title}
    Content: {content[:300]}

    TASKS:
    1. Score from 0-10 based on informational value to tech/business readers.
    2. Chinese summary (under 30 words).
    3. English summary (under 30 words).

    Return EXACTLY this JSON format:
    {{
      "score": <number>,
      "zh": {{"summary": "中文摘要"}},
      "en": {{"summary": "English Summary"}}
    }}
    """
    res = call_zhipu("glm-4-air", prompt)
    if not res:
        return None
    try:
        match = re.search(r'\{.*\}', res, re.DOTALL)
        return json.loads(match.group())
    except Exception:
        return None


def contains_chinese(text):
    return bool(re.search(r'[一-鿿]', text))


def baidu_translate(text):
    if not BAIDU_APP_ID or not BAIDU_SECRET_KEY:
        return None
    salt = str(random.randint(10000, 99999))
    sign = hashlib.md5((BAIDU_APP_ID + text + salt + BAIDU_SECRET_KEY).encode()).hexdigest()
    try:
        resp = requests.get("https://fanyi-api.baidu.com/api/trans/vip/translate", params={
            'q': text, 'from': 'en', 'to': 'zh',
            'appid': BAIDU_APP_ID, 'salt': salt, 'sign': sign
        }, timeout=10)
        data = resp.json()
        if 'trans_result' in data:
            return data['trans_result'][0]['dst']
    except Exception:
        pass
    return None


# ---- JSON Export ----

def categorize_item(title, platform):
    """Simple category assignment based on keywords."""
    title_lower = title.lower()
    if any(k in title_lower for k in ['ai', '人工智能', 'gpt', '模型', 'llm', '大模型', '机器学习', 'deep learning', 'neural']):
        return "AI模型"
    if any(k in title_lower for k in ['融资', '上市', 'ipo', '收购', '投资', '估值', '财报']):
        return "资本市场"
    if any(k in title_lower for k in ['iphone', '华为', '小米', 'oppo', 'vivo', '手机', '芯片', '半导体', '骁龙', '天玑']):
        return "消费电子"
    if any(k in title_lower for k in ['汽车', '新能源', '特斯拉', '比亚迪', '蔚来', '小鹏', '理想']):
        return "智能汽车"
    if any(k in title_lower for k in ['微信', '抖音', 'tiktok', '小红书', '快手', 'instagram', 'twitter']):
        return "社交平台"
    if any(k in title_lower for k in ['安全', '漏洞', '攻击', '勒索', '数据泄露', 'privacy']):
        return "安全"
    if any(k in title_lower for k in ['开源', 'github', 'docker', 'kubernetes', 'rust', 'python', 'javascript', 'react']):
        return "开源/开发者"
    if any(k in title_lower for k in ['腾讯云', '阿里云', 'aws', 'azure', 'cloud', '云服务']):
        return "云服务"
    return "其他"


def export_json(items, date_key):
    """Export items to zh/en JSON files."""
    zh_items = []
    en_items = []

    seen_ids = set()
    idx = 1
    for item in items:
        item_id = idx
        idx += 1
        platform = item.get('platform', 'news_aggregator')
        meta = PLATFORM_META.get(platform, {"label": platform, "color": "#94A3B8", "icon": "📌"})

        title = item.get('title', '')
        clean_desc = (item.get('desc', '') or item.get('ai_summary', '') or '').replace("摘要：", "").replace("Summary:", "").strip()
        zh_title = item.get('zh_title', '')
        en_title = item.get('en_title', '')

        base = {
            "id": item_id,
            "url": item.get('url', ''),
            "platform": platform,
            "platform_label": meta["label"],
            "platform_color": meta["color"],
            "platform_icon": meta["icon"],
            "hot": item.get('hot', 0),
            "date": date_key,
            "score": item.get('score', 0),
            "category": item.get('category', categorize_item(title, platform)),
        }

        zh_item = dict(base, title=zh_title or title, desc=clean_desc)
        en_item = dict(base, title=en_title or title, desc=item.get('en_summary', '') or clean_desc)

        if item.get('merged_sources'):
            zh_item['merged_sources'] = item['merged_sources']
            en_item['merged_sources'] = item['merged_sources']

        zh_items.append(zh_item)
        en_items.append(en_item)

    out_dir = OUT_BASE / "zh"
    out_dir.mkdir(exist_ok=True, parents=True)
    with open(out_dir / f"{date_key}.json", "w", encoding="utf-8") as f:
        json.dump({"date": date_key, "items": zh_items}, f, ensure_ascii=False, indent=2)
    log(f"  zh: {len(zh_items)} items exported")

    out_dir = OUT_BASE / "en"
    out_dir.mkdir(exist_ok=True, parents=True)
    with open(out_dir / f"{date_key}.json", "w", encoding="utf-8") as f:
        json.dump({"date": date_key, "items": en_items}, f, ensure_ascii=False, indent=2)
    log(f"  en: {len(en_items)} items exported")


# ---- Focus Generation ----

def generate_focus(items, date_key):
    """Generate today's focus using AI."""
    focus_dir = OUT_BASE
    scored = [it for it in items if it.get('score', 0) >= 5]
    scored.sort(key=lambda x: x['score'], reverse=True)
    top5 = scored[:5]

    if len(top5) < 3:
        log(f"  [Focus] insufficient data ({len(top5)} items), skip")
        fallback = {"date": date_key, "generated_at": datetime.now().isoformat(), "highlights": [], "trends": []}
        with open(focus_dir / "today-focus.json", "w", encoding="utf-8") as f:
            json.dump(fallback, f, ensure_ascii=False, indent=2)
        return

    items_text = "\n".join([
        f"{i+1}. [{it['platform']}] {it['title']} (评分:{it.get('score', 0)}) | {it.get('desc', '') or it.get('ai_summary', '') or '无摘要'} | 链接: {it.get('url', '') or '无'}"
        for i, it in enumerate(top5)
    ])

    prompt = f"""你是豆子实验室的首席编辑。分析以下今日情报,输出最有价值的发现。

今日情报列表（按AI评分排序）:
{items_text}

请以 JSON 格式返回（不要包含其他内容）:
{{
  "summary": "今日整体趋势一句话总结（20字以内）",
  "trendAnalysis": "今日趋势解读:分析今日资讯中占比最高的方向,值得关注的变化（60-100字,要有数据感,如'占比最高''环比上升''集中爆发'等。这段文字会直接展示给读者,要写得像编辑手记,有洞察力）",
  "highlights": [
    {{
      "rank": 1,
      "title": "原标题",
      "reason": "为什么重要（20字以内）",
      "insight": "深度解读或背后趋势（40字以内）",
      "summary": "浓缩原文要点生成一段60字以内的中文摘要",
      "source": "来源",
      "url": "原文链接"
    }}
  ],
  "trends": ["趋势关键词1", "趋势关键词2", "趋势关键词3"]
}}

要求:
- 选最重要的 5 条,不是评分最高的 5 条
- reason 写这条信息为什么对读者重要
- insight 写背后的含义或趋势信号
- trends 写 3 个今日最值得关注的关键词趋势
- trendAnalysis 要写得像编辑手记,有洞察力,不要套话
"""

    result = call_zhipu("glm-4-air", prompt)
    if result:
        try:
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                data = json.loads(match.group())
                data['date'] = date_key
                data['generated_at'] = datetime.now().isoformat()
                with open(focus_dir / "today-focus.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                log(f"  [Focus] {len(data.get('highlights', []))} highlights generated")
                return
        except Exception as e:
            log(f"  [Focus] parse error: {e}")

    log("  [Focus] AI failed, writing empty")
    fallback = {"date": date_key, "generated_at": datetime.now().isoformat(), "highlights": [], "trends": []}
    with open(focus_dir / "today-focus.json", "w", encoding="utf-8") as f:
        json.dump(fallback, f, ensure_ascii=False, indent=2)


# ---- Main ----

def collect_all():
    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz).strftime("%Y-%m-%d")
    log(f"=== RSS Collection: {today} (Asia/Shanghai) ===")

    # Step 1: Fetch all RSS sources
    all_items = []
    source_health = {}

    # 1a. newsnow RSS (primary)
    t0 = time.time()
    items = fetch_newsnow_rss()
    duration = int((time.time() - t0) * 1000)
    source_health['newsnow'] = {"status": "success", "items": len(items), "duration_ms": duration}

    # Limit per-platform for diversity
    platform_buckets = {}
    for it in items:
        p = it['platform']
        platform_buckets.setdefault(p, []).append(it)

    # Sort each bucket by pubDate descending, take top N
    limited = []
    platform_counts = {}
    for p, pitems in platform_buckets.items():
        pitems.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
        take = pitems[:PER_SOURCE_LIMIT]
        limited.extend(take)
        platform_counts[p] = len(take)
    log(f"  Per-source limits: {dict(sorted(platform_counts.items(), key=lambda x: -x[1]))}")

    # Sort all by pubDate descending, take MAX_TOTAL
    limited.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
    all_items = limited[:MAX_TOTAL]
    log(f"  After limiting: {len(all_items)} items (from {len(items)} raw)")

    # 1b. Supplementary RSS
    t0 = time.time()
    supp_items = fetch_direct_rss()
    supp_duration = int((time.time() - t0) * 1000)
    source_health['supplementary_rss'] = {"status": "success", "items": len(supp_items), "duration_ms": supp_duration}
    all_items.extend(supp_items)
    log(f"  Supplementary: {len(supp_items)} items")

    # Step 2: Mark items needing AI processing (no score yet)
    unprocessed = [it for it in all_items if it.get('score', 0) == 0]
    processed = [it for it in all_items if it.get('score', 0) > 0]
    log(f"  AI queue: {len(unprocessed)} new items, {len(processed)} already scored")

    # Step 3: AI scoring + summarization
    translate_usage = 0
    for item in unprocessed:
        title = item.get('title', '')
        desc = item.get('desc', '')
        log(f"  [AI] {title[:40]}...")
        dual = get_dual_language_data(title, desc)
        if isinstance(dual, dict):
            item['score'] = dual.get('score', 5) or 5
            zh = dual.get('zh', {})
            en = dual.get('en', {})
            if isinstance(zh, dict):
                item['ai_summary'] = zh.get('summary', '')
            if isinstance(en, dict):
                item['en_summary'] = en.get('summary', '')

        # Baidu translate for English titles
        if not contains_chinese(title):
            est = len(title) + 20
            if translate_usage + est <= DAILY_TRANSLATE_LIMIT:
                zh = baidu_translate(title)
                if zh and zh != title:
                    item['zh_title'] = zh
                    translate_usage += est
                    log(f"  [CN] {title[:30]} → {zh[:30]}")

        time.sleep(0.5)  # rate limit

    all_items = unprocessed + processed

    # Step 4: Dedup
    total_before = len(all_items)
    all_items = dedup_items(all_items)
    log(f"  Dedup: {total_before} → {len(all_items)} items")

    # Step 5: Sort by score descending
    all_items.sort(key=lambda x: x.get('score', 0), reverse=True)

    # Step 6: Export JSON
    log("Exporting JSON...")
    export_json(all_items, today)
    log(f"  Total: {len(all_items)} items")

    # Step 7: Source health
    health_out = OUT_BASE / "source-health.json"
    with open(health_out, "w", encoding="utf-8") as f:
        json.dump({"date": today, "sources": source_health}, f, ensure_ascii=False, indent=2)

    # Step 8: Generate today's focus
    log("Generating today's focus...")
    generate_focus(all_items, today)

    log(f"=== Finished: {len(all_items)} items ===")


if __name__ == "__main__":
    collect_all()
