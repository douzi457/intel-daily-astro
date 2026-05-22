# -*- coding: utf-8 -*-
"""
generate_site.py
读取 rewrite/{date}.json → 生成静态 HTML → output/
"""
import json, os
from pathlib import Path
from datetime import date, timedelta

WORKSPACE    = Path(__file__).parent
REWRITE_DIR  = WORKSPACE / "rewrite"
OUT_DIR      = WORKSPACE / "output"
OUT_DAY_DIR  = OUT_DIR / "day"
OUT_DAY_DIR.mkdir(parents=True, exist_ok=True)

# ── 平台元数据 ────────────────────────────────
PLATFORMS = {
    "weibo":        {"label": "🔥 微博",    "color": "#FF9500", "tab": "热搜"},
    "douyin":       {"label": "🎵 抖音",    "color": "#00F2EA", "tab": "热搜"},
    "wallstreetcn": {"label": "📈 华尔街见闻","color": "#3395FF", "tab": "财经"},
    "36kr":         {"label": "📊 36Kr",    "color": "#4A90E2", "tab": "财经"},
    "toutiao":      {"label": "📰 今日头条","color": "#E63946", "tab": "财经"},
    "tencent":      {"label": "🌐 腾讯新闻","color": "#1DB100", "tab": "财经"},
    "ithome":       {"label": "💻 IT之家", "color": "#0090D8", "tab": "开发"},
    "bilibili":     {"label": "📺 B站",    "color": "#FB7299", "tab": "开发"},
    "sspai":        {"label": "🎯 少数派", "color": "#4CAF50", "tab": "开发"},
    "github":       {"label": "🐙 GitHub", "color": "#6CCB5F", "tab": "开发"},
    "hackernews":   {"label": "⚡ HN",     "color": "#FF6600", "tab": "开发"},
    "producthunt":  {"label": "🚀 PH",     "color": "#DA5430", "tab": "开发"},
    "v2ex":         {"label": "💬 V2EX",   "color": "#4CAF50", "tab": "开发"},
    "reddit":        {"label": "🤖 Reddit", "color": "#FF4500", "tab": "开发"},
    "gzh":          {"label": "📮 公众号", "color": "#2ECC71", "tab": "公众号"},
}

TAB_ORDER = ["热搜", "财经", "开发", "公众号"]

def get_tab(src):
    p = src.get("platform") or ""
    orig = src.get("original", "").lower()
    if p in ("weibo", "douyin"):
        return "热搜"
    if p in ("wallstreetcn", "36kr", "toutiao", "tencent"):
        return "财经"
    if p in ("ithome", "bilibili", "sspai", "github", "hackernews", "producthunt", "v2ex", "reddit"):
        return "开发"
    if p in ("gzh",):
        return "公众号"
    return "财经"

def freq_stars(freq):
    f = float(freq or 0)
    if f >= 5: return "🔥🔥🔥"
    if f >= 3: return "🔥🔥"
    if f >= 1: return "🔥"
    return ""

def render_item(src, idx):
    tab  = get_tab(src)
    meta = PLATFORMS.get(src.get("platform",""), {"label": src.get("platform",""), "color": "#94a3b8"})
    badge = f"<span class='ptag' style='color:{meta['color']}'>{meta['label']}</span>"
    stars = freq_stars(src.get("hot", 0))
    return f"""
  <div class="row" data-tab="{tab}" data-platform="{src.get('platform','')}">
    <span class="idx">{idx}</span>
    {badge}
    <span class="main">
      <a href="{src.get('url','#')}" target="_blank" class="tl">{src.get('title','')}</a>
      <div class="aisum">{src.get('desc','')}</div>
    </span>
    <span class="freq">{stars}</span>
    <span class="tm"></span>
  </div>"""

