# rss_direct.py — 直连 RSS 抓取（阮一峰、少数派、GeekPark）
import time
from xml.etree import ElementTree as ET
import requests
from ..config import HEADERS, SUPPLEMENTARY_RSS
from ..log import log


def fetch_direct_rss():
    """抓取补充直连 RSS 源。"""
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
                    title_elem = item_elem.find('title')
                    link_elem = item_elem.find('link')
                    title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                    link = link_elem.get('href', '') or link_elem.text or '' if link_elem is not None else ""
                    if not title or not link:
                        continue
                    items.append({"title": title, "url": link, "pubDate": "", "platform": key})
                    if len(items) >= 10:
                        break
            except ET.ParseError:
                log(f"    XML parse failed, skip")
                continue

            all_items.extend(items)
            log(f"    {len(items)} items")
        except Exception as e:
            log(f"    Error: {e}")
            continue
    return all_items
