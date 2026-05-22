# -*- coding: utf-8 -*-
"""
generate_site_v2.py
Superpowers 站点生成器 — 基于情报系统数据库
读取 intel.db → 生成静态网站 → output/

结构：
  output/
  ├── index.html              首页（四模块入口 + 今日摘要 + 福利区）
  ├── archive.html            历史归档
  ├── stats.html             统计面板
  ├── day/YYYY-MM-DD.html   每日日报（Tab筛选 + 搜索）
  ├── css/style.css         统一样式
  └── js/main.js            交互脚本
"""
import sqlite3, os, json
from pathlib import Path
from datetime import date, timedelta
from collections import Counter

# ── 路径配置 ─────────────────────────────────
WORKSPACE   = Path(__file__).parent
DB_PATH     = WORKSPACE / "db" / "intel.db"
OUT_DIR     = WORKSPACE / "output"
OUT_DAY_DIR = OUT_DIR / "day"
CSS_DIR     = OUT_DIR / "css"
JS_DIR      = OUT_DIR / "js"
for d in [OUT_DIR, OUT_DAY_DIR, CSS_DIR, JS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── 平台元数据 ─────────────────────────────────
PLATFORMS = {
    "weibo":        {"label": "微博",     "color": "#FF9500", "tab": "热搜",  "icon": "🔥"},
    "douyin":       {"label": "抖音",     "color": "#00F2EA", "tab": "热搜",  "icon": "🎵"},
    "wallstreetcn": {"label": "华尔街见闻","color": "#3395FF", "tab": "财经",  "icon": "📈"},
    "36kr":         {"label": "36Kr",     "color": "#4A90E2", "tab": "财经",  "icon": "📊"},
    "toutiao":      {"label": "今日头条", "color": "#E63946", "tab": "财经",  "icon": "📰"},
    "tencent":      {"label": "腾讯新闻", "color": "#1DB100", "tab": "财经",  "icon": "🌐"},
    "ithome":       {"label": "IT之家",   "color": "#0090D8", "tab": "开发",  "icon": "💻"},
    "github":       {"label": "GitHub",   "color": "#6CCB5F", "tab": "开发",  "icon": "🐙"},
    "hackernews":   {"label": "HN",        "color": "#FF6600", "tab": "开发",  "icon": "⚡"},
    "producthunt":  {"label": "ProductHunt","color": "#DA5430","tab": "开发",  "icon": "🚀"},
    "v2ex":         {"label": "V2EX",      "color": "#4CAF50", "tab": "开发",  "icon": "💬"},
    "gzh":          {"label": "公众号",    "color": "#2ECC71", "tab": "公众号","icon": "📮"},
}
TABS = ["热搜", "财经", "开发", "公众号"]
TAB_COLORS = {"热搜": "#FF9500", "财经": "#3395FF", "开发": "#6CCB5F", "公众号": "#2ECC71"}

# ── 数据库读取 ─────────────────────────────────
def get_items(day_str=None):
    """从 intel.db 读取数据，返回 items 列表"""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if day_str:
        cur.execute(
            "SELECT * FROM items WHERE date_key=? ORDER BY score DESC",
            (day_str,)
        )
    else:
        cur.execute("SELECT * FROM items ORDER BY date_key DESC, score DESC")
    rows = cur.fetchall()
    conn.close()
    items = []
    for r in rows:
        d = dict(r)
        p = d.get("source_type", "")
        tab = next((v["tab"] for k, v in PLATFORMS.items() if k == p), "财经")
        meta = PLATFORMS.get(p, {"label": p, "color": "#94a3b8", "tab": tab, "icon": "📌"})
        items.append({
            "id": d.get("id"),
            "title": d.get("title", ""),
            "desc": d.get("ai_summary", "") or d.get("description", ""),
            "url": d.get("url", ""),
            "platform": p,
            "platform_label": meta["label"],
            "platform_color": meta["color"],
            "platform_icon": meta["icon"],
            "tab": tab,
            "hot": d.get("hot_value", 0),
            "date": d.get("date_key", ""),
            "score": d.get("score", 0),
        })
    return items

def get_all_dates():
    """获取所有有数据的日期"""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT date_key FROM items ORDER BY date_key DESC")
    dates = [r[0] for r in cur.fetchall()]
    conn.close()
    return dates

def get_stats():
    """获取全局统计"""
    if not DB_PATH.exists():
        return {}
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM items")
    total = cur.fetchone()[0]
    cur.execute("SELECT source_type, COUNT(*) as c FROM items GROUP BY source_type ORDER BY c DESC")
    platform_dist = dict(cur.fetchall())
    conn.close()
    return {"total": total, "platform_dist": platform_dist}

# ── CSS 样式 ─────────────────────────────────
CSS = """
/* ── 变量 & 重置 ── */
:root {
  --bg: #0b0f1a;
  --surface: #131929;
  --surface2: #1a2235;
  --border: #232d42;
  --accent: #f59e0b;
  --accent2: #38bdf8;
  --text: #e2e8f0;
  --text2: #8899b4;
  --text3: #4a5a78;
  --热搜: #FF9500;
  --财经: #3395FF;
  --开发: #6CCB5F;
  --公众号: #2ECC71;
}
*{margin:0;padding:0;box-sizing:border-box}
a{color:inherit;text-decoration:none}
body{font-family:'PingFang SC','Microsoft YaHei',-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}

/* ── 布局 ── */
.layout{display:flex;min-height:100vh}
.sidebar{width:220px;flex-shrink:0;background:var(--surface);border-right:1px solid var(--border);position:sticky;top:0;height:100vh;overflow-y:auto;padding:20px 0;display:flex;flex-direction:column}
.main{flex:1;padding:28px 32px 60px;overflow:hidden}
.container{max-width:1100px}

/* ── 侧边栏 ── */
.logo{padding:0 20px 20px;border-bottom:1px solid var(--border);margin-bottom:16px}
.logo h1{font-size:1.1em;color:var(--accent);letter-spacing:.5px}
.logo span{font-size:.75em;color:var(--text3);display:block;margin-top:2px}
.nav-section{margin-bottom:20px}
.nav-title{font-size:.68em;color:var(--text3);text-transform:uppercase;letter-spacing:1px;padding:0 20px;margin-bottom:6px}
.nav-item{display:flex;align-items:center;gap:8px;padding:8px 20px;font-size:.82em;color:var(--text2);transition:.15s;cursor:pointer}
.nav-item:hover{background:var(--surface2);color:var(--text)}
.nav-item.active{background:var(--accent)18;color:var(--accent);border-right:2px solid var(--accent)}
.nav-item .dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.nav-item .badge{margin-left:auto;background:var(--surface2);color:var(--text3);font-size:.7em;padding:1px 6px;border-radius:10px}
.nav-footer{padding:20px;margin-top:auto;font-size:.72em;color:var(--text3);border-top:1px solid var(--border)}

/* ── 主区域 ── */
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:28px;flex-wrap:wrap;gap:12px}
.topbar h2{font-size:1.3em;color:var(--text)}
.topbar h2 span{color:var(--accent)}
.topbar-meta{font-size:.8em;color:var(--text3)}

/* ── 统计卡片 ── */
.stats-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;margin-bottom:32px}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:18px 16px;transition:.2s}
.stat-card:hover{border-color:var(--accent);transform:translateY(-2px)}
.stat-card .sc-num{font-size:1.8em;font-weight:700;color:var(--accent)}
.stat-card .sc-lbl{font-size:.75em;color:var(--text2);margin-top:4px}
.stat-card .sc-icon{font-size:1.4em;margin-bottom:8px}

/* ── 四模块入口 ── */
.module-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:36px}
.module-card{background:var(--surface);border:2px solid var(--border);border-radius:14px;padding:22px;transition:.2s;cursor:pointer}
.module-card:hover{border-color:var(--module-color);transform:translateY(-3px);box-shadow:0 8px 30px #0004}
.module-card .mc-icon{font-size:2em;margin-bottom:10px}
.module-card .mc-name{font-size:1.05em;font-weight:600;margin-bottom:6px;color:var(--text)}
.module-card .mc-desc{font-size:.78em;color:var(--text2);margin-bottom:10px}
.module-card .mc-bar{height:4px;background:var(--surface2);border-radius:2px;overflow:hidden}
.module-card .mc-bar-fill{height:100%;border-radius:2px;background:var(--module-color);transition:width .6s ease}
.module-card .mc-count{font-size:.75em;color:var(--text3);margin-top:6px}

/* ── Tab 标签页 ── */
.tabs{display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap}
.tab-btn{padding:7px 16px;border-radius:20px;border:1px solid var(--border);background:var(--surface);color:var(--text2);font-size:.8em;cursor:pointer;transition:.15s;display:flex;align-items:center;gap:6px}
.tab-btn:hover{border-color:var(--accent);color:var(--text)}
.tab-btn.active{background:var(--accent)20;border-color:var(--accent);color:var(--accent)}
.tab-btn .cnt{background:var(--surface2);padding:1px 6px;border-radius:8px;font-size:.9em}

/* ── 搜索框 ── */
.search-bar{display:flex;align-items:center;gap:10px;margin-bottom:20px}
.search-bar input{flex:1;max-width:480px;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 16px;font-size:.85em;color:var(--text);outline:none;transition:.2s}
.search-bar input:focus{border-color:var(--accent)}
.search-bar input::placeholder{color:var(--text3)}
.result-hint{font-size:.8em;color:var(--text3)}

/* ── 内容列表 ── */
.item-list{display:flex;flex-direction:column;gap:6px}
.item-card{display:flex;align-items:flex-start;gap:12px;padding:14px 16px;background:var(--surface);border:1px solid var(--border);border-radius:10px;transition:.15s}
.item-card:hover{border-color:var(--item-color,var(--accent));background:var(--surface2)}
.item-card.hidden{display:none}
.item-idx{color:var(--text3);font-size:.72em;min-width:22px;text-align:right;flex-shrink:0;padding-top:3px}
.item-badge{min-width:78px;flex-shrink:0;text-align:center;font-size:.72em;padding:3px 8px;border-radius:6px;background:var(--badge-bg,var(--surface2));color:var(--badge-color,var(--text2));font-weight:600}
.item-body{flex:1;min-width:0}
.item-title{font-size:.88em;font-weight:500;color:var(--text);margin-bottom:4px;line-height:1.4}
.item-title a:hover{color:var(--accent)}
.item-desc{font-size:.78em;color:var(--text2);line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.item-meta{display:flex;align-items:center;gap:12px;margin-top:6px}
.item-hot{font-size:.72em;color:var(--accent)}
.item-time{font-size:.72em;color:var(--text3)}

/* ── 导航箭头（日报页）── */
.day-nav{display:flex;align-items:center;justify-content:center;gap:20px;margin-bottom:24px}
.day-nav a{display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:var(--surface);border:1px solid var(--border);color:var(--text2);font-size:14px;transition:.15s}
.day-nav a:hover{border-color:var(--accent);color:var(--accent)}
.day-nav .current{font-size:.9em;font-weight:600;color:var(--text)}

/* ── 历史归档 ── */
.archive-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:20px}
.archive-day a{display:flex;flex-direction:column;align-items:center;padding:14px 10px;background:var(--surface);border:1px solid var(--border);border-radius:10px;text-align:center;transition:.15s;font-size:.82em;color:var(--text2)}
.archive-day a:hover{border-color:var(--accent);color:var(--accent);transform:translateY(-2px)}
.archive-day .ad-dow{font-size:.7em;color:var(--text3);margin-top:2px}

/* ── 福利区 ── */
.welfare{padding:24px;background:var(--surface);border:1px solid var(--border);border-radius:14px;margin-top:32px}
.welfare h3{font-size:.9em;color:var(--text2);margin-bottom:14px;display:flex;align-items:center;gap:6px}
.welfare-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}
.welfare-item{display:flex;align-items:center;gap:10px;padding:10px 14px;background:var(--surface2);border-radius:8px;font-size:.82em;transition:.15s}
.welfare-item:hover{border-color:var(--accent)}

/* ── 页脚 ── */
footer{border-top:1px solid var(--border);padding:24px 0;margin-top:40px;text-align:center;font-size:.78em;color:var(--text3)}

/* ── 响应式 ── */
@media(max-width:768px){
  .layout{flex-direction:column}
  .sidebar{width:100%;height:auto;position:static;border-right:none;border-bottom:1px solid var(--border)}
  .module-grid{grid-template-columns:1fr}
  .stats-grid{grid-template-columns:repeat(2,1fr)}
  .main{padding:20px 16px}
}
"""

# ── JavaScript ─────────────────────────────────
JS = """
document.addEventListener('DOMContentLoaded', function(){

  // Tab 切换
  document.querySelectorAll('.tab-btn').forEach(function(btn){
    btn.addEventListener('click', function(){
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      var tab = btn.dataset.tab;
      document.querySelectorAll('.item-card[data-tab]').forEach(function(card){
        card.classList.toggle('hidden', tab !== '全部' && card.dataset.tab !== tab);
      });
      updateCount();
    });
  });

  // 搜索
  var qInput = document.getElementById('q');
  if(qInput){
    qInput.addEventListener('input', function(){
      var v = qInput.value.toLowerCase().trim();
      document.querySelectorAll('.item-card').forEach(function(card){
        var show = !v || card.textContent.toLowerCase().includes(v);
        card.classList.toggle('hidden', !show);
      });
      updateCount();
    });
  }

  function updateCount(){
    var hint = document.getElementById('cntHint');
    if(!hint) return;
    var visible = document.querySelectorAll('.item-card:not(.hidden)').length;
    hint.textContent = visible + '条';
  }

  // 当前选中侧边栏
  var path = window.location.pathname;
  document.querySelectorAll('.nav-item[data-page]').forEach(function(item){
    var pg = item.dataset.page;
    if(path.endsWith(pg) || (pg === 'index.html' && (path === '/' || path.endsWith('index.html')))){
      item.classList.add('active');
    }
  });
});
"""

# ── HTML 组件 ─────────────────────────────────
def css_link(css_path):
    return f'<link rel="stylesheet" href="{css_path}">'

def script_tag(js_path):
    return f'<script src="{js_path}"></script>'

def make_sidebar(active_page="index.html", day_counts=None):
    if day_counts is None:
        day_counts = {}
    dates = get_all_dates()[:7]  # 最近7天
    dow = ["周一","周二","周三","周四","周五","周六","周日"]

    nav_items = [
        ("📡", "首页", "index.html", "全部"),
        ("📈", "今日日报", "day/{today}.html".format(today=date.today().isoformat()), "日报"),
        ("📁", "归档", "archive.html", "归档"),
        ("📊", "统计", "stats.html", "统计"),
    ]

    nav_html = ""
    for icon, label, href, page in nav_items:
        nav_html += f'<div class="nav-item" data-page="{page}"><span>{icon}</span>{label}</div>\n'

    # 最近日期
    recent_html = ""
    for d in dates:
        dow_idx = date.fromisoformat(d).weekday()
        recent_html += f'<div class="nav-item" data-page="day"><a href="day/{d}.html">{d} {dow[dow_idx]}</a></div>\n'

    return f"""
<aside class="sidebar">
  <div class="logo">
    <h1>📡 INTEL<span style="color:var(--accent2)">.SYS</span></h1>
    <span>Superpowers 情报站</span>
  </div>
  <div class="nav-section">
    <div class="nav-title">导航</div>
    {nav_html}
  </div>
  <div class="nav-section">
    <div class="nav-title">最近日报</div>
    {recent_html}
  </div>
  <div class="nav-footer">
    自动生成 · 无需人工干预<br>
    更新周期：每2小时
  </div>
</aside>"""

def make_day_nav(prev_day, next_day, today_str):
    prev_link = f'<a href="{prev_day}.html">←</a>' if prev_day else '<span style="width:36px;display:inline-block"></span>'
    next_link = f'<a href="{next_day}.html">→</a>' if next_day else '<span style="width:36px;display:inline-block"></span>'
    return f"""
<div class="day-nav">
  {prev_link}
  <span class="current">{today_str}</span>
  {next_link}
</div>"""

# ── 页面渲染 ─────────────────────────────────

def render_css():
    """生成统一样式文件"""
    (CSS_DIR / "style.css").write_text(CSS, encoding="utf-8")
    print(f"  ✅ css/style.css")

def render_js():
    """生成交互脚本"""
    (JS_DIR / "main.js").write_text(JS, encoding="utf-8")
    print(f"  ✅ js/main.js")

def render_index(today_str, items, all_dates):
    stats = get_stats()
    total = stats["total"]
    tab_counts = Counter(it["tab"] for it in items)

    # 四大模块卡片
    module_colors = {"热搜": "#FF9500", "财经": "#3395FF", "开发": "#6CCB5F", "公众号": "#2ECC71"}
    module_icons = {"热搜": "🔥", "财经": "📈", "开发": "💻", "公众号": "📮"}
    module_descs = {
        "热搜": "微博 · 抖音热搜榜单",
        "财经": "36Kr · 华尔街见闻 · 今日头条",
        "开发": "GitHub · HN · ProductHunt · V2EX",
        "公众号": "AI · 创业 · 副业精选"
    }
    module_max = {t: max(tab_counts.get(t, 0), 1) for t in TABS}
    module_html = ""
    for tab in TABS:
        cnt = tab_counts.get(tab, 0)
        color = module_colors[tab]
        icon = module_icons[tab]
        desc = module_descs[tab]
        pct = min(int(cnt / module_max[tab] * 100), 100) if module_max[tab] > 0 else 0
        module_html += f"""
      <div class="module-card" style="--module-color:{color}" onclick="location.href='day/{today_str}.html'">
        <div class="mc-icon">{icon}</div>
        <div class="mc-name">{tab}</div>
        <div class="mc-desc">{desc}</div>
        <div class="mc-bar"><div class="mc-bar-fill" style="width:{pct}%"></div></div>
        <div class="mc-count">{cnt} 条内容</div>
      </div>"""

    # 今日内容预览（每模块取3条）
    preview_html = ""
    for tab in TABS:
        tab_items = [it for it in items if it["tab"] == tab][:3]
        if not tab_items:
            continue
        items_html = ""
        for i, it in enumerate(tab_items, 1):
            items_html += f"""
        <div class="item-card" data-tab="{tab}" style="--item-color:{module_colors[tab]}">
          <div class="item-idx">{i}</div>
          <div class="item-badge" style="--badge-bg:{module_colors[tab]}20;--badge-color:{module_colors[tab]}">{it['platform_icon']} {it['platform_label']}</div>
          <div class="item-body">
            <div class="item-title"><a href="{it['url']}" target="_blank">{it['title']}</a></div>
            <div class="item-desc">{it['desc']}</div>
          </div>
        </div>"""
        preview_html += f'<div class="tab-section" id="tab-{tab}">{items_html}</div>'

    # 历史归档
    archive_html = ""
    for d in all_dates[:14]:
        archive_html += f'<div class="archive-day"><a href="day/{d}.html">{d}<span class="ad-dow">{["周一","周二","周三","周四","周五","周六","周日"][date.fromisoformat(d).weekday()]}</span></a></div>'

    # 福利区
    welfare_html = """
      <div class="welfare-grid">
        <div class="welfare-item">🔗 <span>福利链接配置区（待添加）</span></div>
      </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>📡 INTEL.SYS · 每日情报</title>
{css_link('css/style.css')}
</head>
<body>
<div class="layout">
{make_sidebar('index.html')}
<div class="main">
  <div class="container">
    <div class="topbar">
      <h2>📡 今日<span>情报</span> {today_str}</h2>
      <span class="topbar-meta">系统自动生成 · 每2小时更新</span>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="sc-icon">📡</div>
        <div class="sc-num">{len(items)}</div>
        <div class="sc-lbl">今日条数</div>
      </div>
      <div class="stat-card">
        <div class="sc-icon">🔥</div>
        <div class="sc-num">{tab_counts.get('热搜',0)}</div>
        <div class="sc-lbl">热搜</div>
      </div>
      <div class="stat-card">
        <div class="sc-icon">📈</div>
        <div class="sc-num">{tab_counts.get('财经',0)}</div>
        <div class="sc-lbl">财经</div>
      </div>
      <div class="stat-card">
        <div class="sc-icon">💻</div>
        <div class="sc-num">{tab_counts.get('开发',0)}</div>
        <div class="sc-lbl">开发</div>
      </div>
      <div class="stat-card">
        <div class="sc-icon">📮</div>
        <div class="sc-num">{tab_counts.get('公众号',0)}</div>
        <div class="sc-lbl">公众号</div>
      </div>
      <div class="stat-card">
        <div class="sc-icon">📁</div>
        <div class="sc-num">{len(all_dates)}</div>
        <div class="sc-lbl">历史天数</div>
      </div>
    </div>

    <h3 style="font-size:.85em;color:var(--text3);margin-bottom:14px">🎯 四大模块</h3>
    <div class="module-grid">
      {module_html}
    </div>

    <h3 style="font-size:.85em;color:var(--text3);margin-bottom:14px">📋 今日内容预览</h3>
    <div class="tabs">
      <button class="tab-btn active" data-tab="全部">📡 全部<span class="cnt">{len(items)}</span></button>
      {''.join(f"<button class='tab-btn' data-tab='{t}'>{module_icons[t]} {t}<span class='cnt'>{tab_counts.get(t,0)}</span></button>" for t in TABS)}
    </div>
    <div class="search-bar">
      <input id="q" placeholder="🔍 搜索标题/描述..." autocomplete="off">
      <span class="result-hint" id="cntHint"></span>
    </div>
    <div class="item-list" id="itemList">
      {preview_html}
    </div>

    <div class="welfare">
      <h3>🎁 福利区</h3>
      {welfare_html}
    </div>

    <h3 style="font-size:.85em;color:var(--text3);margin:28px 0 14px">📁 历史归档</h3>
    <div class="archive-list">
      {archive_html}
    </div>

    <footer>📡 INTEL.SYS · Superpowers 情报系统 · {stats['total']} 条全量数据</footer>
  </div>
</div>
</div>
{script_tag('js/main.js')}
</body>
</html>"""
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"  ✅ index.html ({len(items)}条今日数据)")

