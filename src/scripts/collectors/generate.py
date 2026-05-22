"""
HTML生成器 - 情报中心 · 副业风格
"""
import sys, json, html as h
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime, date, timedelta

WORKSPACE = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")
OUTPUT    = WORKSPACE / "output"
TPL_DAY   = WORKSPACE / "templates" / "newsnow.html"
TPL_INDEX = WORKSPACE / "templates" / "index.html"

sys.path.insert(0, str(WORKSPACE))
from db.db import get_items_by_date, get_all_dates, get_conn
from translate import batch_translate, TRANSLATABLE_SOURCES

# 翻译来源列表（用于快速判断）
FOREIGN_SOURCES = TRANSLATABLE_SOURCES

N = {
    'gzh':'公众号','weibo':'微博','douyin':'抖音',
    'hackernews':'HackerNews','github':'GitHub',
    'producthunt':'ProductHunt','36kr':'36Kr',
    'wallstreetcn':'WallStreet','v2ex':'V2EX',
    'tencent':'腾讯新闻','ithome':'IT之家',
    'toutiao':'今日头条','bilibili':'B站',
    'chuangye':'创业邦','sspai':'少数派',
    'reddit':'Reddit',
    'news_aggregator':'综合','unknown':'其他',
}
COL = {
    'gzh':'#FF6B6B','weibo':'#FF9500','douyin':'#00F2EA',
    'hackernews':'#FF6600','github':'#4ECDC4','producthunt':'#FF6B35',
    '36kr':'#2B8CFF','wallstreetcn':'#5856D6','v2ex':'#584528',
    'tencent':'#E43961','ithome':'#0090D8','toutiao':'#E60023',
    'bilibili':'#FB7299','chuangye':'#F5A623','sspai':'#4CAF50',
    'reddit':'#FF4500',
    'news_aggregator':'#607D8B','unknown':'#95A5A6',
}
PRI = ['gzh','36kr','v2ex','weibo','wallstreetcn','sspai','ithome','chuangye',
       'producthunt','github','hackernews','reddit','bilibili','toutiao','tencent',
       'news_aggregator','douyin','unknown']
def gs(item):
    u = item.get('url','') or ''
    if 'github.com' in u: return 'github'
    if 'sspai.com' in u: return 'sspai'
    o = item.get('original_source','') or ''
    if o in N: return o
    st = item.get('source_type','unknown')
    return st if st in N else 'unknown'

def gv(item):
    # 优先用 AI 评分(score字段)，fallback到频次*10
    score = item.get('score') or 0
    if score > 0:
        return int(score * 10)  # 0-100 范围，和原来频率一致
    return int((item.get('frequency') or 1) * 10)

def gt(item):
    t = item.get('pub_time','') or item.get('time','') or ''
    return t[t.index('T')+1:t.index('T')+6] if 'T' in t else (t[-5:] if t else '')

def scoreOf(i):
    pi = PRI.index(gs(i)) if gs(i) in PRI else 999
    return pi * 10000000 + gv(i)

def build_data(items):
    """构建前端 DATA 数组（直接使用数据库已有翻译结果）"""
    items = sorted(items, key=scoreOf, reverse=True)

    rows = []
    for it in items:
        s = gs(it)
        orig_title = it.get('title', 'No title')
        db_desc = it.get('description') or ''  # 数据库已有翻译结果

        # 国外平台：有 description 则用作显示标题，否则用原文
        if s in FOREIGN_SOURCES and db_desc.strip():
            title_text = db_desc
        else:
            title_text = orig_title

        rows.append({
            't': h.escape(title_text),
            'orig': orig_title if s in FOREIGN_SOURCES else '',
            'u': it.get('url','') or '',
            'src': N.get(s, s),
            'srcKey': s,
            'col': COL.get(s,'#475569'),
            'hot': gv(it),
            'score': int(it.get('score') or 0),
            'freq': int(it.get('frequency') or 1),
            'tm': gt(it),
            'ai': it.get('ai_summary') or '',
        })
    return rows

def gen_day_page(date_key, items):
    items = sorted(items, key=scoreOf, reverse=True)
    total = len(items)
    src_cnt = {}
    for it in items:
        s = gs(it)
        src_cnt[s] = src_cnt.get(s, 0) + 1

    dt = datetime.strptime(date_key, '%Y-%m-%d')
    prev = (dt - timedelta(days=1)).strftime('%Y-%m-%d')
    nxt  = (dt + timedelta(days=1)).strftime('%Y-%m-%d')

    top3 = items[:3]
    top_src = []
    for it in top3:
        s = gs(it)
        top_src.append(N.get(s,s))

    data = build_data(items)
    subtitle = ' · '.join(top_src) if top_src else '暂无数据'

    tpl = open(TPL_DAY, encoding='utf-8').read()
    tpl = tpl.replace('__PAGE_TITLE__', 'INTEL.SYS ' + date_key)
    tpl = tpl.replace('__CAL_ACTIVE__', date_key)
    tpl = tpl.replace('__CAL_PREV__', '../day/' + prev + '.html')
    tpl = tpl.replace('__CAL_NEXT__', '../day/' + nxt + '.html')
    tpl = tpl.replace('__SUBTITLE__', subtitle)
    tpl = tpl.replace('__DATA__', json.dumps(data, ensure_ascii=False))
    tpl = tpl.replace('__SRC_MAP__', json.dumps(N, ensure_ascii=False))
    tpl = tpl.replace('__SRC_PRI__', json.dumps(PRI, ensure_ascii=False))
    tpl = tpl.replace('__SRC_CNT__', json.dumps(src_cnt, ensure_ascii=False))
    tpl = tpl.replace('__FOOTER__', 'INTEL.SYS · ' + date_key + ' · ' + str(total) + ' items · 情报中心')
    return tpl

