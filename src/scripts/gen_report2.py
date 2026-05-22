"""
AI情报日报 v3 — 全量平台列表版
===============================
- 今日所有条目全量展示
- 平台Tab切换（全部/各平台）
- 关键词搜索
- HN/GH/PH 英文内容翻译显示
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from datetime import date, datetime, timedelta
import json, re

WORKSPACE = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")
OUTPUT    = WORKSPACE / "output" / "day"
TPL_PATH  = WORKSPACE / "templates" / "newsnow_v2.html"

sys.path.insert(0, str(WORKSPACE))
from db.db import get_conn

# ─────────────────────────────────────────────
# 平台配置
# ─────────────────────────────────────────────
PLATFORMS = [
    ('all',          '全部',        '📡',  '#64748b'),
    ('gzh',          '公众号',      '📮',  '#FF6B6B'),
    ('weibo',        '微博',        '🔥',  '#FF9500'),
    ('douyin',       '抖音',        '🎵',  '#00F2EA'),
    ('hackernews',   'HackerNews',  '▲',  '#FF6600'),
    ('github',       'GitHub',      '⚙️',  '#4ECDC4'),
    ('producthunt',  'ProductHunt', '🚀',  '#FF6B35'),
    ('36kr',         '36Kr',        '📊',  '#2B8CFF'),
    ('wallstreetcn', '华尔街见闻',  '📈',  '#5856D6'),
    ('v2ex',         'V2EX',        '💬',  '#584528'),
    ('ithome',       'IT之家',      '💻',  '#0090D8'),
    ('toutiao',      '今日头条',    '📰',  '#E60023'),
    ('bilibili',     'B站',         '📺',  '#FB7299'),
    ('chuangye',     '创业邦',      '🏭',  '#F5A623'),
    ('sspai',        '少数派',      '🎯',  '#4CAF50'),
    ('reddit',       'Reddit',      '💬',  '#FF4500'),
    ('tencent',      '腾讯新闻',    '🌐',  '#E43961'),
]

def gs(item):
    """来源标准化"""
    u = item.get('url', '') or ''
    o = item.get('original_source', '') or ''
    st = item.get('source_type', '') or ''

    if 'github.com' in u: return 'github'
    if 'sspai.com' in u: return 'sspai'
    if o == 'weibo_hot': return 'weibo'
    if o in [p[0] for p in PLATFORMS]: return o
    if '/' in o:
        base = o.split('/')[0]
        if base in [p[0] for p in PLATFORMS]: return base
    if st in [p[0] for p in PLATFORMS]: return st
    if st == 'douyin': return 'douyin'
    return 'unknown'

def gv(item):
    """热度分"""
    score = item.get('score') or 0
    if score > 0:
        return int(score * 10)
    return int((item.get('frequency') or 1) * 10)

def scoreOf(item):
    s = gs(item)
    pri = ['gzh','weibo','douyin','hackernews','github','producthunt',
           '36kr','wallstreetcn','v2ex','ithome','toutiao','bilibili',
           'chuangye','sspai','reddit','tencent','news_aggregator','unknown']
    pi = pri.index(s) if s in pri else 999
    return pi * 100000 + gv(item)

# ─────────────────────────────────────────────
# 数据库读取（只取今天的数据）
# ─────────────────────────────────────────────
conn = get_conn()
c = conn.cursor()

def fetch_today_items(date_key):
    c.execute("""
        SELECT id, title, description, url, source_type, original_source,
               COALESCE(score,0), frequency, ai_summary, pub_time,
               created_at
        FROM items
        WHERE DATE(created_at) = ?
        ORDER BY created_at DESC
    """, (date_key,))
    items = []
    for r in c.fetchall():
        items.append({
            'id': r[0], 'title': r[1] or '', 'description': r[2] or '',
            'url': r[3] or '', 'source_type': r[4] or '',
            'original_source': r[5] or '', 'score': r[6],
            'frequency': r[7] or 1, 'ai_summary': r[8] or '',
            'pub_time': r[9] or '',
            'created_at': r[10] or '',
        })
    return items

def display_title(item):
    """显示标题：直接返回原文（翻译需要API，这里显示原文）"""
    return item.get('title') or ''

def display_desc(item):
    """显示描述：直接返回原文"""
    return item.get('description') or ''

# ─────────────────────────────────────────────
# 渲染单条
# ─────────────────────────────────────────────
def render_row(it, idx):
    s = gs(it)
    title  = display_title(it)
    desc   = display_desc(it)
    url    = it.get('url') or ''
    score  = int(it.get('score') or 0)
    freq   = it.get('frequency') or 1
    ai_sum = it.get('ai_summary') or ''
    pt     = it.get('pub_time', '') or ''
    tm     = pt[11:16] if 'T' in pt else ''

    # 平台色彩
    pconf = next((p for p in PLATFORMS if p[0] == s), None)
    if not pconf:
        pconf = ('unknown', s, '📌', '#607D8B')
    pid, pname, picon, pcol = pconf

    display = desc if len(desc) > 15 else title
    if not display:
        display = title

    fires = '🔥' * min(int(freq), 3)
    sc_col = '#ef4444' if score >= 8 else ('#f59e0b' if score >= 5 else '#475569')
    sc_badge = f'<span class="sc" style="color:{sc_col}">{score}分</span>' if score > 0 else ''

    # AI摘要（卡片形式）
    ai_html = ''
    if ai_sum:
        ai_html = f'<div class="aisum">💡 {ai_sum}</div>'

    # 链接
    if url:
        title_html = f'<a href="{url}" target="_blank" class="tl">{display}</a>'
    else:
        title_html = f'<span class="tl">{display}</span>'

    qtext = (title + ' ' + desc).replace('"','&quot;').lower()
    return f"""<div class="row" data-platform="{pid}" data-q=\"{qtext}\">
  <span class="idx">{idx}</span>
  <span class="ptag" style="color:{pcol}">{picon} {pname}</span>
  <span class="main">{title_html}{ai_html}</span>
  {sc_badge}
  <span class="freq">{fires}</span>
  <span class="tm">{tm}</span>
