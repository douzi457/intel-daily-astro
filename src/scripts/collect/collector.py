"""
情报采集器 - SQLite 持久化版
每次采集增量写入数据库，支持重复运行去重
"""
import subprocess, json, time, os, sys
from datetime import datetime, timedelta, timezone, date
from pathlib import Path
import io
sys.stdout.reconfigure(encoding='utf-8')

# 路径配置
WORKSPACE   = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")
SKILLS_DIR  = Path(r"C:\Users\douzi457\.qclaw\workspace\skills")
DB_DIR      = WORKSPACE / "db"

CST = timezone(timedelta(hours=8))

# 添加 db 目录到 sys.path 以便导入
sys.path.insert(0, str(WORKSPACE))
from db.db import upsert_item, upsert_stats, log_collect

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    # 避免 emoji 在 Windows PowerShell GBK 编码下报错
    safe = msg.encode('utf-8', 'replace').decode('utf-8')
    print(f"[{ts}] {safe}", flush=True)

def run_py(script, *args):
    cmd = [sys.executable, str(script)] + list(args)
    try:
        # 子进程脚本输出可能是 GBK（中文 Windows）或 UTF-8，GBK 覆盖大多数情况
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                          encoding='utf-8', errors='replace')
        if r.returncode == 0 and r.stdout.strip():
            try:
                return json.loads(r.stdout.strip())
            except json.JSONDecodeError:
                log(f"  JSON解析失败（输出非JSON）: {script.name}")
    except Exception as e:
        log(f"  执行错误 {script.name}: {e}")
    return None

def run_js(script, *args):
    cmd = ['node', str(script)] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                          encoding='utf-8', errors='replace')
        if r.returncode == 0 and r.stdout.strip():
            try:
                return json.loads(r.stdout.strip())
            except json.JSONDecodeError:
                log(f"  JSON解析失败: {script.name}")
    except Exception as e:
        log(f"  执行错误 {script.name}: {e}")
    return None

def read_sqlite(db_path, query, params=None):
    if not Path(db_path).exists(): return []
    import sqlite3
    try:
        conn = sqlite3.connect(str(db_path)); conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params or []).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except: return []

# ---- 数据源采集函数 ----

def collect_news_agg():
    """8大情报源"""
    script = SKILLS_DIR / "news-aggregator-skill" / "scripts" / "fetch_news.py"
    if not script.exists(): return []
    sources = ['hackernews','github','producthunt','36kr','tencent','v2ex','wallstreetcn','ithome','chuangye','toutiao','bilibili']
    items = []
    for src in sources:
        res = run_py(script, "--source", src, "--limit", "10")
        if isinstance(res, list):
            for it in res:
                it['source_type'] = 'news_aggregator'
                it['original_source'] = src
            items.extend(res)
        time.sleep(0.5)
    return items

def collect_douyin():
    script = SKILLS_DIR / "douyin-hot" / "scripts" / "douyin_json.js"
    if not script.exists(): return []
    res = run_js(script, "10")  # limit 10 to avoid dominating the feed
    if isinstance(res, list):
        return [{
            'source_type':'douyin','original_source':'douyin_hot',
            'title': i.get('title',''), 'desc': i.get('desc',''),
            'url': i.get('link','') or i.get('url',''), 'hot_value': i.get('hot_value',0),
            'frequency': 2
        } for i in res if isinstance(i, dict)]
    return []

def collect_gzh():
    script = SKILLS_DIR / "gzh-explosive-content-detector" / "scripts" / "fetch_gzh_trends.py"
    if not script.exists(): return []
    items = []
    import json as _json
    for kw in ["副业","赚钱","变现","创业","AI","工具"]:
        # gzh 脚本把文件写到 cwd，先清理旧文件避免读旧数据
        output_file = WORKSPACE / f"{kw}_爆款数据.json"
        if output_file.exists():
            try: output_file.unlink()
            except: pass
        # 运行脚本（JSON写入cwd）
        r = run_py(script, "--keyword", kw, "--max-items", "10", "--output-format", "json")
        time.sleep(0.5)
        # 从 cwd 的 JSON 文件读取数据
        if output_file.exists():
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    data = _json.load(f)
                if isinstance(data, dict) and "items" in data:
                    for it in data["items"]:
                        it['source_type'] = 'gzh'
                        it['original_source'] = kw
                    items.extend(data["items"])
            except Exception as e:
                log(f"  gzh[{kw}] 解析失败: {e}")
    return items