def render_day_page(day_str, items, prev_day, next_day):
    tab_counts = Counter(it["tab"] for it in items)
    module_icons = {"热搜": "🔥", "财经": "📈", "开发": "💻", "公众号": "📮"}
    module_colors = {"热搜": "#FF9500", "财经": "#3395FF", "开发": "#6CCB5F", "公众号": "#2ECC71"}

    rows_html = ""
    for i, it in enumerate(items, 1):
        color = it["platform_color"]
        tab = it["tab"]
        hot_str = "🔥" * min(int(it.get("hot", 0) / 10 + 1), 3) if it.get("hot", 0) else ""
        rows_html += f"""
      <div class="item-card" data-tab="{tab}" data-platform="{it['platform']}" style="--item-color:{color}">
        <div class="item-idx">{i}</div>
        <div class="item-badge" style="--badge-bg:{color}22;--badge-color:{color}">{it['platform_icon']} {it['platform_label']}</div>
        <div class="item-body">
          <div class="item-title"><a href="{it['url']}" target="_blank">{it['title']}</a></div>
          <div class="item-desc">{it['desc']}</div>
          <div class="item-meta">
            {f'<span class="item-hot">{hot_str}</span>' if hot_str else ''}
            <span class="item-time">{it.get('date','')}</span>
          </div>
        </div>
      </div>"""

    stat_cards = ""
    for t in TABS:
        cnt = tab_counts.get(t, 0)
        color = module_colors[t]
        stat_cards += f"""
      <div class="stat-card" style="cursor:pointer" onclick="document.querySelector('[data-tab={t}]').click()">
        <div class="sc-icon">{module_icons[t]}</div>
        <div class="sc-num" style="color:{color}">{cnt}</div>
        <div class="sc-lbl">{t}</div>
      </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>📡 INTEL.SYS · {day_str}</title>
{css_link('../css/style.css')}
</head>
<body>
<div class="layout">
{make_sidebar('day')}
<div class="main">
  <div class="container">
    <div class="topbar">
      <h2>📡 <span>{day_str}</span> 情报日报</h2>
      <span class="topbar-meta">{len(items)} 条内容</span>
    </div>

    {make_day_nav(prev_day, next_day, day_str)}

    <div class="stats-grid">{stat_cards}</div>

    <div class="tabs">
      <button class="tab-btn active" data-tab="全部">📡 全部<span class="cnt">{len(items)}</span></button>
      {''.join(f"<button class='tab-btn' data-tab='{t}'>{module_icons[t]} {t}<span class='cnt'>{tab_counts.get(t,0)}</span></button>" for t in TABS)}
    </div>
    <div class="search-bar">
      <input id="q" placeholder="🔍 搜索标题/描述..." autocomplete="off">
      <span class="result-hint" id="cntHint"></span>
    </div>
    <div class="item-list" id="itemList">
      {rows_html}
    </div>

    <footer>📡 INTEL.SYS · {day_str}</footer>
  </div>
</div>
</div>
{script_tag('../js/main.js')}
</body>
</html>"""
    out_path = OUT_DAY_DIR / f"{day_str}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"  ✅ day/{day_str}.html ({len(items)}条)")