</div>"""

# ─────────────────────────────────────────────
# 构建今日页面
# ─────────────────────────────────────────────
def build_page(date_key, items):
    total = len(items)

    # 按平台统计
    src_cnt = {}
    for it in items:
        s = gs(it)
        src_cnt[s] = src_cnt.get(s, 0) + 1

    # 全部平台的Tab
    tabs_html = ''
    for pid, pname, picon, pcol in PLATFORMS:
        cnt = src_cnt.get(pid, 0) if pid != 'all' else total
        if pid == 'all':
            tabs_html += f'<button class="tab active" data-platform="all">{picon} {pname}<span class="tc">{cnt}</span></button>'
        elif cnt > 0:
            tabs_html += f'<button class="tab" data-platform="{pid}">{picon} {pname}<span class="tc">{cnt}</span></button>'

    # 全部行HTML（用于前端过滤）
    all_rows = '\n'.join(render_row(it, i+1) for i, it in enumerate(items))

    # 统计卡片
    stat_cards = ''.join(
        f'<div class="scard"><div class="sn">{n}</div><div class="sl">{pname}</div></div>'
        for pid, pname, picon, pcol in PLATFORMS[1:]
        if (n := src_cnt.get(pid, 0)) > 0
    )

    dt   = datetime.strptime(date_key, '%Y-%m-%d')
    prev = (dt - timedelta(days=1)).strftime('%Y-%m-%d')
    nxt  = (dt + timedelta(days=1)).strftime('%Y-%m-%d')
    now_s = datetime.now().strftime('%H:%M')

    html = open(TPL_PATH, encoding='utf-8').read()
    html = html.replace('__PAGE_TITLE__', f'📡 INTEL.SYS {date_key}')
    html = html.replace('__SUBTITLE__', f'{total}条 · 更新于{now_s}')
    html = html.replace('__DATE_TODAY__', date_key)
    html = html.replace('__CAL_PREV__', prev + '.html')
    html = html.replace('__CAL_NEXT__', nxt + '.html')
    html = html.replace('__TOTAL_COUNT__', str(total))
    html = html.replace('__ALL_ROWS__', all_rows)
    html = html.replace('__TABS_HTML__', tabs_html)
    html = html.replace('__STAT_CARDS__', stat_cards)
    html = html.replace('__FOOTER__', f'INTEL.SYS · {date_key} · {total}条 · 平台Tab切换 · Ctrl+F搜索')
    return html

# ─────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────
if __name__ == "__main__":
    OUTPUT.mkdir(parents=True, exist_ok=True)
    dk = date.today().strftime("%Y-%m-%d")

    items = fetch_today_items(dk)
    html  = build_page(dk, items)

    out_path = OUTPUT / (dk + ".html")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # 按平台统计
    src_cnt = {}
    for it in items:
        s = gs(it)
        src_cnt[s] = src_cnt.get(s, 0) + 1
    top5 = sorted(src_cnt.items(), key=lambda x: -x[1])[:5]
    print(f"✅ {dk} — {len(items)}条")
    for s, n in top5:
        pconf = next((p for p in PLATFORMS if p[0] == s), None)
        pname = pconf[1] if pconf else s
        print(f"   {pname}: {n}")
