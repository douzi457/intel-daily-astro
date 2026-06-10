#!/usr/bin/env python3
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

"""
dashboard_v4.py — 多源信息聚合看板 (采集+去重+翻译+评分+分类+推荐+摘要+HTML)
合并：horizon 的异步并发架构 + dashboard_v3 的 38 源 + 完整功能链

用法：python dashboard_v4.py
输出：output/dashboard.html  +  output/daily_recommend.md

依赖：pip install httpx feedparser    (已安装)
"""
import asyncio, json, os, re, sys, time, urllib.parse, html as html_mod
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Tuple, Any

import httpx
import feedparser

CST = timezone(timedelta(hours=8))
NOW_TS = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
TODAY = datetime.now(CST).strftime("%Y-%m-%d")
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = []  # [{category, name, type, count, items}]

# ====================================================================
# DATA MODEL
# ====================================================================
@dataclass
class NewsItem:
    title: str
    url: str
    summary: str = ""
    source: str = ""
    category: str = ""
    score: float = 0.0
    heat: Any = None
    title_cn: str = ""
    item_summary: str = ""  # generated summary for recommendation

    def to_dict(self):
        return asdict(self)


# ====================================================================
# CONFIG — 38 数据源 (from dashboard_v3)
# ====================================================================
# 每项：(category, name, type, url, extract_fn_or_None)
# type: 'rss' | 'json' | 'raw_json' | 'html' | 'special'

