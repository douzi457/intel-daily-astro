# rss_newsnow.py — 主 RSS 抓取（newsnow 聚合源）
import re
import time
from xml.etree import ElementTree as ET
import requests
from ..config import HEADERS, URL_PLATFORM_MAP, PER_SOURCE_LIMIT, MAX_TOTAL
from ..log import log


def detect_platform(url):
    """URL → 平台键映射。"""
    if not url:
        return "news_aggregator"
    for pattern, key in URL_PLATFORM_MAP:
        if re.search(pattern, url, re.IGNORECASE):
            return key
    return "news_aggregator"


def parse_rss_items(xml_content, source="newsnow"):
    """解析 RSS 2.0 XML，返回条目列表。"""
    items = []
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        log(f"  RSS parse failed for {source}")
        return items

    for item_elem in root.findall('.//item'):
        title_elem = item_elem.find('title')
        link_elem = item_elem.find('link')
        pub_date_elem = item_elem.find('pubDate')
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
        link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
        pub_date = pub_date_elem.text.strip() if pub_date_elem is not None and pub_date_elem.text else ""

        if not title or not link:
            continue

        items.append({
            "title": title, "url": link, "pubDate": pub_date,
            "platform": detect_platform(link),
        })
    return items


def fetch_newsnow_rss():
    """抓取并解析 newsnow RSS 源。"""
    url = "https://news.zhinengtech.dpdns.org/api/feed.xml"
    log(f"Fetching newsnow RSS: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            log(f"  newsnow RSS: HTTP {resp.status_code}")
            return [], {"status": "error", "items": 0, "duration_ms": 0}
        t0 = time.time()
        items = parse_rss_items(resp.content)
        duration = int((time.time() - t0) * 1000)

        # 每源限制 + 总数限制
        platform_buckets = {}
        for it in items:
            platform_buckets.setdefault(it['platform'], []).append(it)
        limited = []
        for p, pitems in platform_buckets.items():
            pitems.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
            limited.extend(pitems[:PER_SOURCE_LIMIT])
        limited.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
        result = limited[:MAX_TOTAL]

        log(f"  newsnow RSS: {len(result)} items (from {len(items)} raw)")
        return result, {"status": "success", "items": len(result), "duration_ms": duration}
    except Exception as e:
        log(f"  newsnow RSS error: {e}")
        return [], {"status": "error", "items": 0, "duration_ms": 0, "error_message": str(e)[:200]}
