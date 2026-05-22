import argparse
import json
import requests
from bs4 import BeautifulSoup
import sys
import time
import re
import concurrent.futures
from datetime import datetime

# 确保 stdout 输出 UTF-8（避免中文 Windows 系统 codepage 导致乱码）
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Headers for scraping to avoid basic bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def filter_items(items, keyword=None):
    if not keyword:
        return items
    keywords = [k.strip() for k in keyword.split(',') if k.strip()]
    pattern = '|'.join([r'\b' + re.escape(k) + r'\b' for k in keywords])
    regex = r'(?i)(' + pattern + r')'
    return [item for item in items if re.search(regex, item['title'])]

def fetch_url_content(url):
    """
    Fetches the content of a URL and extracts text from paragraphs.
    Truncates to 3000 characters.
    """
    if not url or not url.startswith('http'):
        return ""
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
         # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        # Simple cleanup
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text[:3000]
    except Exception:
        return ""

def enrich_items_with_content(items, max_workers=10):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {executor.submit(fetch_url_content, item['url']): item for item in items}
        for future in concurrent.futures.as_completed(future_to_item):
            item = future_to_item[future]
            try:
                content = future.result()
                if content:
                    item['content'] = content
            except Exception:
                item['content'] = ""
    return items

# --- Source Fetchers ---

def fetch_hackernews(limit=5, keyword=None):
    base_url = "https://news.ycombinator.com"
    news_items = []
    page = 1
    max_pages = 5
    
    while len(news_items) < limit and page <= max_pages:
        url = f"{base_url}/news?p={page}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200: break
        except: break

        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.select('.athing')
        if not rows: break
        
        page_items = []
        for row in rows:
            try:
                id_ = row.get('id')
                title_line = row.select_one('.titleline a')
                if not title_line: continue
                title = title_line.get_text()
                link = title_line.get('href')
                
                # Metadata
                score_span = soup.select_one(f'#score_{id_}')
                score = score_span.get_text() if score_span else "0 points"
                
                # Age/Time
                age_span = soup.select_one(f'.age a[href="item?id={id_}"]')
                time_str = age_span.get_text() if age_span else ""
                
                if link and link.startswith('item?id='): link = f"{base_url}/{link}"
                
                page_items.append({
                    "source": "Hacker News", 
                    "title": title, 
                    "url": link, 
                    "heat": score,
                    "time": time_str
                })
            except: continue
        
        news_items.extend(filter_items(page_items, keyword))
        if len(news_items) >= limit: break
        page += 1
        time.sleep(0.5)

    return news_items[:limit]

def fetch_weibo(limit=5, keyword=None):
    # Use the PC Ajax API which returns JSON directly and is less rate-limited than scraping s.weibo.com
    url = "https://weibo.com/ajax/side/hotSearch"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://weibo.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        items = data.get('data', {}).get('realtime', [])
        
        all_items = []
        for item in items:
            # key 'note' is usually the title, sometimes 'word'
            title = item.get('note', '') or item.get('word', '')
            if not title: continue
            
            # 'num' is the heat value
            heat = item.get('num', 0)
            
            # Construct URL (usually search query)
            # Web UI uses: https://s.weibo.com/weibo?q=%23TITLE%23&Refer=top
            full_url = f"https://s.weibo.com/weibo?q={requests.utils.quote(title)}&Refer=top"
            
            all_items.append({
                "source": "Weibo Hot Search", 
                "title": title, 
                "url": full_url, 
                "heat": f"{heat}",
                "time": "Real-time"
            })
            
        return filter_items(all_items, keyword)[:limit]
    except Exception: 
        return []

def fetch_github(limit=5, keyword=None):
    try:
        response = requests.get("https://github.com/trending", headers=HEADERS, timeout=10)
    except: return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    items = []
    for article in soup.select('article.Box-row'):
        try:
            h2 = article.select_one('h2 a')
            if not h2: continue
            title = h2.get_text(strip=True).replace('\n', '').replace(' ', '')
            link = "https://github.com" + h2['href']
            
            desc = article.select_one('p')
            desc_text = desc.get_text(strip=True) if desc else ""
            
            # Stars (Heat)
            # usually the first 'Link--muted' with a SVG star
            stars_tag = article.select_one('a[href$="/stargazers"]')
            stars = stars_tag.get_text(strip=True) if stars_tag else ""
            
            items.append({
                "source": "GitHub Trending", 
                "title": f"{title} - {desc_text}", 
                "url": link,
                "heat": f"{stars} stars",
                "time": "Today"
            })
        except: continue
    return filter_items(items, keyword)[:limit]

