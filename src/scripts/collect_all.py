import os
import json
import requests
import time
import subprocess
import sys
import re
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

# 设置基础路径
BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR
DB_DIR = BASE_DIR / "db"
SKILLS_DIR = BASE_DIR / "skills"

# 将核心模块加入路径
sys.path.insert(0, str(BASE_DIR))
from db.db import upsert_item, upsert_stats, log_collect, get_conn, _hash

API_KEY = os.environ.get("ZHIPU_API_KEY")

# Baidu Translate
BAIDU_APP_ID = os.environ.get("BAIDU_TRANSLATE_APP_ID", "")
BAIDU_SECRET_KEY = os.environ.get("BAIDU_TRANSLATE_SECRET_KEY", "")

# 每日翻译字符上限（百度免费 100 万/月，设 3 万/天留余量）
DAILY_TRANSLATE_LIMIT = 30000

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    try:
        print(f"[{ts}] {msg}", flush=True)
    except UnicodeEncodeError:
        print(f"[{ts}] {msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace')}", flush=True)

def call_zhipu(model, prompt, temperature=0.2):
    if not API_KEY: return None
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": temperature}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        log(f"  AI API Error: {e}")
        return None

def get_dual_language_data(title, content):
    """使用 GLM-4-Air 处理双语和评分"""
    prompt = f"""
    You are an expert intelligence analyst. Analyze the following content:
    Title: {title}
    Content: {content[:300]}

    Tasks:
    1. Score from 0-10 based on value.
    2. Provide a concise Chinese summary (under 30 words).
    3. Translate title to English.
    4. Provide a concise English summary.

    Return EXACTLY in this JSON format:
    {{
      "score": number,
      "zh": {{"summary": "中文摘要"}},
      "en": {{"title": "English Title", "summary": "English Summary"}}
    }}
    """
    res = call_zhipu("glm-4-air", prompt)
    if not res: return None
    try:
        match = re.search(r'\{.*\}', res, re.DOTALL)
        return json.loads(match.group())
    except: return None


def contains_chinese(text):
    """检测是否包含中文"""
    return bool(re.search(r'[一-鿿]', text))