SOURCES = [
    # ── International Tech (16) ──
    ("International Tech", "Hacker News",     "rss",  "https://news.ycombinator.com/rss"),
    ("International Tech", "Techmeme",        "rss",  "https://www.techmeme.com/feed.xml"),
    ("International Tech", "Slashdot",        "rss",  "https://rss.slashdot.org/Slashdot/slashdotMain"),
    ("International Tech", "Engadget",        "rss",  "https://www.engadget.com/rss.xml"),
    ("International Tech", "HackerNoon",      "rss",  "https://hackernoon.com/feed"),
    ("International Tech", "TechCrunch",      "rss",  "https://techcrunch.com/feed/"),
    ("International Tech", "The Verge",       "rss",  "https://www.theverge.com/rss/index.xml"),
    ("International Tech", "Ars Technica",    "rss",  "https://feeds.arstechnica.com/arstechnica/index"),
    ("International Tech", "Wired",           "rss",  "https://www.wired.com/feed/rss"),
    ("International Tech", "Dev.to",          "rss",  "https://dev.to/feed"),
    ("International Tech", "Lobsters",        "rss",  "https://lobste.rs/rss"),
    ("International Tech", "Nature",          "rss",  "https://www.nature.com/nature.rss"),
    ("International Tech", "Science Daily",   "rss",  "https://www.sciencedaily.com/rss/top/science.xml"),
    ("International Tech", "MIT Tech Review", "rss",  "https://www.technologyreview.com/feed/"),
    ("International Tech", "BBC Tech",        "rss",  "https://feeds.bbci.co.uk/news/technology/rss.xml"),
    ("International Tech", "GitHub Trending", "github_trending",
     "https://github.com/trending?since=daily"),

    # ── International News (8) ──
    ("International News", "BBC World",       "rss", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("International News", "BBC News",        "rss", "https://feeds.bbci.co.uk/news/rss.xml"),
    ("International News", "The Guardian",    "rss", "https://www.theguardian.com/world/rss"),
    ("International News", "NYTimes Tech",    "rss", "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"),
    ("International News", "NYTimes World",   "rss", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    ("International News", "CBC World",       "rss", "https://www.cbc.ca/webfeed/rss/rss-world"),
    ("International News", "Euronews",        "rss", "https://www.euronews.com/rss"),
    ("International News", "NPR",             "rss", "https://feeds.npr.org/1001/rss.xml"),

    # ── Chinese Hot Search (4) ──
    ("Chinese Hot Search", "Baidu",   "raw_html", "https://top.baidu.com/board?tab=realtime"),
    ("Chinese Hot Search", "Douyin",  "json",
     "https://www.douyin.com/aweme/v1/web/hot/search/list/",
     lambda d: [{'title': i.get("word",""), 'heat': i.get("hot_value",0)}
                for i in d.get("data",{}).get("word_list",[])[:50]],
     {'Referer': 'https://www.douyin.com/'}),
    ("Chinese Hot Search", "Bilibili","json",
     "https://s.search.bilibili.com/main/hotword",
     lambda d: [{'title': i.get("keyword",""),
                 'url': f'https://search.bilibili.com/all?keyword={i.get("keyword","")}'}
                for i in d.get("list",[])[:30]]),
    ("Chinese Hot Search", "Zhihu",   "json",
     "https://www.zhihu.com/api/v3/feed/topstory/hot-list-web?limit=30&desktop=true",
     lambda d: [{'title': i.get("target",{}).get("title_area",{}).get("text",""),
                 'url': i.get("target",{}).get("link",{}).get("url",""),
                 'heat': i.get("target",{}).get("metrics_area",{}).get("text","")}
                for i in d.get("data",[])[:30] if isinstance(i,dict)],
     {'Referer': 'https://www.zhihu.com/'}),

    # ── Chinese News (3) ──
    ("Chinese News", "Toutiao",  "json",
     "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
     lambda d: [{'title': i.get("Title",""),
                 'url': f'https://www.toutiao.com/trending/{i.get("ClusterId","")}',
                 'heat': i.get("HotValue","")} for i in d.get("data",[])[:30]]),
    ("Chinese News", "Pengpai",  "raw_json",
     "https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar"),
    ("Chinese News", "Sputnik CN","html",
     "https://sputniknews.cn/services/widget/lenta/"),

    # ── Chinese Tech (4) ──
    ("Chinese Tech", "Juejin",   "json",
     "https://api.juejin.cn/content_api/v1/content/article_rank?category_id=1&type=hot",
     lambda d: [{'title': i.get("content",{}).get("title",""),
                 'url': f'https://juejin.cn/post/{i.get("content",{}).get("content_id","")}'}
                for i in d.get("data",[])[:20]]),
    ("Chinese Tech", "ifanr",    "rss", "https://www.ifanr.com/feed"),
    ("Chinese Tech", "InfoQ CN", "rss", "https://www.infoq.cn/feed"),
    ("Chinese Tech", "QbitAI",   "rss", "https://www.qbitai.com/feed"),

    # ── AI/Frontier (1) ──
    ("AI/Frontier", "AI Hot", "json",
     "https://aihot.virxact.com/api/public/items?limit=30",
     lambda d: [{'title': i.get("title",""), 'url': i.get("url","")}
                for i in (d.get("data") or d.get("items") or [])[:30]]),

    # ── Finance (2) ──
    ("Finance", "WallstreetCN Hot", "json",
     "https://api-one.wallstcn.com/apiv1/content/articles/hot?period=day&limit=20",
     lambda d: [{'title': i.get("title",""), 'url': i.get("uri","")}
                for i in d.get("data",{}).get("day_items",[])[:20]]),
    ("Finance", "WallstreetCN Live","json",
     "https://api-one.wallstcn.com/apiv1/content/lives?limit=20&channel=global",
     lambda d: [{'title': i.get("title",""), 'url': ''}
                for i in (d if isinstance(d,list) else
                          d.get("data",[]) if isinstance(d.get("data"),list) else
                          d.get("data",{}).get("items",[]))[:20]]),

    # ── Community (2) ──
    ("Community", "Tieba", "json",
     "https://tieba.baidu.com/hottopic/browse/topicList",
     lambda d: [{'title': i.get("topic_name",""),
                 'url': f'https://tieba.baidu.com/hottopic/browse?topic_id={i.get("topic_id","")}',
                 'heat': i.get("discuss_num","")}
                for i in d.get("data",{}).get("bang_topic",{}).get("topic_list",[])[:30]]),
    ("Community", "Nowcoder","json",
     f'https://gw-c.nowcoder.com/api/sparta/hot-search/top-hot-pc?page=1&size=20&_={int(time.time()*1000)}',
     lambda d: [{'title': i.get("title",""),
                 'url': i.get("router",{}).get("url","") if isinstance(i.get("router"),dict) else ''}
                for i in d.get("data",{}).get("result",[])[:20]]),

    # ── New Sources: V2EX, Reddit, Twitter, etc. ──
    ("Community", "V2EX Hot", "json",
     "https://www.v2ex.com/api/topics/hot.json",
     lambda d: [{'title': i.get("title",""),
                 'url': f'https://www.v2ex.com/t/{i.get("id","")}',
                 'heat': i.get("replies",0)}
                for i in (d if isinstance(d,list) else [])[:30]]),

    ("Community", "Reddit Hot", "json",
     "https://www.reddit.com/r/all/hot/.json?limit=25",
     lambda d: [{'title': i.get("data",{}).get("title",""),
                 'url': f'https://www.reddit.com{i.get("data",{}).get("permalink","")}',
                 'heat': i.get("data",{}).get("score",0)}
                for i in d.get("data",{}).get("children",[])[:25]],
     {'User-Agent': 'intel-daily-astro/1.0'}),

    ("Community", "Twitter Hot (Sopilot)", "rss",
     "https://sopilot.net/rss/hottweets"),

    ("Chinese Hot Search", "Weibo", "json",
     "https://weibo.com/ajax/side/hotSearch",
     lambda d: [{'title': i.get("word",""),
                 'url': f'https://s.weibo.com/weibo?q={i.get("word","")}',
                 'heat': i.get("raw_hot",0)}
                for i in d.get("data",{}).get("realtime",[])[:30]],
     {'Referer': 'https://weibo.com/', 
      'Cookie': 'SUB=_2AkMSEic0f8NxqwJRmPoRyGjmaoV-zg7EieKiRMrFJRMxHRl-yT9kqmMtRBGFaUsfX6dYIx7b3vjyFGT6FAUquV8gJCiq'}),

    ("Chinese Tech", "IT之家", "rss",
     "https://api.ithome.com/rss/news"),

    ("Chinese Tech", "36氪", "rss",
     "https://36kr.com/feed"),
]


# ====================================================================
# UTILITIES
# ====================================================================

def add(cat: str, name: str, dtype: str, items: list):
    items = [i for i in items if i.get("title")]
    OUT.append({"category": cat, "name": name, "type": dtype,
                "count": len(items), "items": items})


async def fetch_async(client: httpx.AsyncClient, url: str, timeout: int = 20,
                      extra_headers: dict = None) -> Optional[str]:
    """Async HTTP GET with retry"""
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
        "Accept": "application/json, application/rss+xml, text/html, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if extra_headers:
        headers.update(extra_headers)
    for attempt in range(3):
        try:
            resp = await client.get(url, headers=headers, timeout=timeout, follow_redirects=True)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 429:
                await asyncio.sleep(3 * (attempt + 1))
                continue
        except:
            await asyncio.sleep(2)
    return None


def parse_rss(body: str) -> list:
    """Parse RSS via feedparser, fallback to regex"""
    feed = feedparser.parse(body)
    items = []
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        if not title:
            continue
        link = entry.get("link", "")
        items.append({"title": html_mod.unescape(title), "url": link})
    if items:
        return items
    # Fallback: regex
    return parse_rss_regex(body)


def parse_rss_regex(body: str) -> list:
    items = []
    try:
        root = ET.fromstring(body)
        for tag, ns in [("item", None), (None, "http://www.w3.org/2005/Atom"),
                         (None, "http://purl.org/rss/1.0/")]:
            if tag:
                for el in root.iter(tag):
                    t = el.find("title")
                    l = el.find("link")
                    txt = (t.text or "").strip() if t is not None and t.text else ""
                    lnk = (l.text or "").strip() if l is not None and l.text else ""
                    if txt:
                        items.append({"title": html_mod.unescape(txt), "url": lnk})
            elif ns:
                qtag = f"{{{ns}}}entry" if "Atom" in ns else f"{{{ns}}}item"
                qt = f"{{{ns}}}title"
                ql = f"{{{ns}}}link"
                for el in root.iter(qtag):
                    t = el.find(qt)
                    l = el.find(ql)
                    txt = (t.text or "").strip() if t is not None and t.text else ""
                    lnk = ""
                    if l is not None:
                        lnk = l.attrib.get("href", (l.text or "").strip())
                    if "Atom" in ns and l is not None:
                        lnk = l.attrib.get("href", lnk)
                    if txt:
                        items.append({"title": html_mod.unescape(txt), "url": lnk})
            if items:
                break
    except:
        ts = re.findall(r"<title>(.*?)</title>", body)[1:]
        ls = re.findall(r"<link>(.*?)</link>", body)
        items = [{"title": html_mod.unescape(t.strip()), "url": l.strip()}
                 for t, l in zip(ts, ls) if t.strip()]
    return items


# ====================================================================
# PHASE 1: CONCURRENT COLLECTION (async)
# ====================================================================

async def fetch_rss_source(client: httpx.AsyncClient, cat: str, name: str, url: str, limit: int = 15):
    body = await fetch_async(client, url)
    if body:
        items = parse_rss(body)
        add(cat, name, "RSS", items[:limit])
        return len(items[:limit])
    return 0


async def fetch_json_source(client: httpx.AsyncClient, cat: str, name: str, url: str,
                            extract_fn, limit: int = 30, extra_headers: dict = None):
    body = await fetch_async(client, url, extra_headers=extra_headers)
    if body:
        try:
            data = json.loads(body)
            items = extract_fn(data)[:limit]
            add(cat, name, "JSON", items)
            return len(items)
        except Exception:
            pass
    return 0


async def fetch_raw_json(client: httpx.AsyncClient, cat: str, name: str, url: str, limit: int = 30):
    """JSON source with nested traversing (Pengpai)"""
    body = await fetch_async(client, url)
    if body:
        try:
            j = json.loads(body)
            items = []
            data = j.get("data", {})
            if isinstance(data, dict):
                for sec in data.values():
                    if isinstance(sec, list):
                        for it in sec:
                            if isinstance(it, dict) and (it.get("title") or it.get("name")):
                                items.append({
                                    "title": it.get("title") or it.get("name", ""),
                                    "url": f'https://www.thepaper.cn/newsDetail_forward_{it.get("contId","")}'
                                })
            add(cat, name, "JSON", items[:limit])
            return len(items[:limit])
        except:
            pass
    return 0


async def fetch_html_source(client: httpx.AsyncClient, cat: str, name: str, url: str, limit: int = 20):
    """HTML parsed source (Sputnik CN)"""
    body = await fetch_async(client, url)
    if body:
        texts = re.findall(r'lenta__item-text[^>]*>([^<]+)<', body)
        links = re.findall(r'href="(/\d+/\d+\.html)"', body)
        items = [{"title": html_mod.unescape(t.strip()),
                  "url": f"https://sputniknews.cn{u}"}
                 for t, u in zip(texts, links)][:limit]
        add(cat, name, "HTML", items)
        return len(items)
    return 0


async def fetch_baidu(client: httpx.AsyncClient, cat: str, name: str, url: str, limit: int = 30):
    """Baidu hot search (extract from <!--s-data:-->)"""
    body = await fetch_async(client, url)
    if body:
        m = re.search(r'<!--s-data:(.*?)-->', body, re.DOTALL)
        if m:
            try:
                cards = json.loads(m.group(1)).get("data", {}).get("cards", [{}])[0].get("content", [])
                items = [{"title": c.get("word", ""), "url": c.get("url", ""),
                          "heat": c.get("hotScore", "")} for c in cards[:limit]]
                add(cat, name, "JSON", items)
                return len(items)
            except:
                pass
    return 0


async def fetch_github_trending(client: httpx.AsyncClient, cat: str, name: str, url: str, limit: int = 15):
    """Scrape GitHub Trending page for repos with daily star gain"""
    body = await fetch_async(client, url, extra_headers={
        "Accept": "text/html,application/xhtml+xml",
    })
    if not body:
        return 0

    items = []
    # Split by article tags (GitHub Trending uses Box-row class)
    articles = re.findall(
        r'<article[^>]*class="Box-row[^"]*"[^>]*>(.*?)</article>',
        body, re.DOTALL | re.IGNORECASE
    )

    for art in articles[:limit]:
        # Extract repo owner/name
        m = re.search(r'href="/([^"/]+/[^"/]+?)"', art)
        if not m:
            continue
        full_name = m.group(1)

        # Extract description
        desc_m = re.search(r'<p[^>]*>(.*?)</p>', art, re.DOTALL)
        desc = re.sub(r'<[^>]+>', '', desc_m.group(1)).strip() if desc_m else ""
        desc = html_mod.unescape(desc)

        # Extract stars today
        stars_m = re.search(r'(\d[\d,]*)\s*stars?\s*today', art, re.IGNORECASE)
        stars_today = int(stars_m.group(1).replace(',', '')) if stars_m else 0

        title = f'{full_name} - {desc[:80]}' if desc else full_name

        items.append({
            'title': title.strip(),
            'url': f'https://github.com/{full_name}',
            'heat': stars_today,
        })

    add(cat, name, "trending", items)
    return len(items)


async def collect_all():
    """Phase 1: Fetch all sources concurrently"""
    print("=== PHASE 1: Concurrent Collection ===", flush=True)
    print("  Creating async HTTP client...", flush=True)

    tasks = []
    conn = httpx.AsyncClient(limits=httpx.Limits(max_keepalive_connections=20, max_connections=30), timeout=httpx.Timeout(25.0))

    async with conn as client:
        for entry in SOURCES:
            cat, name, stype, url = entry[0], entry[1], entry[2], entry[3]

            if stype == "rss":
                tasks.append(fetch_rss_source(client, cat, name, url))

            elif stype == "json":
                extract_fn = entry[4]
                extra_hdrs = entry[5] if len(entry) > 5 else None
                tasks.append(fetch_json_source(client, cat, name, url, extract_fn,
                                                extra_headers=extra_hdrs))

            elif stype == "raw_json":
                tasks.append(fetch_raw_json(client, cat, name, url))

            elif stype == "html":
                tasks.append(fetch_html_source(client, cat, name, url))

            elif stype == "raw_html" and name == "Baidu":
                tasks.append(fetch_baidu(client, cat, name, url))

            elif stype == "github_trending":
                tasks.append(fetch_github_trending(client, cat, name, url))

            print(f"  Queued: [{cat}] {name}", flush=True)

        print(f"  Executing {len(tasks)} concurrent fetches...", flush=True)
        results = await asyncio.gather(*tasks, return_exceptions=True)

    ok_count = sum(1 for r in results if isinstance(r, int) and r > 0)
    total_items = sum(r for r in results if isinstance(r, int))
    print(f"\n  Done: {ok_count}/{len(SOURCES)} sources, {total_items} items", flush=True)
    return ok_count, total_items


# ====================================================================
# PHASE 2: DEDUP
# ====================================================================
def normalize(s: str) -> str:
    return re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbfa-zA-Z0-9]', '', s).lower()[:80]


def is_similar(a: str, b: str, threshold: float = 0.75) -> bool:
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    sa = set(a[i:i+2] for i in range(len(a)-1))
    sb = set(b[i:i+2] for i in range(len(b)-1))
    if not sa or not sb:
        return False
    return len(sa & sb) / len(sa | sb) > threshold


def deduplicate():
    """Phase 2: Per-source + cross-source dedup"""
    print("\n=== PHASE 2: Deduplication ===")

    raw_total = sum(s["count"] for s in OUT)

    # Per-source
    for s in OUT:
        seen = set()
        deduped = []
        for item in s["items"]:
            n = normalize(item["title"])
            if n and n not in seen:
                seen.add(n)
                deduped.append(item)
        s["items"] = deduped
        s["count"] = len(deduped)

    # Cross-source
    all_items = []
    for s in OUT:
        for item in s["items"]:
            all_items.append({**item, "source": s["name"], "category": s["category"]})

    final = []
    for item in all_items:
        dup = False
        for ex in final[-50:]:
            if is_similar(item["title"], ex["title"]):
                dup = True
                break
        if not dup:
            final.append(item)

    print(f"  Raw: {raw_total} -> Per-source: {len(all_items)} -> Cross-dedup: {len(final)}")
    return final


# ====================================================================
# PHASE 3: TRANSLATION
# ====================================================================
def translate_one(text: str) -> str:
    """Google Translate via URL API (httpx, no curl.exe)"""
    try:
        encoded = urllib.parse.quote(text[:300])
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh-CN&dt=t&q={encoded}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code == 200:
                body = resp.text
                j = json.loads(body)
                result = "".join([s[0] for s in j[0] if s[0]]) if j and j[0] else text
                return result.strip() if result.strip() else text
    except:
        pass
    return text


def translate_titles(final: list):
    """Phase 3: Translate English titles to Chinese"""
    print("\n=== PHASE 3: Translation ===")

    to_translate = []
    seen_t = set()
    for item in final:
        t = item["title"]
        zh = sum(1 for c in t if '\u4e00' <= c <= '\u9fff' or '\u3400' <= c <= '\u4dbf')
        if zh <= len(t) * 0.3 and len(t) >= 3 and t not in seen_t:
            seen_t.add(t)
            to_translate.append(t)

    print(f"  English titles to translate: {len(to_translate)}")
    cache = {}

    if to_translate:
        done = 0
        total = len(to_translate)
        with ThreadPoolExecutor(max_workers=12) as pool:
            futures = {pool.submit(translate_one, t): t for t in to_translate}
            for f in as_completed(futures):
                orig = futures[f]
                try:
                    cache[orig] = f.result()
                except:
                    cache[orig] = orig
                done += 1
                if done % 50 == 0:
                    print(f"    {done}/{total}")
        print(f"    {done}/{total} done")

    for item in final:
        item["title_cn"] = cache.get(item["title"], item["title"])

    return cache


# ====================================================================
# PHASE 4: SCORING
# ====================================================================
TECH_KEYWORDS = {
    "AI": 3, "人工智能": 3, "GPT": 3, "Claude": 3, "DeepSeek": 3, "LLM": 3,
    "苹果": 2, "Apple": 2, "华为": 2, "Huawei": 2, "小米": 2, "Xiaomi": 2,
    "特斯拉": 2, "Tesla": 2, "新能源": 1.5, "电动车": 1.5,
    "GitHub": 2, "开源": 1.5, "编程": 1.5, "代码": 1,
    "芯片": 2, "GPU": 2, "NVIDIA": 2, "显卡": 1.5,
    "手机": 1.5, "笔记本": 1.5, "电脑": 1, "数码": 1.5,
    "游戏": 1, "电竞": 1, "Steam": 1.5,
    "机器人": 2, "无人机": 1.5, "自动驾驶": 2,
    "VR": 1.5, "AR": 1.5, "元宇宙": 1,
    "ChatGPT": 3, "大模型": 2.5, "Agent": 2,
}

CATEGORY_WEIGHTS = {
    "AI/Frontier": 1.5, "Chinese Tech": 1.3, "International Tech": 1.2,
    "Chinese Hot Search": 0.8, "Finance": 0.9, "Community": 0.7,
    "Chinese News": 0.6, "International News": 0.5,
}

TECH_SOURCES = {"Hacker News", "GitHub Trending", "AI Hot",
                "TechCrunch", "The Verge", "MIT Tech Review"}


def calc_score(item: dict) -> float:
    """科技自媒体向评分 (0-10)
    改进：按类别设基础分（重要类别即使无关键词也不会被埋没）
    """
    # 类别基础分（重要类别起点高，噪音类别起点低）
    CATEGORY_BASELINE = {
        "AI/Frontier": 7.0,
        "Chinese Tech": 6.0,
        "International Tech": 6.0,
        "Chinese Hot Search": 3.0,  # 热搜含大量娱乐八卦
        "Chinese News": 4.0,
        "International News": 5.0,
        "Finance": 5.0,
        "Community": 3.0,  # 贴吧/牛客噪音多
    }
    cat = item.get("category", "")
    score = CATEGORY_BASELINE.get(cat, 5.0)

    # 关键词加分（命中即加，不重复覆盖）
    title = item.get("title_cn", item["title"])
    keyword_bonus = 0
    for kw, weight in TECH_KEYWORDS.items():
        if kw.lower() in title.lower():
            keyword_bonus = max(keyword_bonus, weight)
    score += min(keyword_bonus, 3)

    # 热度加分
    heat = item.get("heat", 0)
    if isinstance(heat, str):
        heat = re.sub(r'[^\d]', "", heat)
        heat = int(heat) if heat else 0
    if heat >= 5_000_000:
        score += 2
    elif heat >= 1_000_000:
        score += 1.5
    elif heat >= 500_000:
        score += 1
    elif heat >= 100_000:
        score += 0.5

    # 优质来源加分
    source = item.get("source", "")
    if source in TECH_SOURCES:
        score += 1

    return round(min(max(score, 0), 10), 1)


def score_items(final: list):
    """Phase 4: Score all items"""
    print("\n=== PHASE 4: Scoring ===")
    for item in final:
        item["score"] = calc_score(item)
    final.sort(key=lambda x: x["score"], reverse=True)
    print(f"  Scored {len(final)} items")


# ====================================================================
# PHASE 5: CLASSIFICATION + RECOMMENDATIONS
# ====================================================================
CATEGORY_RULES = {
    "AI/大模型": ["ai", "人工智能", "gpt", "claude", "deepseek", "llm",
                  "大模型", "agent", "chatgpt", "大语言模型"],
    "数码/硬件": ["苹果", "apple", "华为", "huawei", "小米", "xiaomi",
                  "特斯拉", "tesla", "手机", "芯片", "gpu", "nvidia",
                  "显卡", "笔记本", "数码"],
    "开源/工具": ["github", "开源", "工具", "库", "框架", "api", "sdk"],
}


def classify_item(item: dict) -> Optional[str]:
    title = item.get("title_cn", item["title"]).lower()
    source = item.get("source", "")
    cat = item.get("category", "")

    for direction, keywords in CATEGORY_RULES.items():
        if any(kw in title for kw in keywords):
            return direction

    if source == "GitHub Trending":
        return "开源/工具"
    if cat in ("International Tech", "Chinese Tech") or source in ("Hacker News", "TechCrunch", "The Verge"):
        return "科技热点"
    if cat == "Finance" or any(kw in title for kw in ("融资", "ipo", "投资", "营收", "市值")):
        return "财经/商业"
    return None


def build_recommendations(final: list):
    """Phase 5: Categorize items into 5 recommendation directions"""
    print("\n=== PHASE 5: Classification ===")

    candidates = {
        "AI/大模型": [], "数码/硬件": [], "开源/工具": [],
        "科技热点": [], "财经/商业": [],
    }

    for item in final:
        cat = classify_item(item)
        if cat and item.get("url") and len(candidates[cat]) < 20:
            candidates[cat].append(item)

    print(f"  Candidates: {sum(len(v) for v in candidates.values())} items")
    return candidates


# ====================================================================
# PHASE 6: SUMMARY GENERATION
# ====================================================================
def extract_text_from_html(html_content: str) -> str:
    """Extract clean text from HTML, targeting article/main content"""
    html_content = re.sub(r'<script[^>]*>.*?</script>', "", html_content,
                          flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<style[^>]*>.*?</style>', "", html_content,
                          flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<nav[^>]*>.*?</nav>', "", html_content,
                          flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<header[^>]*>.*?</header>', "", html_content,
                          flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<footer[^>]*>.*?</footer>', "", html_content,
                          flags=re.DOTALL | re.IGNORECASE)

    article_match = re.search(r'<article[^>]*>(.*?)</article>', html_content,
                              flags=re.DOTALL | re.IGNORECASE)
    if article_match:
        html_content = article_match.group(1)
    else:
        main_match = re.search(r'<main[^>]*>(.*?)</main>', html_content,
                               flags=re.DOTALL | re.IGNORECASE)
        if main_match:
            html_content = main_match.group(1)
        else:
            content_match = re.search(
                r'<div[^>]*class="[^"]*(?:content|article|post|entry)[^"]*"[^>]*>(.*?)</div>',
                html_content, flags=re.DOTALL | re.IGNORECASE)
            if content_match:
                html_content = content_match.group(1)

    text = re.sub(r'<[^>]+>', " ", html_content)
    text = html_mod.unescape(text)
    text = re.sub(r'\s+', " ", text)
    # ── 砍掉常见 UI 垃圾文本 ──
    text = re.sub(
        r'(?:'
        r'关闭[。，]?\s*此主题[^。]*帖子[^。]*添加到[^。]*邮件[^。]*摘要[^。]*提要|'
        r'添加到你的每日|添加到您的每日|'
        r'此主题的[^。]*帖子将[^。]*添加到|'
        r'查看所有[^。]*|查看全部[^。]*|'
        r'关闭[。，]?[^。]*此主题[^。]*|'
        r'此主题的[^。]*(?:游戏|娱乐|新闻|科技)[^。]*|'
        r'关注[。，]?\s*关注|Follow\s+关注|'
        r'Skip to content|Skip to main content|'
        r'Navigation Menu|Toggle navigation|'
        r'Sign in|Log in|Subscribe Now|Read more stories|'
        r'Theme[^。]*Light|Theme[^。]*Dark|'
        r'Privacy[^。]*Cookies|Cookie[^。]*Settings|'
        r')', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _zhipu_summary(title: str, text: str, api_key: str) -> Optional[str]:
    """Use ZHIPU GLM-4-Flash to generate a concise Chinese summary (1-2 sentences)"""
    prompt = f"""你是一个科技资讯编辑。请用1-2句中文简洁概括以下科技资讯的核心看点。
不要评价"值得关注"这类废话，直接说这条资讯讲了什么。

标题：{title}
内容摘要：{text[:800]}

中文概括（1-2句）："""
    try:
        resp = httpx.post(
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "GLM-4-Flash",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 150,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            summary = resp.json()["choices"][0]["message"]["content"].strip()
            summary = summary.strip('\"').strip("'")
            if summary and len(summary) > 10:
                zh = sum(1 for c in summary if '\u4e00' <= c <= '\u9fff')
                if zh >= len(summary) * 0.3:
                    return summary[:200]
    except:
        pass
    return None


def _fallback_summary_from_page(url: str, title: str) -> Optional[str]:
    """Fallback: fetch page, extract first sentences, translate if needed"""
    if not url:
        return None
    body = None
    try:
        with httpx.Client(timeout=25, follow_redirects=True) as client:
            resp = client.get(url, headers={
                "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            })
            if resp.status_code == 200:
                body = resp.text
    except:
        pass
    if not body:
        return None

    text = extract_text_from_html(body)
    if len(text) < 100:
        return None
    text = text[:3000]

    sentences = re.split(r'[。！？.!?]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if len(sentences) >= 3:
        summary = "。".join(sentences[:3]) + "。"
    elif len(sentences) >= 2:
        summary = "。".join(sentences[:2]) + "。"
    elif len(sentences) == 1:
        summary = sentences[0]
    else:
        summary = text[:150]

    zh_count = sum(1 for c in summary if '\u4e00' <= c <= '\u9fff')
    if zh_count < len(summary) * 0.7 and len(summary) > 20:
        try:
            with httpx.Client(timeout=15) as c2:
                encoded = urllib.parse.quote(summary[:300])
                resp2 = c2.get(
                    f"https://translate.googleapis.com/translate_a/single?"
                    f"client=gtx&sl=auto&tl=zh-CN&dt=t&q={encoded}",
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                if resp2.status_code == 200:
                    body_tr = resp2.text
                    j = json.loads(body_tr)
                    translated = "".join([s[0] for s in j[0] if s[0]]) if j and j[0] else summary
                    if translated.strip():
                        summary = translated.strip()
                        zh_after = sum(1 for c in summary if '\u4e00' <= c <= '\u9fff')
                        if zh_after < len(summary) * 0.5:
                            return None
        except:
            return None

    # ── 再次清洗垃圾 UI 文本 ──
    GARBAGE_UI = [
        '关闭', '此主题', '添加到', '电子邮件', '摘要', '提要',
        '查看所有', '查看全部', 'Skip to', 'Navigation', 'Toggle',
        'Sign in', 'Log in', 'Subscribe', 'Cookie', 'Privacy',
        'Follow', '关注', '关注关注',
    ]
    garbage_count = sum(1 for g in GARBAGE_UI if g.lower() in summary.lower())
    if garbage_count >= 3:
        return None

    final_zh = sum(1 for c in summary if '\u4e00' <= c <= '\u9fff')
    if final_zh < len(summary) * 0.5:
        return None
    return summary[:200]


def generate_summary(url: str, title: str, api_key: str = "") -> Optional[str]:
    """Generate a concise Chinese summary. Prefers ZHIPU AI, falls back to page extraction + translation."""
    if not url:
        return None
    body = None
    try:
        with httpx.Client(timeout=25, follow_redirects=True) as client:
            resp = client.get(url, headers={
                "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            })
            if resp.status_code == 200:
                body = resp.text
    except:
        pass
    if not body:
        return None

    text = extract_text_from_html(body)
    if len(text) < 100:
        return None

    # Method 1: ZHIPU API (if key available)
    if api_key:
        result = _zhipu_summary(title, text[:800], api_key)
        if result:
            return result

    # Method 2: Fallback to page extraction + translation
    text_full = text[:3000]
    sentences = re.split(r'[。！？.!?]', text_full)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if len(sentences) >= 3:
        summary = "。".join(sentences[:3]) + "。"
    elif len(sentences) >= 2:
        summary = "。".join(sentences[:2]) + "。"
    elif len(sentences) == 1:
        summary = sentences[0]
    else:
        summary = text_full[:150]

    zh = sum(1 for c in summary if '\u4e00' <= c <= '\u9fff')
    if zh < len(summary) * 0.7 and len(summary) > 20:
        try:
            with httpx.Client(timeout=15) as c2:
                encoded = urllib.parse.quote(summary[:300])
                resp2 = c2.get(
                    f"https://translate.googleapis.com/translate_a/single?"
                    f"client=gtx&sl=auto&tl=zh-CN&dt=t&q={encoded}",
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                if resp2.status_code == 200:
                    body_tr = resp2.text
                    j = json.loads(body_tr)
                    translated = "".join([s[0] for s in j[0] if s[0]]) if j and j[0] else summary
                    if translated.strip():
                        summary = translated.strip()
                        zh2 = sum(1 for c in summary if '\u4e00' <= c <= '\u9fff')
                        if zh2 < len(summary) * 0.5:
                            return None
        except:
            return None

    # ── 再次清洗垃圾 UI 文本 ──
    GARBAGE_UI = [
        '关闭', '此主题', '添加到', '电子邮件', '摘要', '提要',
        '查看所有', '查看全部', 'Skip to', 'Navigation', 'Toggle',
        'Sign in', 'Log in', 'Subscribe', 'Cookie', 'Privacy',
        'Follow', '关注', '关注关注',
    ]
    garbage_count = sum(1 for g in GARBAGE_UI if g.lower() in summary.lower())
    if garbage_count >= 3:
        return None

    final_zh = sum(1 for c in summary if '\u4e00' <= c <= '\u9fff')
    if final_zh < len(summary) * 0.5:
        return None
    return summary[:200]


def generate_summaries(candidates: dict):
    """Phase 6: Generate summaries for recommendation candidates"""
    print("\n=== PHASE 6: Summary Generation ===")

    api_key = os.environ.get("ZHIPU_API_KEY", "").strip()
    if api_key:
        print(f"  Using ZHIPU API (GLM-4-Flash) for AI-powered summaries")
    else:
        print(f"  No ZHIPU_API_KEY found, using fallback (page extraction + translate)")

    count = 0
    total = sum(len(items) for items in candidates.values())
    done = 0
    for cat, items in candidates.items():
        for item in items:
            url = item.get("url", "")
            title = item.get("title_cn", item["title"])
            summary = generate_summary(url, title, api_key)
            if summary:
                item["summary"] = summary
                count += 1
            else:
                item["summary"] = None
            done += 1
            if done % 5 == 0:
                print(f"    Summaries: {done}/{total} (valid: {count})", flush=True)

    print(f"  Summaries generated: {count}/{total}")
    return count


def select_recommendations(candidates: dict) -> dict:
    """Select top 5 per category with summaries, fill gaps with high-score items"""
    recommendations = {k: [] for k in candidates}

    all_valid = []
    for cat, items in candidates.items():
        for item in items:
            if item.get("summary"):
                all_valid.append({**item, "original_category": cat})
    all_valid.sort(key=lambda x: x["score"], reverse=True)

    used_ids = set()
    for cat in recommendations:
        cat_items = [it for it in all_valid
                     if it["original_category"] == cat and id(it) not in used_ids]
        for item in cat_items[:5]:
            recommendations[cat].append(item)
            used_ids.add(id(item))

    remaining = [it for it in all_valid if id(it) not in used_ids]
    for _ in range(25):
        need = {k: 5 - len(v) for k, v in recommendations.items() if len(v) < 5}
        if not need or not remaining:
            break
        for cat in need:
            while len(recommendations[cat]) < 5 and remaining:
                recommendations[cat].append(remaining.pop(0))

    final_count = sum(len(v) for v in recommendations.values())
    print(f"  Final recommendations: {final_count} items")
    return recommendations


# ====================================================================
# PHASE 7: OUTPUT
# ====================================================================
def e(s): return html_mod.escape(str(s)) if s else ""


def generate_markdown(recommendations: dict, final: list):
    """Generate daily_recommend.md"""
    outdir = os.path.join(BASE, "output")
    os.makedirs(outdir, exist_ok=True)

    md_path = os.path.join(outdir, "daily_recommend.md")
    md_lines = [f"# 每日科技推荐 - {NOW_TS}", ""]
    md_lines.append(f"> 共推荐 {sum(len(v) for v in recommendations.values())} 条，全部包含简介")
    md_lines.append("")

    for cat, items in recommendations.items():
        if items:
            md_lines.append(f"## {cat}")
            md_lines.append("")
            for i, item in enumerate(items, 1):
                title = item.get("title_cn", item["title"])
                url = item.get("url", "")
                score = item["score"]
                source = item.get("source", "")
                summary = item.get("summary", "")
                if url:
                    md_lines.append(f'{i}. **[{score:.1f}]** [{title}]({url}) - {source}')
                else:
                    md_lines.append(f'{i}. **[{score:.1f}]** {title} - {source}')
                if summary:
                    md_lines.append(f"   > {summary}")
                md_lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"  Markdown: {md_path}")


def generate_html(recommendations: dict, final: list):
    """Generate dashboard.html"""
    outdir = os.path.join(BASE, "output")
    os.makedirs(outdir, exist_ok=True)

    cat_colors = {
        "Chinese Hot Search": "#e74c3c", "Chinese News": "#e67e22",
        "Chinese Tech": "#9b59b6", "AI/Frontier": "#00bcd4",
        "Finance": "#f39c12", "Community": "#2ecc71",
        "International Tech": "#3498db", "International News": "#1abc9c",
    }
    active_sources = [s for s in OUT if s["count"] > 0]

    cats = {}
    for item in final:
        c = item["category"]
        cats.setdefault(c, []).append(item)

    rec_count = sum(len(v) for v in recommendations.values())
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="zh-CN">',
        '<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">',
        f'<title>Info Dashboard - {NOW_TS}</title>',
        ('<style>'
         '*{margin:0;padding:0;box-sizing:border-box}'
         'body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:#f0f2f5;color:#2c3e50}'
         '.header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:30px 20px;text-align:center}'
         '.header h1{font-size:1.8em;margin-bottom:5px}'
         '.header .meta{opacity:.85;font-size:.9em}'
         '.container{max-width:1400px;margin:0 auto;padding:20px}'
         '.recommend{background:#fff;border-radius:10px;padding:20px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,.05)}'
         '.recommend h2{color:#667eea;margin-bottom:15px;font-size:1.3em}'
         '.recommend-section{margin-bottom:20px}'
         '.recommend-section h3{color:#333;margin-bottom:10px;font-size:1.1em;border-bottom:1px solid #eee;padding-bottom:5px}'
         '.recommend-item{padding:12px;border-bottom:1px solid #eee}'
         '.recommend-item:last-child{border-bottom:none}'
         '.score{display:inline-block;background:#667eea;color:#fff;padding:2px 8px;border-radius:3px;font-size:.85em;margin-right:8px}'
         '.summary{color:#666;font-size:.9em;margin-top:8px;padding-left:10px;border-left:3px solid #667eea;font-style:italic}'
         '.stats{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px}'
         '.stat{background:#fff;border-radius:10px;padding:10px 16px;box-shadow:0 2px 8px rgba(0,0,0,.05);font-size:.82em}'
         '.stat b{color:#667eea}'
         '.category{margin-bottom:28px}'
         '.cat-header{display:flex;align-items:center;gap:10px;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #eee}'
         '.cat-dot{width:12px;height:12px;border-radius:50%;flex-shrink:0}'
         '.cat-name{font-size:1.2em;font-weight:700}'
         '.cat-count{color:#999;font-size:.82em}'
         '.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(370px,1fr));gap:6px}'
         '.card{background:#fff;border-radius:8px;padding:10px 14px;box-shadow:0 1px 4px rgba(0,0,0,.04);transition:all .15s;border-left:3px solid transparent;display:flex;flex-direction:column;gap:3px}'
         '.card:hover{box-shadow:0 4px 16px rgba(0,0,0,.1);transform:translateY(-1px)}'
         '.card .title{font-size:.92em;line-height:1.5;font-weight:500}'
         '.card .title a{color:#2c3e50;text-decoration:none}'
         '.card .title a:hover{color:#667eea;text-decoration:underline}'
         '.card .source-row{display:flex;align-items:center;gap:6px;font-size:.72em;color:#999;flex-wrap:wrap;margin-top:2px}'
         '.tag{padding:1px 7px;border-radius:3px;font-size:.85em;white-space:nowrap}'
         '.tag.cn{background:#fff3e0;color:#e67e22}'
         '.tag.en{background:#e3f2fd;color:#1976d2}'
         '.heat{color:#e74c3c;font-weight:600}'
         '.nolink{color:#bbb}'
         '.orig{font-size:.78em;color:#aaa;font-style:italic}'
         '.footer{text-align:center;padding:30px;color:#999;font-size:.8em}'
         '@media(max-width:600px){.grid{grid-template-columns:1fr}}'
         '</style></head><body>'),
        f'<div class="header"><h1>Info Dashboard</h1>'
        f'<div class="meta">Generated: {NOW_TS} CST | {len(final)} items | {len(active_sources)} sources</div></div>',
        '<div class="container">',
    ]

    # Recommendations section
    html_parts.append(
        f'<div class="recommend"><h2>📊 今日推荐</h2>'
        f'<p style="color:#666;font-size:.9em;margin-bottom:15px">共推荐 {rec_count} 条，全部包含简介</p>')
    for cat, items in recommendations.items():
        if items:
            html_parts.append(f'<div class="recommend-section"><h3>{cat} ({len(items)}条)</h3>')
            for item in items:
                title = item.get("title_cn", item["title"])
                url = item.get("url", "")
                score = item["score"]
                source = item.get("source", "")
                summary = item.get("summary", "")
                html_parts.append(f'<div class="recommend-item"><span class="score">{score:.1f}</span>')
                if url:
                    html_parts.append(f'<a href="{e(url)}" target="_blank">{e(title)}</a>')
                else:
                    html_parts.append(e(title))
                html_parts.append(f' <span style="color:#999;font-size:.8em">({e(source)})</span>')
                if summary:
                    html_parts.append(f'<div class="summary">{e(summary)}</div>')
                html_parts.append("</div>")
            html_parts.append("</div>")
    html_parts.append("</div>")

    # Stats bar
    html_parts.append('<div class="stats">')
    for cname in sorted(cats.keys()):
        color = cat_colors.get(cname, "#999")
        html_parts.append(f'<div class="stat"><span style="color:{color}">&#9679;</span> '
                          f'<b>{e(cname)}</b> {len(cats[cname])}</div>')
    html_parts.append("</div>")

    # Items grid by category
    def cn_src(name):
        return any(ord(c) > 255 for c in name)

    for cname in sorted(cats.keys()):
        color = cat_colors.get(cname, "#999")
        items = cats[cname]
        html_parts.append(
            f'<div class="category"><div class="cat-header">'
            f'<div class="cat-dot" style="background:{color}"></div>'
            f'<span class="cat-name">{e(cname)}</span>'
            f'<span class="cat-count">({len(items)})</span></div><div class="grid">')
        for item in items:
            tc = item.get("title_cn") or item["title"]
            to = item["title"]
            url = item.get("url", "")
            src = item["source"]
            heat = item.get("heat", "")
            score = item.get("score", 0)
            diff = tc != to
            tagc = " cn" if cn_src(src) else " en"
            html_parts.append(f'<div class="card" style="border-left-color:{color}">')
            if url:
                html_parts.append(f'<div class="title"><a href="{e(url)}" target="_blank" '
                                  f'rel="noopener">{e(tc)}</a></div>')
            else:
                html_parts.append(f'<div class="title"><span class="nolink">{e(tc)}</span></div>')
            if diff:
                html_parts.append(f'<div class="orig">{e(to)}</div>')
            html_parts.append(f'<div class="source-row"><span class="score">{score:.1f}</span>'
                              f'<span class="tag{tagc}">{e(src)}</span>')
            if heat:
                html_parts.append(f'<span class="heat">{e(str(heat))}</span>')
            html_parts.append("</div></div>")
        html_parts.append("</div></div>")

    src_list = ", ".join(sorted(set(s["name"] for s in active_sources)))
    html_parts.append(
        f'</div><div class="footer">Sources: {e(src_list)}<br>'
        f'Powered by dashboard_v4 - Auto-generated</div></body></html>')

    html_path = os.path.join(outdir, "dashboard.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))
    print(f"  HTML: {html_path}")


def generate_v4_json(final: list, recommendations: dict, cache: dict):
    """Export JSON for Astro site (intel-daily-astro)"""
    from datetime import datetime, timezone, timedelta
    import json, os
    CST = timezone(timedelta(hours=8))
    now_ts = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now(CST).strftime("%Y-%m-%d")
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(outdir, exist_ok=True)

    active_sources = [s for s in OUT if s["count"] > 0]

    cat_recs = {}
    for cat, items in recommendations.items():
        cat_recs[cat] = [
            {
                "title": item.get("title_cn", item["title"]),
                "title_original": item["title"],
                "url": item.get("url", ""),
                "source": item.get("source", ""),
                "score": round(item["score"], 1),
                "summary": item.get("summary", ""),
                "heat": str(item.get("heat", "")),
            }
            for item in items
        ]

    cat_colors = {
        "AI/Frontier": "#00bcd4", "Chinese Tech": "#9b59b6",
        "International Tech": "#3498db", "Chinese Hot Search": "#e74c3c",
        "Chinese News": "#e67e22", "Finance": "#f39c12",
        "Community": "#2ecc71", "International News": "#1abc9c",
    }
    by_category = {}
    for item in final:
        c = item["category"]
        by_category.setdefault(c, []).append({
            "title": item.get("title_cn", item["title"]),
            "url": item.get("url", ""),
            "source": item.get("source", ""),
            "score": round(item.get("score", 0), 1),
            "heat": str(item.get("heat", "")),
        })

    data = {
        "date": date_str,
        "generated_at": now_ts,
        "summary": f"今日采集 {len(active_sources)} 个源，共 {len(final)} 条去重数据",
        "total_items": len(final),
        "total_sources": len(active_sources),
        "total_translated": len(cache),
        "recommendations": cat_recs,
        "by_category": by_category,
        "sources": [{"name": s["name"], "category": s["category"], "count": s["count"]}
                     for s in active_sources],
    }

    json_path = os.path.join(outdir, "daily_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  JSON: {json_path}")

    # Astro data directory (relative to script location: scripts/ -> ../src/data/v4/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    astro_dir = os.path.normpath(os.path.join(script_dir, "..", "src", "data", "v4"))
    if os.path.isdir(astro_dir):
        astro_path = os.path.join(astro_dir, f"daily-{date_str}.json")
        with open(astro_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  -> Astro: {astro_path}")
        # Update index.json with latest date
        index_path = os.path.join(astro_dir, "index.json")
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({"latest_date": date_str}, f, ensure_ascii=False)
        print(f"  -> Updated index.json: latest_date={date_str}")

        # Also copy to public/data/ for direct HTTP access (deployed as static file)
        public_dir = os.path.normpath(os.path.join(script_dir, "..", "public", "data"))
        os.makedirs(public_dir, exist_ok=True)
        public_path = os.path.join(public_dir, f"daily-{date_str}.json")
        with open(public_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  -> Public: {public_path}")
        # Always update latest.json
        latest_path = os.path.join(public_dir, "latest.json")
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  -> Public latest: {latest_path}")
    else:
        print(f"  (Astro v4 data dir not found: {astro_dir})")


def generate_rewrite_json(final: list, recommendations: dict):
    """Export rewrite-format JSON for Astro site's PlatformSection"""
    import json, os
    from datetime import datetime, timezone, timedelta
    CST = timezone(timedelta(hours=8))
    date_str = datetime.now(CST).strftime("%Y-%m-%d")
    
    # Source name → old platform key mapping
    SOURCE_PLATFORM = {
        "Hacker News": "hackernews", "Techmeme": "techmeme",
        "Slashdot": "slashdot", "Engadget": "engadget",
        "HackerNoon": "hackernoon", "TechCrunch": "techcrunch",
        "The Verge": "theverge", "Ars Technica": "arstechnica",
        "Wired": "wired", "Dev.to": "devto", "Lobsters": "lobsters",
        "Nature": "nature", "Science Daily": "sciencedaily",
        "MIT Tech Review": "mitteltechreview", "BBC Tech": "bbc",
        "GitHub Trending": "github", "BBC World": "bbc",
        "BBC News": "bbc", "The Guardian": "guardian",
        "NYTimes Tech": "nytimes", "NYTimes World": "nytimes",
        "CBC World": "cbc", "Euronews": "euronews", "NPR": "npr",
        "Baidu": "baidu", "Douyin": "douyin", "Bilibili": "bilibili",
        "Zhihu": "zhihu", "Toutiao": "toutiao", "Pengpai": "pengpai",
        "Sputnik CN": "sputnik", "Juejin": "juejin",
        "ifanr": "ifanr", "InfoQ CN": "infoq", "QbitAI": "qbitai",
        "AI Hot": "aihot", "WallstreetCN Hot": "wallstreetcn",
        "WallstreetCN Live": "wallstreetcn", "Tieba": "tieba",
        "Nowcoder": "nowcoder",
        "V2EX Hot": "v2ex",
        "Reddit Hot": "reddit",
        "Twitter Hot (Sopilot)": "twitter",
        "Weibo": "weibo",
        "IT之家": "ithome",
        "36氪": "36kr",
    }
    
    items = []
    seen_urls = set()
    
    for item in final:
        url = item.get("url", "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        
        source_name = item.get("source", "")
        platform_key = SOURCE_PLATFORM.get(source_name, source_name.lower().replace(" ", ""))
        
        title = item.get("title_cn", item.get("title", ""))
        desc = item.get("summary", "")[:200] if item.get("summary") else title[:200]
        if desc == title:
            desc = ""
        
        items.append({
            "id": len(items) + 1,
            "url": url,
            "platform": platform_key,
            "platform_label": source_name,
            "platform_color": "#94A3B8",
            "platform_icon": "\U0001f4cc",
            "hot": int(''.join(c for c in str(item.get("heat", 0)) if c.isdigit()) or 0),
            "date": date_str,
            "score": int(item.get("score", 0)),
            "category": item.get("category", "其他"),
            "title": title,
            "desc": desc,
            "cross_sources": 0,
        })
    
    data = {"date": date_str, "items": items}
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rewrite_dir = os.path.normpath(os.path.join(script_dir, "..", "src", "data", "rewrite", "zh"))
    if os.path.isdir(os.path.normpath(os.path.join(script_dir, "..", "src", "data", "rewrite"))):
        os.makedirs(rewrite_dir, exist_ok=True)
        json_path = os.path.join(rewrite_dir, f"{date_str}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  -> Rewrite (zh): {json_path} ({len(items)} items)")
    
        # Also generate en version (same data, different label mapping)
        en_dir = os.path.normpath(os.path.join(script_dir, "..", "src", "data", "rewrite", "en"))
        os.makedirs(en_dir, exist_ok=True)
        en_path = os.path.join(en_dir, f"{date_str}.json")
        with open(en_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  -> Rewrite (en): {en_path}")
    else:
        print(f"  (Rewrite dir not found: {rewrite_dir})")


# ====================================================================
# MAIN
# ====================================================================
async def main():
    t0 = time.time()

    # Phase 1: Collect
    ok, total_items = await collect_all()

    # Phase 2: Dedup
    final = deduplicate()

    # Phase 3: Translate
    cache = translate_titles(final)

    # Phase 4: Score
    score_items(final)

    # Phase 5: Classify + Recommend
    candidates = build_recommendations(final)

    # Phase 6: Summaries
    summary_count = generate_summaries(candidates)
    recommendations = select_recommendations(candidates)

    # Phase 7: Output
    print("\n=== PHASE 7: Output ===")
    generate_markdown(recommendations, final)
    generate_html(recommendations, final)
    generate_v4_json(final, recommendations, cache)
    generate_rewrite_json(final, recommendations)

    elapsed = time.time() - t0
    active = [s for s in OUT if s["count"] > 0]
    print(f'\n{"="*60}')
    print(f"Done @ {NOW_TS}  ({elapsed:.0f}s)")
    print(f"  Sources: {len(active)} | Items: {len(final)} | Translated: {len(cache)}")
    print(f"  Recommendations: {sum(len(v) for v in recommendations.values())}")
    for s in OUT:
        ok_s = "OK" if s["count"] > 0 else "--"
        print(f"  {ok_s} [{s['category']}] {s['name']}: {s['count']}")


if __name__ == "__main__":
    asyncio.run(main())