def render_day_page(items, day_str, prev_day, next_day):
    total = len(items)
    tabs_html = "".join(
        f"<button class='tab' data-tab='{t}'>{t}<span class='tc'>{sum(1 for i in items if get_tab(i)==t)}</span></button>"
        for t in TAB_ORDER
    )
    rows_html = "\n".join(render_item(it, i+1) for i, it in enumerate(items))

    stat_items = ""
    from collections import Counter
    tab_cnt = Counter(get_tab(it) for it in items)
    for t in TAB_ORDER:
        cnt = tab_cnt.get(t, 0)
        stat_items += f"<div class='scard'><div class='scnt'>{cnt}</div><div class='slbl'>{t}</div></div>"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>📡 INTEL.SYS {day_str}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;line-height:1.6}}
a{{color:inherit;text-decoration:none}}
.container{{max-width:1200px;margin:0 auto;padding:0 20px 40px}}
img{{max-width:100%}}
header{{text-align:center;padding:28px 0 20px;border-bottom:1px solid #1e3347;margin-bottom:20px}}
.update-badge{{display:inline-block;background:#dc2626;color:#fff;padding:3px 12px;border-radius:20px;font-size:.8em;font-weight:bold;margin-bottom:10px}}
h1{{font-size:1.9em;margin-bottom:6px;color:#f59e0b}}
.subtitle{{color:#94a3b8;font-size:.9em}}
.nav-row{{display:flex;align-items:center;justify-content:center;gap:12px;padding:10px 0}}
.nav-btn{{display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:7px;background:#1e293b;border:1px solid #334155;color:#94a3b8;font-size:13px;transition:.2s}}
.nav-btn:hover{{border-color:#f59e0b;color:#f59e0b}}
.nav-date{{font-size:.95em;font-weight:600;color:#e2e8f0;min-width:160px;text-align:center}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(80px,1fr));gap:8px;margin-bottom:16px}}
.scard{{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:10px 8px;text-align:center}}
.scnt{{font-size:1.4em;font-weight:bold;color:#f59e0b}}
.slbl{{font-size:.75em;color:#94a3b8;margin-top:2px}}
.tabs-wrap{{overflow-x:auto;margin-bottom:14px;-webkit-overflow-scrolling:touch}}
.tabs{{display:flex;gap:6px;padding:2px 0;min-width:max-content}}
.tab{{display:inline-flex;align-items:center;gap:5px;padding:6px 14px;border-radius:20px;border:1px solid #1e3347;background:#1e293b;color:#94a3b8;font-size:.8em;cursor:pointer;transition:.2s;white-space:nowrap}}
.tab:hover{{border-color:#f59e0b;color:#e2e8f0}}
.tab.active{{background:#f59e0b20;border-color:#f59e0b;color:#f59e0b}}
.tab .tc{{margin-left:3px;opacity:.75}}
.search-row{{display:flex;align-items:center;gap:10px;margin-bottom:14px}}
.search-row input{{flex:1;max-width:420px;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:8px 14px;font-size:.85em;color:#e2e8f0;outline:none;transition:.2s}}
.search-row input::placeholder{{color:#475569}}
.search-row input:focus{{border-color:#f59e0b}}
.cnt-hint{{font-size:.8em;color:#475569;white-space:nowrap}}
.sort-hint{{font-size:.78em;color:#475569}}
.item-list{{display:flex;flex-direction:column;gap:4px}}
.row{{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:7px;border:1px solid transparent;transition:.12s;font-size:.82em}}
.row:hover{{background:#1e293b;border-color:#1e3347}}
.row.hidden{{display:none}}
.row .idx{{color:#334155;font-size:.72em;min-width:24px;text-align:right;flex-shrink:0}}
.row .ptag{{font-size:.7em;min-width:72px;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.row .main{{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.row .tl{{color:#c8d6e5;text-decoration:none}}
.row .tl:hover{{color:#f59e0b}}
.row .aisum{{color:#64748b;font-size:.9em;margin-top:3px;white-space:normal;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}}
.row .sc{{font-weight:bold;font-size:.82em;min-width:34px;text-align:center;flex-shrink:0}}
.row .freq{{color:#f59e0b;font-size:.72em;flex-shrink:0;min-width:40px}}
.row .tm{{color:#475569;font-size:.72em;flex-shrink:0;min-width:42px;text-align:right}}
footer{{text-align:center;padding:24px 0;margin-top:32px;border-top:1px solid #1e3347;color:#475569;font-size:.78em}}
</style>
</head>
<body>
<div class="container">
<header>
  <div class="update-badge">⚡ 情报日报</div>
  <h1>📡 INTEL<span style="color:#38bdf8">.SYS</span></h1>
  <p class="subtitle">{total}条 · {day_str}</p>
</header>
<div class="nav-row">
  <a href="{prev_day}.html" class="nav-btn">←</a>
  <span class="nav-date">{day_str}</span>
  <a href="{next_day}.html" class="nav-btn">→</a>
</div>
<div class="stats-grid">{stat_items}</div>
<div class="tabs-wrap">
  <div class="tabs" id="tabs">
    <button class="tab active" data-tab="全部">📡 全部<span class="tc">{total}</span></button>
    {tabs_html}
  </div>
</div>
<div class="search-row">
  <input id="q" placeholder="🔍 搜索标题/描述..." autocomplete="off">
  <span class="cnt-hint" id="cntHint"></span>
</div>
<div class="item-list" id="itemList">
{rows_html}
</div>
<footer>📡 INTEL.SYS · 全自动情报日报</footer>
</div>
<script>
// Tab切换
document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click',()=>{{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  t.classList.add('active');
  const tab=t.dataset.tab;
  document.querySelectorAll('.row').forEach(r=>{{r.classList.toggle('hidden',tab!=='全部'&&r.dataset.tab!==tab)}});
  updateCount();
}}));
// 搜索
const q=document.getElementById('q');
q.addEventListener('input',()=>{{
  const v=q.value.toLowerCase();
  document.querySelectorAll('.row').forEach(r=>{{
    const show=r.textContent.toLowerCase().includes(v);
    r.classList.toggle('hidden',!show);
  }});
  updateCount();
}});
function updateCount(){{
  const visible=document.querySelectorAll('.row:not(.hidden)').length;
  document.getElementById('cntHint').textContent=`${{visible}}条`;
}}
updateCount();
</script>
</body>
</html>"""

def render_index(today_str):
    """生成首页 index.html"""
    rewrite_file = REWRITE_DIR / f"{today_str}.json"
    if rewrite_file.exists():
        data = json.loads(rewrite_file.read_text(encoding="utf-8"))
        items = data.get("items", [])
    else:
        items = []

    from collections import Counter
    tab_cnt = Counter(get_tab(it) for it in items)
    total = len(items)

    sections = ""
    for tab in TAB_ORDER:
        tab_items = [it for it in items if get_tab(it) == tab][:5]
        cards = "".join(
            f"<a href='day/{today_str}.html' class='card'>"
            f"<div class='card-title'>{it.get('title','')[:18]}</div>"
            f"<div class='card-desc'>{it.get('desc','')[:60]}</div></a>"
            for it in tab_items
        )
        sections += f"<section><h2>{tab}</h2><div class='card-grid'>{cards}</div></section>"

    # 历史归档（最新10天）
    day_files = sorted([f.stem for f in OUT_DAY_DIR.glob("*.html")], reverse=True)[:10]
    archive_rows = "".join(
        f"<li><a href='day/{d}.html'>{d}</a></li>" for d in day_files
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>📡 INTEL.SYS · 情报日报</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;line-height:1.6}}
a{{color:inherit;text-decoration:none}}
.container{{max-width:1000px;margin:0 auto;padding:0 20px 60px}}
.hero{{text-align:center;padding:60px 0 40px}}
.hero h1{{font-size:2.5em;color:#f59e0b;margin-bottom:10px}}
.hero p{{color:#94a3b8;font-size:1.1em}}
.stats-row{{display:flex;justify-content:center;gap:30px;margin:20px 0}}
.stat-box{{text-align:center}}
.stat-num{{font-size:2em;font-weight:bold;color:#f59e0b}}
.stat-lbl{{font-size:.8em;color:#94a3b8}}
section{{margin:40px 0}}
section h2{{font-size:1.1em;color:#94a3b8;margin-bottom:16px;border-bottom:1px solid #1e3347;padding-bottom:8px}}
.card-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}}
.card{{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:14px;transition:.2s}}
.card:hover{{border-color:#f59e0b}}
.card-title{{font-size:.9em;font-weight:600;color:#e2e8f0;margin-bottom:6px}}
.card-desc{{font-size:.78em;color:#64748b;line-height:1.5}}
.archive h3{{font-size:.9em;color:#94a3b8;margin-bottom:12px}}
.archive ul{{list-style:none;display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px}}
.archive li a{{display:block;background:#1e293b;border:1px solid #334155;border-radius:6px;padding:8px 12px;font-size:.82em;text-align:center;transition:.2s}}
.archive li a:hover{{border-color:#f59e0b;color:#f59e0b}}
footer{{text-align:center;padding:30px 0;border-top:1px solid #1e3347;color:#475569;font-size:.8em;margin-top:60px}}
</style>
</head>
<body>
<div class="container">
<div class="hero">
  <h1>📡 INTEL<span style="color:#38bdf8">.SYS</span></h1>
  <p>每日自动化情报日报 · 聚合热搜/财经/开发/公众号</p>
  <div class="stats-row">
    <div class="stat-box"><div class="stat-num">{total}</div><div class="stat-lbl">今日条数</div></div>
    <div class="stat-box"><div class="stat-num">{tab_cnt.get('热搜',0)}</div><div class="stat-lbl">热搜</div></div>
    <div class="stat-box"><div class="stat-num">{tab_cnt.get('财经',0)}</div><div class="stat-lbl">财经</div></div>
    <div class="stat-box"><div class="stat-num">{tab_cnt.get('开发',0)}</div><div class="stat-lbl">开发</div></div>
    <div class="stat-box"><div class="stat-num">{tab_cnt.get('公众号',0)}</div><div class="stat-lbl">公众号</div></div>
  </div>
</div>
{sections}
<div class="archive">
  <h3>📁 历史归档</h3>
  <ul>{archive_rows}</ul>
</div>
<footer>📡 INTEL.SYS · 全自动运行，无需人工干预</footer>
</div>
</body>
</html>"""

def render_archive():
    """生成归档页 archive.html"""
    day_files = sorted([f.stem for f in OUT_DAY_DIR.glob("*.html")], reverse=True)
    rows = "".join(
        f"<li><a href='day/{d}.html'>{d}</a></li>" for d in day_files
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>📁 历史归档 · INTEL.SYS</title>
<style>
body{{font-family:-apple-system;background:#0f172a;color:#e2e8f0;padding:40px 20px}}
.container{{max-width:800px;margin:0 auto}}
h1{{color:#f59e0b;margin-bottom:30px}}
ul{{list-style:none;display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px}}
li a{{display:block;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:14px;text-align:center;color:#e2e8f0;transition:.2s}}
li a:hover{{border-color:#f59e0b;color:#f59e0b}}
a.back{{display:inline-block;margin-bottom:20px;color:#94a3b8}}
</style>
</head>
<body>
<div class="container">
<a href="index.html" class="back">← 返回首页</a>
<h1>📁 历史归档</h1>
<ul>{rows}</ul>
</div>
</body>
</html>"""

def main():
    today_str  = date.today().isoformat()
    prev_day   = (date.today() - timedelta(days=1)).isoformat()
    next_day   = (date.today() + timedelta(days=1)).isoformat()

    rewrite_file = REWRITE_DIR / f"{today_str}.json"
    if rewrite_file.exists():
        data  = json.loads(rewrite_file.read_text(encoding="utf-8"))
        items = data.get("items", [])
    else:
        print(f"⚠ 未找到 {rewrite_file}，使用空数据生成页面")
        items = []

    print(f"  生成日报页: {len(items)} 条")
    day_html = render_day_page(items, today_str, prev_day, next_day)
    (OUT_DAY_DIR / f"{today_str}.html").write_text(day_html, encoding="utf-8")

    print(f"  生成首页")
    index_html = render_index(today_str)
    (OUT_DIR / "index.html").write_text(index_html, encoding="utf-8")

    print(f"  生成归档页")
    archive_html = render_archive()
    (OUT_DIR / "archive.html").write_text(archive_html, encoding="utf-8")

    print(f"✅ 生成完成 → output/")

if __name__ == "__main__":
    main()
