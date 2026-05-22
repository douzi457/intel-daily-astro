# dump_astro_json.py
# 从 intel.db 导出 JSON 数据到 rewrite/{lang}/{date}.json 供 Astro 使用
import sqlite3, json, os
from pathlib import Path
from datetime import date, timedelta

# 无论在什么环境下运行，都以脚本所在目录为准
BASE_DIR = Path(__file__).parent
DB = BASE_DIR / "db" / "intel.db"
# 导出到项目根目录下的 src/data/rewrite
OUT_BASE = BASE_DIR.parent.parent / "src" / "data" / "rewrite"

PLATFORM_TAB = {
    "zh": {
        "weibo": "热搜", "douyin": "热搜",
        "wallstreetcn": "财经", "36kr": "财经", "toutiao": "财经", "tencent": "财经",
        "ithome": "开发", "github": "开发", "hackernews": "开发",
        "producthunt": "开发", "v2ex": "开发", "bilibili": "开发",
        "gzh": "公众号", "news_aggregator": "财经", "rss": "财经", "reddit": "开发"
    },
    "en": {
        "weibo": "Trending", "douyin": "Trending",
        "wallstreetcn": "Finance", "36kr": "Finance", "toutiao": "Finance", "tencent": "Finance",
        "ithome": "Dev", "github": "Dev", "hackernews": "Dev",
        "producthunt": "Dev", "v2ex": "Dev", "bilibili": "Dev",
        "gzh": "Society", "news_aggregator": "Finance", "rss": "Finance", "reddit": "Dev"
    }
}

PLATFORM_META = {
    "weibo":        {"label": "微博",     "color": "#FF9500", "icon": "🔥"},
    "douyin":       {"label": "抖音",     "color": "#00F2EA", "icon": "🎵"},
    "wallstreetcn": {"label": "华尔街见闻", "color": "#3395FF", "icon": "📈"},
    "36kr":         {"label": "36Kr",    "color": "#4A90E2", "icon": "📊"},
    "toutiao":      {"label": "今日头条", "color": "#E63946", "icon": "📰"},
    "tencent":      {"label": "腾讯新闻", "color": "#1DB100", "icon": "🌐"},
    "ithome":       {"label": "IT之家",  "color": "#0090D8", "icon": "💻"},
    "github":       {"label": "GitHub",  "color": "#6CCB5F", "icon": "🐙"},
    "hackernews":   {"label": "HN",       "color": "#FF6600", "icon": "⚡"},
    "producthunt":  {"label": "ProductHunt","color": "#DA5430","icon": "🚀"},
    "v2ex":         {"label": "V2EX",     "color": "#4CAF50", "icon": "💬"},
    "gzh":          {"label": "公众号",   "color": "#2ECC71", "icon": "📮"},
}

def hot_stars(hot):
    f = float(hot or 0)
    if f >= 50: return 3
    if f >= 20: return 2
    if f >= 5:  return 1
    return 0

def dump_lang(day_str, lang='zh'):
    if not DB.exists(): return
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM items WHERE date_key=? ORDER BY score DESC LIMIT 200",
        (day_str,)
    )
    rows = cur.fetchall()
    conn.close()

    items = []
    for r in rows:
        p = r["source_type"]
        orig = r["original_source"]
        
        # 语言适配
        title = r["en_title"] if lang == 'en' and r["en_title"] else r["title"]
        desc = r["en_summary"] if lang == 'en' and r["en_summary"] else (r["ai_summary"] or r["description"] or "")
        tab = PLATFORM_TAB[lang].get(p, PLATFORM_TAB[lang].get("news_aggregator", "Finance" if lang == 'en' else "财经"))
        
        meta = PLATFORM_META.get(p, {"label": p, "color": "#94a3b8", "icon": "📌"})
        
        stars = hot_stars(r["hot_value"])
        items.append({
            "id":    r["id"],
            "title": title,
            "desc":  desc,
            "url":   r["url"],
            "platform": p,
            "platform_label": meta["label"],
            "platform_color": meta["color"],
            "platform_icon":  meta["icon"],
            "tab":   tab,
            "hot":   r["hot_value"] or 0,
            "hot_stars": stars,
            "date":  r["date_key"],
            "score": r["score"] or 0,
        })

    out_dir = OUT_BASE / lang
    out_dir.mkdir(exist_ok=True, parents=True)
    out_path = out_dir / f"{day_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"date": day_str, "items": items}, f, ensure_ascii=False, indent=2)
    print(f"  {lang} - {day_str}: {len(items)} items -> {out_path}")

def dump_all():
    if not DB.exists(): return
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT date_key FROM items ORDER BY date_key DESC LIMIT 30")
    dates = [r[0] for r in cur.fetchall()]
    conn.close()
    
    for d in dates:
        dump_lang(d, 'zh')
        dump_lang(d, 'en')

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        dump_lang(sys.argv[1], 'zh')
        dump_lang(sys.argv[1], 'en')
    else:
        dump_all()