def collect_weibo():
    """微博热搜 - 直接 HTTP 抓取 mobile API（无需登录）"""
    try:
        import urllib.request as _urllib
        import urllib.parse as _urllib_parse
        import json as _json
        url = "https://weibo.com/ajax/side/hotSearch"
        req = _urllib.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)',
            'Referer': 'https://weibo.com'
        })
        with _urllib.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read().decode('utf-8'))
        if data.get('ok') != 1: return []
        bands = data.get('data', {}).get('realtime', [])
        items = []
        for b in bands:
            word = b.get('word', '')
            if not word or word in ['首页','推荐','视频','消息']: continue
            items.append({
                'source_type': 'weibo',
                'original_source': 'weibo_hot',
                'title': b.get('word', ''),
                'desc': b.get('note', ''),
                'url': f"https://s.weibo.com/weibo?q={_urllib_parse.quote(b.get('word',''))}",
                'hot_value': 0,
                'frequency': 2
            })
        log(f"  微博热搜 {len(items)} 条")
        return items
    except Exception as e:
        log(f"  微博抓取失败: {e}")
        return []

def collect_sspai():
    """少数派 - 直接 HTTP 抓取 RSS+HTML"""
    try:
        import urllib.request as _urllib
        # RSS 订阅源
        rss_url = "https://sspai.com/feed"
        req = _urllib.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with _urllib.urlopen(req, timeout=15) as resp:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.read().decode('utf-8'), 'html.parser')
        items = []
        for item in soup.find_all('item')[:20]:
            title = item.title.string if item.title else ''
            link = item.link.string if item.link else ''
            desc = item.description.string[:200] if item.description else ''
            if title:
                items.append({
                    'source_type': 'sspai',
                    'original_source': 'sspai',
                    'title': title.strip(),
                    'desc': desc.strip() if desc else '',
                    'url': link.strip() if link else '',
                    'frequency': 1
                })
        log(f"  少数派 {len(items)} 条")
        return items
    except Exception as e:
        log(f"  少数派抓取失败: {e}")
        return []

def collect_reddit():
    script = WORKSPACE / "collect" / "collector_reddit.py"
    if not script.exists(): return []
    result = run_py(script)
    # collector_reddit.py 直接写库，返回 None 或数字
    # 重新查询今日新增条数
    if result is not None:
        from db.db import get_conn
        with get_conn() as conn:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM items WHERE source_type='reddit' AND date_key=?",
                (date.today().strftime("%Y-%m-%d"),)
            ).fetchone()[0]
        log(f"  Reddit 今日累计 {cnt} 条")
    return []

# ---- 主采集流程 ----

SOURCES = [
    ('news_aggregator', collect_news_agg, '综合情报源'),
    ('reddit',          collect_reddit,  'Reddit'),
    ('douyin',          collect_douyin,  '抖音'),
    ('gzh',             collect_gzh,     '公众号'),
    ('weibo',           collect_weibo,   '微博'),
    ('sspai',           collect_sspai,   '少数派'),
]

def run():
    today = date.today().strftime("%Y-%m-%d")
    log(f"=== 采集开始 {today} ===")
    total_added = 0; total_skip = 0

    for src_key, fn, name in SOURCES:
        log(f"📡 {name}...")
        items = fn()
        added = skip = 0
        for it in items:
            a, s = upsert_item(it, today)
            added += a; skip += s
        log(f"  → 新增 {added}，跳过 {skip}")
        total_added += added; total_skip += skip
        time.sleep(1)

    # 更新每日统计
    import sqlite3
    from db.db import get_conn
    with get_conn() as conn:
        cnt = conn.execute("SELECT COUNT(*) FROM items WHERE date_key=?", (today,)).fetchone()[0]
    upsert_stats(today, cnt)
    log_collect("all", total_added, total_skip, f"今日新增{added}条")
    log(f"=== 完成：新增 {total_added}，跳过 {total_skip} ===")

if __name__ == "__main__":
    run()
