"""生成今日中文日报"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from db.db import get_conn
from datetime import datetime

conn = get_conn()
c = conn.cursor()

today = '2026-05-19'
c.execute("""
    SELECT title, description, url, source_type, original_source, score
    FROM items
    WHERE date_key = ? AND score IS NOT NULL
    ORDER BY score DESC, created_at DESC
    LIMIT 30
""", (today,))
rows = c.fetchall()

report = f"""# 📡 情报日报 · {today}

> 数据来源：Reddit · GitHub · HackerNews · ProductHunt 等
> AI 评分TOP · 人工精选

---

## 🔥 今日热点

"""

hot_items = [r for r in rows if r[5] and r[5] >= 7.0]
for i, r in enumerate(hot_items[:10], 1):
    title, desc, url, st, sub, score = r
    source_icon = {"reddit": "💬", "github": "⚙️", "hackernews": "▲", "producthunt": "🚀"}.get(st, "📌")
    report += f"### {i}. {desc or title}\n"
    report += f"- 来源：{source_icon} {sub} · 评分：{score}分\n"
    report += f"- 🔗 {url}\n\n"

report += """
## 💡 AI & 大模型

"""
ai_items = [r for r in rows if r[3] in ('reddit',) and r[4] and any(k in (r[1] or '').lower() for k in ['llm', 'ai', 'claude', 'chatgpt', 'gpt', 'model', 'gemini', 'qwen', 'local'])]
for r in ai_items[:8]:
    title, desc, url, st, sub, score = r
    report += f"- **{desc or title}** [{sub.split('/')[-1]}] ({score}分)\n"

report += """
## 🛠️ 开发工具

"""
dev_items = [r for r in rows if r[3] == 'github' and r[5] and r[5] >= 6.0]
for r in dev_items[:8]:
    title, desc, url, st, sub, score = r
    report += f"- **{desc or title}** ({score}分)\n"

report += """
## 📊 数据趋势

| 指标 | 数值 |
|------|------|
| 今日总条目 | """ + str(len(rows)) + """ |
| AI相关热点 | """ + str(len(hot_items)) + """条 |
| 高分开发工具 | """ + str(len(dev_items)) + """条 |

---

*由 QClaw 情报系统自动生成 · {today}*
""".format(today=today)

with open(f'output/day/daily_{today}.md', 'w', encoding='utf-8') as f:
    f.write(report)

print(f"日报生成完成：output/day/daily_{today}.md")
print(f"共 {len(rows)} 条条目，{len(hot_items)} 条高分")
conn.close()
