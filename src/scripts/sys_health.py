import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3, json
from pathlib import Path
from datetime import date, datetime, timedelta

WORKSPACE = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")
conn = sqlite3.connect(str(WORKSPACE / "db" / "intel.db"))
c = conn.cursor()

print("=" * 55)
print("  情报系统 v2.0 全面体检报告")
print("=" * 55)

# 1. 数据总量 & 趋势
print("\n【1. 数据总量】")
total = c.execute("SELECT COUNT(*) FROM items").fetchone()[0]
today = '2026-05-20'
yesterday = '2026-05-19'
twoday = '2026-05-18'

t_today = c.execute("SELECT COUNT(*) FROM items WHERE DATE(created_at)=?", (today,)).fetchone()[0]
t_ydy   = c.execute("SELECT COUNT(*) FROM items WHERE DATE(created_at)=?", (yesterday,)).fetchone()[0]
t_2dy   = c.execute("SELECT COUNT(*) FROM items WHERE DATE(created_at)=?", (twoday,)).fetchone()[0]

print(f"  总数据量: {total} 条")
print(f"  今日(05-20): {t_today} 条")
print(f"  昨日(05-19): {t_ydy} 条")
print(f"  前日(05-18): {t_2dy} 条")

# 2. 各平台数据量排名
print("\n【2. 各平台数据量（按总条数）】")
rows = c.execute("""
    SELECT original_source, COUNT(*) as cnt
    FROM items
    GROUP BY original_source
    ORDER BY cnt DESC
    LIMIT 15
""").fetchall()
total_in_list = sum(r[1] for r in rows)
print(f"  统计了 {len(rows)} 个平台，合计 {total_in_list} 条")
for name, cnt in rows:
    bar = '█' * min(cnt // 10, 30)
    print(f"  {name:<25} {cnt:>5}条  {bar}")

# 3. URL覆盖率
print("\n【3. URL覆盖率】")
total_items = c.execute("SELECT COUNT(*) FROM items").fetchone()[0]
no_url = c.execute("SELECT COUNT(*) FROM items WHERE url IS NULL OR url = ''").fetchone()[0]
has_url = total_items - no_url
cov = has_url / total_items * 100
print(f"  有链接: {has_url} 条 ({cov:.1f}%)")
print(f"  无链接: {no_url} 条 ({100-cov:.1f}%)")

# 无链接最多的平台
print("  无链接平台TOP5:")
no_url_src = c.execute("""
    SELECT original_source, COUNT(*) as cnt
    FROM items
    WHERE url IS NULL OR url = ''
    GROUP BY original_source
    ORDER BY cnt DESC
    LIMIT 5
""").fetchall()
for name, cnt in no_url_src:
    print(f"    {name:<25} {cnt}条")

# 4. 采集频率（每小时新增趋势）
print("\n【4. 各数据源最后采集时间】")
import os, re
collectors = {
    'collector.py（综合）': WORKSPACE / "collector.py",
    'fetch_news.py（新闻）': WORKSPACE / "collect" / "fetch_news.py",
    'collector_reddit.py': WORKSPACE / "collect" / "collector_reddit.py",
    'fetch_gzh_trends.py': WORKSPACE / "collect" / "fetch_gzh_trends.py",
    'douyin_json.js': WORKSPACE / "collect" / "douyin_json.js",
}
for name, path in collectors.items():
    if path.exists():
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        age = (datetime.now() - mtime).total_seconds() / 3600
        print(f"  {name:<30} {mtime.strftime('%m-%d %H:%M')} ({age:.1f}h前)")
    else:
        print(f"  {name:<30} ❌ 文件不存在")

# 5. 重复数据检测
print("\n【5. 重复数据检测】")
dup = c.execute("""
    SELECT title, COUNT(*) as cnt
    FROM items
    WHERE title != ''
    GROUP BY TRIM(title)
    HAVING cnt > 1
    ORDER BY cnt DESC
    LIMIT 5
""").fetchall()
if dup:
    print(f"  发现 {len(dup)} 组重复标题（TOP5）:")
    for title, cnt in dup:
        short = title[:40] if title else ''
        print(f"    {short}  x{cnt}")
else:
    print("  ✅ 无重复标题")

# 6. 空标题/空描述检测
print("\n【6. 数据质量】")
no_title = c.execute("SELECT COUNT(*) FROM items WHERE title IS NULL OR title = ''").fetchone()[0]
no_desc = c.execute("SELECT COUNT(*) FROM items WHERE description IS NULL OR description = ''").fetchone()[0]
print(f"  空标题: {no_title} 条")
print(f"  空描述: {no_desc} 条")
print(f"  有标题率: {(total-no_title)/total*100:.1f}%")
print(f"  有描述率: {(total-no_desc)/total*100:.1f}%")

# 7. cron任务状态
print("\n【7. Cron定时任务】")
jobs_file = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统\jobs.json")
if jobs_file.exists():
    jobs = json.loads(jobs_file.read_text(encoding='utf-8'))
    for job in jobs:
        print(f"  {job.get('name','?'):<30} {job.get('schedule','?'):<20} {job.get('state','?')}")
else:
    print("  jobs.json 不存在")

# 8. 输出文件
print("\n【8. 日报文件】")
out_dir = WORKSPACE / "output" / "day"
if out_dir.exists():
    files = sorted(out_dir.glob("*.html"))
    print(f"  共 {len(files)} 份日报")
    if files:
        latest = files[-1]
        print(f"  最新: {latest.name} ({latest.stat().st_size//1024}KB)")
else:
    print("  output/day 目录不存在")

# 9. 翻译覆盖率
print("\n【9. 翻译覆盖（zh_title/zh_desc）】")
has_zh_title = c.execute("SELECT COUNT(*) FROM items WHERE zh_title IS NOT NULL AND zh_title != ''").fetchone()[0]
has_zh_desc = c.execute("SELECT COUNT(*) FROM items WHERE zh_desc IS NOT NULL AND zh_desc != ''").fetchone()[0]
foreign = c.execute("""
    SELECT COUNT(*) FROM items
    WHERE original_source IN ('hackernews','github','producthunt')
    AND (title IS NOT NULL AND title != '')
""").fetchone()[0]
print(f"  有zh_title: {has_zh_title} 条")
print(f"  有zh_desc: {has_zh_desc} 条")
print(f"  HN/GH/PH总条数: {foreign} 条")
print(f"  翻译覆盖率: {has_zh_desc}/{foreign} = {has_zh_desc/max(foreign,1)*100:.1f}%")

# 10. AI评分状态
print("\n【10. AI评分（MiniMax）】")
has_score = c.execute("SELECT COUNT(*) FROM items WHERE score > 0").fetchone()[0]
print(f"  有评分: {has_score} 条 / {total} 条")
print(f"  评分率: {has_score/max(total,1)*100:.1f}%")
print(f"  MiniMax API Key: {'✅ 已配置' if os.environ.get('MINIMAX_API_KEY') else '❌ 未配置'}")

conn.close()