def fetch_36kr(limit=5, keyword=None):
    try:
        response = requests.get("https://36kr.com/newsflashes", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        items = []
        for item in soup.select('.newsflash-item'):
            title = item.select_one('.item-title').get_text(strip=True)
            href = item.select_one('.item-title')['href']
            time_tag = item.select_one('.time')
            time_str = time_tag.get_text(strip=True) if time_tag else ""
            
            items.append({
                "source": "36Kr", 
                "title": title, 
                "url": f"https://36kr.com{href}" if not href.startswith('http') else href,
                "time": time_str,
                "heat": ""
            })
        return filter_items(items, keyword)[:limit]
    except: return []

def fetch_v2ex(limit=5, keyword=None):
    try:
        # Hot topics json
        data = requests.get("https://www.v2ex.com/api/topics/hot.json", headers=HEADERS, timeout=10).json()
        items = []
        for t in data:
            # V2EX API fields: created, replies (heat)
            replies = t.get('replies', 0)
            created = t.get('created', 0)
            # convert epoch to readable if possible, simpler to just leave as is or basic format
            # Let's keep it simple
            items.append({
                "source": "V2EX", 
                "title": t['title'], 
                "url": t['url'],
                "heat": f"{replies} replies",
                "time": "Hot"
            })
        return filter_items(items, keyword)[:limit]
    except: return []

def fetch_tencent(limit=5, keyword=None):
    try:
        url = "https://i.news.qq.com/web_backend/v2/getTagInfo?tagId=aEWqxLtdgmQ%3D"
        data = requests.get(url, headers={"Referer": "https://news.qq.com/"}, timeout=10).json()
        items = []
        for news in data['data']['tabs'][0]['articleList']:
            items.append({
                "source": "Tencent News", 
                "title": news['title'], 
                "url": news.get('url') or news.get('link_info', {}).get('url'),
                "time": news.get('pub_time', '') or news.get('publish_time', '')
            })
        return filter_items(items, keyword)[:limit]
    except: return []

def fetch_wallstreetcn(limit=5, keyword=None):
    try:
        url = "https://api-one.wallstcn.com/apiv1/content/information-flow?channel=global-channel&accept=article&limit=30"
        data = requests.get(url, timeout=10).json()
        items = []
        for item in data['data']['items']:
            res = item.get('resource')
            if res and (res.get('title') or res.get('content_short')):
                 ts = res.get('display_time', 0)
                 time_str = datetime.fromtimestamp(ts).strftime('%H:%M') if ts else ""
                 items.append({
                     "source": "Wall Street CN", 
                     "title": res.get('title') or res.get('content_short'), 
                     "url": res.get('uri'),
                     "time": time_str
                 })
        return filter_items(items, keyword)[:limit]
    except: return []

def fetch_producthunt(limit=5, keyword=None):
    # 方法1: 试RSS
    for feed_url in ["https://www.producthunt.com/feed", "https://www.producthunt.com/feed.xml"]:
        try:
            response = requests.get(feed_url, headers=HEADERS, timeout=10)
            if response.status_code == 200 and ('<item' in response.text or '<entry' in response.text):
                soup = BeautifulSoup(response.content, 'xml')
                if not soup.find('item'): soup = BeautifulSoup(response.content, 'html.parser')
                items = []
                for entry in soup.find_all(['item', 'entry'])[:limit]:
                    title = entry.find('title').get_text(strip=True)
                    link_tag = entry.find('link')
                    url = link_tag.get('href') or link_tag.get_text(strip=True) if link_tag else ""
                    pubBox = entry.find('pubDate') or entry.find('published')
                    pub = pubBox.get_text(strip=True) if pubBox else ""
                    items.append({"source": "Product Hunt", "title": title, "url": url, "time": pub, "heat": "Top Product"})
                if items: return items
        except: pass
    
    # 方法2: 抓 sitemap
    try:
        resp = requests.get("https://www.producthunt.com/sitemaps/posts.xml", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'xml')
            items = []
            for loc in soup.find_all('loc')[:limit]:
                url = loc.get_text(strip=True)
                if '/posts/' in url:
                    title = url.split('/posts/')[-1].replace('-', ' ')
                    items.append({"source": "Product Hunt", "title": title, "url": url, "time": "", "heat": ""})
            if items: return items
    except: pass
    
    # 方法3: AlternativeTo 替代（无API Key时可用）
    try:
        resp = requests.get("https://api.alternativeto.net/software/product-hunt", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = []
            for item in data.get('Items', [])[:limit]:
                items.append({
                    "source": "AlternativeTo",
                    "title": item.get('Name', '') + ' - ' + item.get('Description', '')[:50],
                    "url": item.get('Url', ''),
                    "heat": str(item.get('Votes', 0)) + ' votes',
                    "time": ""
                })
            if items: return items
    except: pass
    
    return []

def fetch_ithome(limit=5, keyword=None):
    """IT之家 RSS - 数码科技资讯"""
    try:
        response = requests.get("https://www.ithome.com/rss/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'xml')
        items = []
        for entry in soup.find_all('item')[:limit]:
            title = entry.find('title').get_text(strip=True)
            link = entry.find('link').get_text(strip=True) if entry.find('link') else ""
            pub = entry.find('pubDate').get_text(strip=True) if entry.find('pubDate') else ""
            items.append({"source": "IT之家", "title": title, "url": link, "time": pub, "heat": ""})
        return filter_items(items, keyword)[:limit]
    except: return []

def fetch_chuangye(limit=5, keyword=None):
    """创业邦 RSS - 创业投资资讯"""
    try:
        response = requests.get("https://www.cyzone.cn/rss/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'xml')
        items = []
        for entry in soup.find_all('item')[:limit]:
            title = entry.find('title').get_text(strip=True)
            link = entry.find('link').get_text(strip=True) if entry.find('link') else ""
            pub = entry.find('pubDate').get_text(strip=True) if entry.find('pubDate') else ""
            items.append({"source": "创业邦", "title": title, "url": link, "time": pub, "heat": ""})
        return filter_items(items, keyword)[:limit]
    except: return []

def fetch_toutiao(limit=5, keyword=None):
    """今日头条 API - 国内热点新闻"""
    try:
        url = "https://www.toutiao.com/api/pc/feed/?tab_name=hot_online&max_behot_time=0&count=20"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        items = []
        for item in resp.json().get('data', [])[:limit]:
            title = item.get('title', '')
            url2 = item.get('source_url', '')
            if url2 and not url2.startswith('http'):
                url2 = 'https://www.toutiao.com' + url2
            if not url2:
                gid = item.get('group_id', '') or item.get('mid', '')
                if gid:
                    url2 = f'https://www.toutiao.com/group/{gid}/'
            if title:
                items.append({"source": "今日头条", "title": title, "url": url2, "time": "", "heat": str(item.get('hot_score', ''))})
        return filter_items(items, keyword)[:limit]
    except Exception as e:
        return []

def fetch_bilibili(limit=5, keyword=None):
    """B站排行榜 API - 视频热点"""
    try:
        url = "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        items = []
        for item in data.get('data', {}).get('list', [])[:limit]:
            stat = item.get('stat', {})
            items.append({
                "source": "Bilibili",
                "title": item.get('title', ''),
                "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                "heat": str(stat.get('view', 0)) + "播放",
                "time": ""
            })
        return filter_items(items, keyword)[:limit]
    except: return []

# 澎湃/观察者/网易的RSS被重定向到HTML，暂移除
# 改用 HTML 解析抓取（备选方案）
def fetch_pengpai(limit=5, keyword=None):
    """澎湃新闻 HTML 解析"""
    try:
        resp = requests.get("https://www.thepaper.cn/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = []
        for a in soup.select('a[href*="/newsDetail_"]')[:limit]:
            title = a.get_text(strip=True)
            href = a.get('href', '')
            if title and len(title) > 5:
                full_url = 'https://www.thepaper.cn' + href if href.startswith('/') else href
                items.append({"source": "澎湃新闻", "title": title, "url": full_url, "time": "", "heat": ""})
        return filter_items(items, keyword)[:limit]
    except: return []

def fetch_guancha(limit=5, keyword=None):
    """观察者网 HTML 解析"""
    try:
        resp = requests.get("https://www.guancha.cn/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = []
        for a in soup.select('a[href*="/content_"]')[:limit]:
            title = a.get_text(strip=True)
            href = a.get('href', '')
            if title and len(title) > 5:
                full_url = 'https://www.guancha.cn' + href if href.startswith('/') else href
                items.append({"source": "观察者网", "title": title, "url": full_url, "time": "", "heat": ""})
        return filter_items(items, keyword)[:limit]
    except: return []

def fetch_163(limit=5, keyword=None):
    """网易新闻 HTML 解析"""
    try:
        resp = requests.get("https://www.163.com/news/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = []
        for a in soup.select('a[href*="news.163.com"]')[:limit]:
            title = a.get_text(strip=True)
            href = a.get('href', '')
            if title and len(title) > 5 and not href.startswith('javascript'):
                items.append({"source": "网易新闻", "title": title, "url": href, "time": "", "heat": ""})
        return filter_items(items, keyword)[:limit]
    except: return []

def main():
    parser = argparse.ArgumentParser()
    sources_map = {
        'hackernews': fetch_hackernews, 'weibo': fetch_weibo, 'github': fetch_github,
        '36kr': fetch_36kr, 'v2ex': fetch_v2ex, 'tencent': fetch_tencent,
        'wallstreetcn': fetch_wallstreetcn, 'producthunt': fetch_producthunt,
        'ithome': fetch_ithome, 'chuangye': fetch_chuangye,
        'toutiao': fetch_toutiao, 'bilibili': fetch_bilibili,
        'pengpai': fetch_pengpai, 'guancha': fetch_guancha, '163': fetch_163
    }
    
    parser.add_argument('--source', default='all', help='Source(s) to fetch from (comma-separated)')
    parser.add_argument('--limit', type=int, default=10, help='Limit per source. Default 10')
    parser.add_argument('--keyword', help='Comma-sep keyword filter')
    parser.add_argument('--deep', action='store_true', help='Download article content for detailed summarization')
    
    args = parser.parse_args()
    
    to_run = []
    if args.source == 'all':
        to_run = list(sources_map.values())
    else:
        requested_sources = [s.strip() for s in args.source.split(',')]
        for s in requested_sources:
            if s in sources_map: to_run.append(sources_map[s])
            
    results = []
    for func in to_run:
        try:
            results.extend(func(args.limit, args.keyword))
        except: pass
        
    if args.deep and results:
        sys.stderr.write(f"Deep fetching content for {len(results)} items...\n")
        results = enrich_items_with_content(results)
        
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