def get_daily_translate_usage(date_key):
    """查询当日已用翻译字符数"""
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS translate_usage (date_key TEXT PRIMARY KEY, chars_used INTEGER DEFAULT 0, item_count INTEGER DEFAULT 0)""")
        r = conn.execute("SELECT chars_used FROM translate_usage WHERE date_key = ?", (date_key,)).fetchone()
        return r[0] if r else 0


def record_translate_usage(date_key, chars):
    """记录翻译用量"""
    with get_conn() as conn:
        conn.execute("""INSERT INTO translate_usage (date_key, chars_used, item_count) VALUES (?, ?, 1) ON CONFLICT(date_key) DO UPDATE SET chars_used = chars_used + ?, item_count = item_count + 1""", (date_key, chars, chars))
        conn.commit()


def baidu_translate(text):
    """百度翻译 API：英译中"""
    if not BAIDU_APP_ID or not BAIDU_SECRET_KEY:
        return None
    import random, hashlib
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
        if 'error_code' in data:
            log(f"  百度翻译错误 [{data['error_code']}]: {data.get('error_msg', '')}")
    except Exception as e:
        log(f"  百度翻译异常: {e}")
    return None


# ---- Scrapers ----

def run_py(script, *args):
    cmd = [sys.executable, str(script)] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, encoding='utf-8', errors='replace')
        if r.returncode == 0 and r.stdout.strip():
            try:
                return json.loads(r.stdout.strip())
            except: return None
    except: return None

def collect_news_agg():
    script = SKILLS_DIR / "news-aggregator-skill" / "scripts" / "fetch_news.py"
    if not script.exists(): return []
    sources = ['hackernews','github','producthunt','36kr','tencent','v2ex','wallstreetcn','ithome','toutiao']
    items = []
    for src in sources:
        res = run_py(script, "--source", src, "--limit", "10")
        if isinstance(res, list):
            for it in res:
                it['source_type'] = 'news_aggregator'
                it['original_source'] = src
            items.extend(res)
    return items

def collect_weibo():
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)', 'Referer': 'https://weibo.com'}
        resp = requests.get(url, headers=headers, timeout=15)
        bands = resp.json().get('data', {}).get('realtime', [])
        items = []
        import urllib.parse
        for b in bands:
            word = b.get('word', '')
            if word:
                items.append({
                    'source_type': 'weibo', 'original_source': 'weibo',
                    'title': word, 'desc': b.get('note', ''),
                    'url': f"https://s.weibo.com/weibo?q={urllib.parse.quote(word)}",
                    'hot_value': 0, 'frequency': 2
                })
        return items
    except: return []

def collect_douyin():
    script = SKILLS_DIR / "douyin-hot" / "scripts" / "douyin_json.js"
    if not script.exists(): return []
    cmd = ['node', str(script), "10"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding='utf-8')
        res = json.loads(r.stdout.strip())
        return [{
            'source_type':'douyin','original_source':'douyin',
            'title': i.get('title',''), 'desc': i.get('desc',''),
            'url': i.get('link','') or i.get('url',''), 'hot_value': i.get('hot_value',0),
            'frequency': 2
        } for i in res if isinstance(i, dict)]
    except: return []

def collect_reddit():
    subs = ['technology', 'programming', 'MachineLearning', 'artificial', 'github', 'Python', 'LocalLLaMA']
    items = []
    for sub in subs:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot/.json?limit=10"
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            posts = resp.json()['data']['children']
            for p in posts:
                d = p['data']
                items.append({
                    'source_type': 'reddit', 'original_source': f'reddit/{sub}',
                    'title': d.get('title', ''), 'desc': d.get('selftext', '')[:500],
                    'url': f"https://reddit.com{d.get('permalink', '')}",
                    'hot_value': d.get('score', 0), 'frequency': 1
                })
        except: continue
    return items

def collect_rss():
    feeds = [('36Kr', 'https://36kr.com/feed'), ('少数派', 'https://sspai.com/feed'), ('阮一峰', 'http://feeds.feedburner.com/ruanyifeng')]
    items = []
    for name, url in feeds:
        try:
            resp = requests.get(url, timeout=15)
            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', resp.text)
            links = re.findall(r'<link>(.*?)</link>', resp.text)
            for t, l in zip(titles[:10], links[:10]):
                items.append({'source_type': 'rss', 'original_source': name, 'title': t, 'desc': '', 'url': l, 'hot_value': 0, 'frequency': 1})
        except: continue
    return items

# ---- Focus Generation ----

def generate_focus(date_key):
    """使用 AI 生成今日重点：TOP5 亮点 + 趋势关键词"""
    focus_dir = BASE_DIR.parent.parent / "src" / "data" / "rewrite"
    focus_dir.mkdir(exist_ok=True, parents=True)

    with get_conn() as conn:
        rows = conn.execute("""
            SELECT title, url, score, ai_summary, source_type
            FROM items
            WHERE date_key = ? AND score >= 5
            ORDER BY score DESC
            LIMIT 20
        """, (date_key,)).fetchall()

    if len(rows) < 3:
        log(f"  [Focus] 数据不足 ({len(rows)}条)，跳过")
        return

    items_text = "\n".join([
        f"{i+1}. [{r['source_type']}] {r['title']} (评分:{r['score']}) | {r['ai_summary'] or '无摘要'}"
        for i, r in enumerate(rows)
    ])

    prompt = f"""你是豆子实验室的首席编辑。分析以下今日情报，输出最有价值的发现。

今日情报列表（按AI评分排序）：
{items_text}

