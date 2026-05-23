# dump_astro_json.py
# 2026 Pro Intelligence Engine - Data Exporter
import sqlite3, json, os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB = BASE_DIR / "db" / "intel.db"
OUT_BASE = BASE_DIR.parent.parent / "src" / "data" / "rewrite"

# 映射配置：让每个源都有自己的“名片”
PLATFORM_META = {
    "36kr":         {"label": "36Kr",    "color": "#4A90E2", "icon": "📊"},
    "wallstreetcn": {"label": "华尔街见闻", "color": "#3395FF", "icon": "📈"},
    "ithome":       {"label": "IT之家",  "color": "#0090D8", "icon": "💻"},
    "github":       {"label": "GitHub",  "color": "#6CCB5F", "icon": "🐙"},
    "hackernews":   {"label": "HN",      "color": "#FF6600", "icon": "⚡"},
    "toutiao":      {"label": "今日头条", "color": "#E63946", "icon": "📰"},
    "weibo":        {"label": "微博热搜", "color": "#FF9500", "icon": "🔥"},
    "douyin":       {"label": "抖音热搜", "color": "#00F2EA", "icon": "🎵"},
    "v2ex":         {"label": "V2EX",    "color": "#4CAF50", "icon": "💬"},
    "producthunt":  {"label": "ProductHunt", "color": "#DA5430", "icon": "🚀"},
}

def dump_lang(day_str, lang='zh'):
    if not DB.exists(): return
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE date_key=? ORDER BY score DESC LIMIT 500", (day_str,))
    rows = cur.fetchall()
    conn.close()

    items = []
    for r in rows:
        # 1. 来源识别优化：优先使用 original_source 来定义卡片归属
        source_key = r["original_source"] if r["original_source"] in PLATFORM_META else r["source_type"]
        meta = PLATFORM_META.get(source_key, {"label": source_key, "color": "#94a3b8", "icon": "📌"})
        
        # 2. AI 摘要优先：如果 AI 生成了摘要，就直接作为主描述显示
        raw_desc = r["ai_summary"] or r["description"] or ""
        # 去除摘要中可能存在的“摘要：”字样
        clean_desc = raw_desc.replace("摘要：", "").replace("Summary:", "").strip()
        
        # 3. 语言适配
        title = r["en_title"] if lang == 'en' and r["en_title"] else r["title"]
        desc = r["en_summary"] if lang == 'en' and r["en_summary"] else clean_desc
        
        items.append({
            "id": r["id"],
            "title": title,
            "desc": desc,
            "url": r["url"],
            "platform": source_key, # 这里改用 source_key 保证了前端的分组正确
            "platform_label": meta["label"],
            "platform_color": meta["color"],
            "platform_icon": meta["icon"],
            "hot": r["hot_value"] or 0,
            "date": r["date_key"],
            "score": r["score"] or 0
        })

    out_dir = OUT_BASE / lang
    out_dir.mkdir(exist_ok=True, parents=True)
    with open(out_dir / f"{day_str}.json", "w", encoding="utf-8") as f:
        json.dump({"date": day_str, "items": items}, f, ensure_ascii=False, indent=2)
    print(f"  {lang} - {day_str}: {len(items)} items exported.")

def dump_all():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT date_key FROM items ORDER BY date_key DESC LIMIT 30")
    dates = [r[0] for r in cur.fetchall()]
    conn.close()
    for d in dates:
        dump_lang(d, 'zh')
        dump_lang(d, 'en')

if __name__ == "__main__":
    dump_all()