def render_archive():
    all_dates = get_all_dates()
    dow = ["周一","周二","周三","周四","周五","周六","周日"]
    archive_html = ""
    for d in all_dates:
        dow_idx = date.fromisoformat(d).weekday()
        archive_html += f'<div class="archive-day"><a href="day/{d}.html">{d}<span class="ad-dow">{dow[dow_idx]}</span></a></div>'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>📁 历史归档 · INTEL.SYS</title>
{css_link('css/style.css')}
</head>
<body>
<div class="layout">
{make_sidebar('archive')}
<div class="main">
  <div class="container">
    <div class="topbar">
      <h2>📁 历史<span>归档</span></h2>
      <span class="topbar-meta">{len(all_dates)} 天历史数据</span>
    </div>
    <div class="archive-list">{archive_html}</div>
    <footer>📡 INTEL.SYS · 历史归档</footer>
  </div>
</div>
</div>
{script_tag('js/main.js')}
</body>
</html>"""
    (OUT_DIR / "archive.html").write_text(html, encoding="utf-8")
    print(f"  ✅ archive.html ({len(all_dates)}天)")

def render_stats():
    stats = get_stats()
    all_dates = get_all_dates()
    platform_dist = stats.get("platform_dist", {})

    # 平台分布
    plat_html = ""
    total_items = sum(platform_dist.values())
    for p, cnt in sorted(platform_dist.items(), key=lambda x: -x[1])[:12]:
        meta = PLATFORMS.get(p, {"label": p, "color": "#94a3b8", "icon": "📌"})
        pct = int(cnt / total_items * 100) if total_items else 0
        plat_html += f"""
      <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border)">
        <span style="font-size:.8em;min-width:80px">{meta['icon']} {meta['label']}</span>
        <div style="flex:1;height:6px;background:var(--surface2);border-radius:3px;overflow:hidden">
          <div style="height:100%;width:{pct}%;background:{meta['color']};border-radius:3px"></div>
        </div>
        <span style="font-size:.75em;color:var(--text3);min-width:40px;text-align:right">{cnt}</span>
      </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>📊 统计面板 · INTEL.SYS</title>
{css_link('css/style.css')}
</head>
<body>
<div class="layout">
{make_sidebar('stats')}
<div class="main">
  <div class="container">
    <div class="topbar">
      <h2>📊 统计<span>面板</span></h2>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="sc-num">{stats['total']:,}</div>
        <div class="sc-lbl">总数据量</div>
      </div>
      <div class="stat-card">
        <div class="sc-num">{len(all_dates)}</div>
        <div class="sc-lbl">覆盖天数</div>
      </div>
      <div class="stat-card">
        <div class="sc-num">{len(platform_dist)}</div>
        <div class="sc-lbl">数据源数</div>
      </div>
    </div>

    <h3 style="font-size:.9em;color:var(--text2);margin:24px 0 14px">平台分布</h3>
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px 20px">
      {plat_html}
    </div>
    <footer>📡 INTEL.SYS · 统计面板</footer>
  </div>
