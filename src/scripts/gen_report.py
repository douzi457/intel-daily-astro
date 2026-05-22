"""生成今日中文日报"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn

conn = get_conn()
c = conn.cursor()

today = '2026-05-19'
c.execute("""
    SELECT title, description, url, source_type, original_source, score
    FROM items
    WHERE date_key = ? AND score IS NOT NULL
    ORDER BY score DESC, created_at DESC
    LIMIT 40
""", (today,))
rows = c.fetchall()
c.close()

# 如果今天没数据，用最新的
if not rows:
    c = conn.cursor()
    c.execute("SELECT MAX(date_key) FROM items")
    today = c.fetchone()[0]
    c.execute("""
        SELECT title, description, url, source_type, original_source, score
        FROM items
        WHERE date_key = ? AND score IS NOT NULL
        ORDER BY score DESC, created_at DESC
        LIMIT 40
    """, (today,))
    rows = c.fetchall()
    c.close()

conn.close()

report = f"""# 📡 情报日报 · {today}

> 数据来源：Reddit · GitHub · HackerNews · ProductHunt
> AI 评分TOP · 人工精选

---

## 今日热点 TOP10

"""

hot = [r for r in rows if r[5] and r[5] >= 7.0]
icons = {'reddit': '💬', 'github': '⚙️', 'hackernews': '▲', 'producthunt': '🚀'}
for i, r in enumerate(hot[:10], 1):
    title, desc, url, st, sub, score = r
    icon = icons.get(st, '📌')
    display = desc if desc else title
    report += f"**{i}. {display}**\n"
    report += f"来源：{icon} {sub} · AI评分：{score}分\n\n"

report += """
## 大模型 & AI

"""
ai_keywords = ['llm', 'ai', 'claude', 'chatgpt', 'gpt', 'model', 'gemini', 'qwen', 'local', 'agent', 'anthropic']
ai_items = [r for r in rows if r[5] and r[5] >= 6.0 and any(k in (r[1] or '').lower() for k in ai_keywords)]
for r in ai_items[:8]:
    title, desc, url, st, sub, score = r
    display = desc if desc else title
    report += f"- {display} [{sub.split('/')[-1]}] ({score}分)\n"

report += """
## 开发工具 & 开源

"""
dev_items = [r for r in rows if r[3] == 'github' and r[5] and r[5] >= 6.0]
for r in dev_items[:8]:
    title, desc, url, st, sub, score = r
    display = desc if desc else title
    report += f"- {display} ({score}分)\n"

report += """
## 行业 & 商业

"""
biz_items = [r for r in rows if r[5] and r[5] >= 6.5 and r[3] in ('reddit',) and not any(k in (r[1] or '').lower() for k in ai_keywords)]
for r in biz_items[:5]:
    title, desc, url, st, sub, score = r
    display = desc if desc else title
    report += f"- {display} [{sub.split('/')[-1]}] ({score}分)\n"

report += f"""
---

**数据概览**
- 今日总条目：{len(rows)}
- 今日热点（7分以上）：{len(hot)}条
- 覆盖来源：Reddit · GitHub · HackerNews · ProductHunt

*QClaw 情报系统 · {today}*
"""

print(report)
print(f"\n[DBG] today={today}, rows={len(rows)}, hot={len(hot)}")
