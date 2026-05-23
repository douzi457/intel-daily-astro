# dump_astro_json.py
# 从 intel.db 导出 JSON 数据到 rewrite/{lang}/{date}.json
import sqlite3, json, os
from pathlib import Path
from datetime import date, timedelta

# 获取脚本所在目录
BASE_DIR = Path(__file__).parent
DB = BASE_DIR / "db" / "intel.db"
# 确保指向项目根目录下的数据目录
OUT_BASE = BASE_DIR.parent.parent / "src" / "data" / "rewrite"

PLATFORM_TAB = {
    "zh": {
        "weibo": "热搜", "douyin": "热搜", "wallstreetcn": "财经", "36kr": "财经", 
        "toutiao": "财经", "tencent": "财经", "ithome": "开发", "github": "开发", 
        "hackernews": "开发", "producthunt": "开发", "v2ex": "开发", "gzh": "公众号",
        "news_aggregator": "财经", "rss": "财经", "reddit": "开发"
    },
    "en": {
        "weibo": "Trending", "douyin": "Trending", "wallstreetcn": "Finance", "36kr": "Finance",
        "toutiao": "Finance", "tencent": "Finance", "ithome": "Dev", "github": "Dev",
        "hackernews": "Dev", "producthunt": "Dev", "v2ex": "Dev", "gzh": "Society",
        "news_aggregator": "Finance", "rss": "Finance", "reddit": "Dev"
    }
}

def hot_stars(hot):
    try: f = float(hot or 0)
    except: f = 0
    if f >= 50: return 3
    if f >= 20: return 2
    if f >= 5:  return 1
    return 0

def dump_lang(day_str, lang='zh'):
    if not DB.exists(): return
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE date_key=? ORDER BY score DESC LIMIT 200", (day_str,))
    rows = cur.fetchall()
    conn.close()

    items = []
    for r in rows:
        title = r["en_title"] if lang == 'en' and r["en_title"] else r["title"]
        desc = r["en_summary"] if lang == 'en' and r["en_summary"] else (r["ai_summary"] or r["description"] or "")
        tab = PLATFORM_TAB[lang].get(r["source_type"], "Finance" if lang == 'en' else "财经")
        
        items.append({
            "id": r["id"], "title": title, "desc": desc, "url": r["url"],
            "platform": r["source_type"], "tab": tab,
            "hot": r["hot_value"] or 0, "hot_stars": hot_stars(r["hot_value"]),
            "date": r["date_key"], "score": r["score"] or 0,
            "platform_color": "#4A90E2", # 默认颜色，可后续扩展
            "platform_label": r["source_type"],
            "platform_icon": "📌"
        })

    # 关键点：创建子目录
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