请以 JSON 格式返回（不要包含其他内容）：
{{
  "summary": "今日整体趋势一句话总结（20字以内）",
  "highlights": [
    {{
      "rank": 1,
      "title": "原标题",
      "reason": "为什么重要（20字以内）",
      "insight": "深度解读或背后趋势（40字以内）",
      "source": "来源",
      "url": "原文链接"
    }}
  ],
  "trends": ["趋势关键词1", "趋势关键词2", "趋势关键词3"]
}}

要求：
- 选最重要的 5 条，不是评分最高的 5 条
- reason 写这条信息为什么对读者重要
- insight 写背后的含义或趋势信号
- trends 写 3 个今日最值得关注的关键词趋势
"""

    result = call_zhipu("glm-4-air", prompt)
    if not result:
        log("  [Focus] AI 无返回")
        return

    try:
        match = re.search(r'\{.*\}', result, re.DOTALL)
        if not match:
            log("  [Focus] 未找到 JSON")
            return
        data = json.loads(match.group())
        data['date'] = date_key
        data['generated_at'] = datetime.now().isoformat()

        with open(focus_dir / "today-focus.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log(f"  [Focus] 生成 {len(data.get('highlights', []))} 条重点 ✓")
    except Exception as e:
        log(f"  [Focus] 解析失败: {e}")

# ---- Main ----

def collect_all():
    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz).strftime("%Y-%m-%d")
    log(f"=== Global Collection: {today} (Asia/Shanghai) ===")
    
    scrapers = [
        ('News Aggregator', collect_news_agg),
        ('Weibo', collect_weibo),
        ('Douyin', collect_douyin),
        ('Reddit', collect_reddit),
        ('RSS', collect_rss)
    ]
    
    added_count = 0
    skip_count = 0
    
    for name, fn in scrapers:
        log(f"Running {name}...")
        items = fn()
        log(f"  Found {len(items)} items")
        
        for it in items:
            h = _hash(it['title'], it.get('url', ''))
            with get_conn() as conn:
                if conn.execute("SELECT id FROM items WHERE hash = ?", (h,)).fetchone():
                    skip_count += 1
                    continue
            
            # AI Processing
            log(f"  [AI] Processing: {it['title'][:40]}...")
            dual = get_dual_language_data(it['title'], it.get('desc', ''))
            if isinstance(dual, dict):
                it['score'] = dual.get('score', 5) or 5
                zh = dual.get('zh')
                en = dual.get('en')
                if isinstance(zh, dict):
                    it['ai_summary'] = zh.get('summary', '')
                if isinstance(en, dict):
                    it['en_title'] = en.get('title', '')
                    it['en_summary'] = en.get('summary', '')

            # 百度翻译：英文标题 → 中文（每日限额 30000 字符）
            if not contains_chinese(it['title']):
                used = get_daily_translate_usage(today)
                est = len(it['title']) + 20  # title + 20 字符余量
                if used + est <= DAILY_TRANSLATE_LIMIT:
                    zh = baidu_translate(it['title'])
                    if zh and zh != it['title']:
                        it['zh_title'] = zh
                        record_translate_usage(today, est)
                        log(f"  [CN] Translated: {it['title'][:30]} → {zh[:30]}")
                else:
                    pass  # 超出每日限额，跳过翻译
            
            a, s = upsert_item(it, today)
            added_count += a
            skip_count += s
            if a > 0: time.sleep(0.5)

    # Stats
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM items WHERE date_key=?", (today,)).fetchone()[0]
    upsert_stats(today, total)
    
    # Export
    log("Exporting JSONs...")
    subprocess.run([sys.executable, str(SCRIPTS_DIR / "dump_astro_json.py")], cwd=str(SCRIPTS_DIR))

    # Generate today's focus
    log("Generating today's focus...")
    generate_focus(today)

    log(f"=== Finished: +{added_count}, skipped {skip_count} ===")

if __name__ == "__main__":
    collect_all()