</div>
</div>
{script_tag('js/main.js')}
</body>
</html>"""
    (OUT_DIR / "stats.html").write_text(html, encoding="utf-8")
    print(f"  ✅ stats.html")

# ── 主入口 ─────────────────────────────────
def main():
    today_str = date.today().isoformat()
    prev_day  = (date.today() - timedelta(days=1)).isoformat()
    next_day  = (date.today() + timedelta(days=1)).isoformat()

    print(f"\n📡 INTEL.SYS v2 站点生成器")
    print(f"  日期: {today_str}")

    # 渲染静态资源
    render_css()
    render_js()

    # 读取数据
    all_dates = get_all_dates()
    all_items = get_items()  # 全量数据
    today_items = [it for it in all_items if it.get("date") == today_str]

    # 生成首页
    render_index(today_str, today_items, all_dates)

    # 生成今日日报
    if today_items:
        render_day_page(today_str, today_items, prev_day, next_day)

    # 生成归档页
    render_archive()

    # 生成统计页
    render_stats()

    print(f"\n✅ 生成完成 → output/")
    print(f"   首页: output/index.html")
    print(f"   日报: output/day/{today_str}.html")
    print(f"   归档: output/archive.html")
    print(f"   统计: output/stats.html")
    print(f"   样式: output/css/style.css")
    print(f"   脚本: output/js/main.js")

if __name__ == "__main__":
    main()