def gen_index():
    all_dates = get_all_dates()
    date_list  = [d['date_key'] for d in all_dates]
    date_cnt   = {d['date_key']: d['cnt'] for d in all_dates}
    today = date.today().strftime("%Y-%m-%d")
    updated = datetime.now().strftime("%Y-%m-%d %H:%M")

    cal_parts = []
    for i in range(29, -1, -1):
        d = date.today() - timedelta(days=i)
        dk = d.strftime("%Y-%m-%d")
        cnt = date_cnt.get(dk, 0)
        cls = ('today' if dk == today else '') + ('' if cnt>0 else ' empty')
        url = 'day/' + dk + '.html' if cnt > 0 else '#'
        label = d.strftime("%m/%d")
        wd = ['一','二','三','四','五','六','日'][d.weekday()]
        icon = ('★ ' + str(cnt)) if cnt > 0 else '—'
        cal_parts.append(
            '<a class="day' + (' ' + cls if cls else '') + '" href="' + url + '">'
            '<span class="dl">' + label + '</span><span class="dw">' + wd + '</span><span class="dc">' + icon + '</span></a>'
        )

    hot = []
    for dk in date_list[:3]:
        hot.extend(get_items_by_date(dk))
    hot = sorted(hot, key=gv, reverse=True)[:5]
    ticker = ' · '.join([N.get(gs(x),'') + ' · ' + (x.get('title','')[:28]) for x in hot])

    recent_parts = []
    for dk in date_list[:5]:
        items = sorted(get_items_by_date(dk), key=scoreOf, reverse=True)[:3]
        total = date_cnt.get(dk, 0)
        prev_html = []
        for it in items:
            s = gs(it)
            co = COL.get(s,'#888')
            prev_html.append(
                '<div><span style="color:' + co + ';font-weight:700;margin-right:6px">' + N.get(s,s)
                + '</span>' + (it.get('title','')[:38]) + '</div>'
            )
        recent_parts.append(
            '<div class="recent-item"><div class="recent-header">'
            '<a href="day/' + dk + '.html">' + dk + '</a>'
            '<span class="total">' + str(total) + ' items</span></div>'
            '<div class="recent-preview">' + ''.join(prev_html) + '</div></div>'
        )

    with get_conn() as conn:
        grand = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]

    tpl = open(TPL_INDEX, encoding='utf-8').read()
    tpl = tpl.replace('__TITLE__', '情报中心 · 首页')
    tpl = tpl.replace('__BRAND__', '情报中心')
    tpl = tpl.replace('__UPDATED__', updated)
    tpl = tpl.replace('__TICKER_LABEL__', '最热：')
    tpl = tpl.replace('__TICKER__', ticker)
    tpl = tpl.replace('__CAL_LABEL__', '日历 · 近30天')
    tpl = tpl.replace('__CAL__', ''.join(cal_parts))
    tpl = tpl.replace('__RECENT_LABEL__', '最近日报')
    tpl = tpl.replace('__RECENT__', ''.join(recent_parts))
    tpl = tpl.replace('__FOOTER__', '情报中心 · 共 ' + str(grand) + ' 条数据')
    return tpl

def generate_all():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "day").mkdir(parents=True, exist_ok=True)
    idx = gen_index()
    with open(OUTPUT / "index.html", 'w', encoding='utf-8') as f:
        f.write(idx)
    print("✅ index.html")
    for d in get_all_dates():
        dk = d['date_key']
        items = get_items_by_date(dk)
        html = gen_day_page(dk, items)
        with open(OUTPUT / "day" / (dk + ".html"), 'w', encoding='utf-8') as f:
            f.write(html)
        print("  📄 " + dk + " — " + str(len(items)) + " items")

def generate_today():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "day").mkdir(parents=True, exist_ok=True)
    dk = date.today().strftime("%Y-%m-%d")
    items = get_items_by_date(dk)
    html = gen_day_page(dk, items)
    with open(OUTPUT / "day" / (dk + ".html"), 'w', encoding='utf-8') as f:
        f.write(html)
    idx = gen_index()
    with open(OUTPUT / "index.html", 'w', encoding='utf-8') as f:
        f.write(idx)
    print("✅ " + dk + " (" + str(len(items)) + " items)")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--today':
        generate_today()
    else:
        generate_all()
