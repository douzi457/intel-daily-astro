#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日报 → 公众号格式转换器
将 output/day/YYYY-MM-DD.html 转换为可直接粘贴到公众号编辑器的HTML
用法：python daily_to_wechat.py [日期，默认今天]
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
import sqlite3
from datetime import date
from pathlib import Path

WORKSPACE = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")
DB_PATH = WORKSPACE / "db" / "intel.db"
OUTPUT_DIR = WORKSPACE / "output" / "wechat"  # 输出目录

def get_today_items(target_date=None):
    """从数据库取今日数据，按平台分组"""
    if target_date is None:
        target_date = str(date.today())
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute("""
        SELECT title, url, description, original_source, hot_value
        FROM items
        WHERE DATE(created_at) = ?
        AND title IS NOT NULL AND title != ''
        ORDER BY original_source, hot_value DESC
    """, (target_date,)).fetchall()
    conn.close()
    return rows

def group_by_source(rows):
    """按平台分组"""
    groups = {}
    for title, url, desc, src, hv in rows:
        groups.setdefault(src, []).append({
            'title': title,
            'url': url or '',
            'desc': desc or '',
            'hot_value': hv or 0,
        })
    return groups

def render_wechat_html(groups, target_date):
    """生成公众号兼容的HTML"""
    date_str = target_date
    total = sum(len(v) for v in groups.values())

    # 公众号兼容CSS（内联样式，微信编辑器支持有限）
    html = f"""<!-- 情报日报 {date_str} → 公众号版 -->
<!-- 直接复制下方内容粘贴到公众号编辑器 -->

<div style="max-width:680px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;color:#333;line-height:1.8;font-size:15px;">

<!-- 标题区 -->
<div style="text-align:center;padding:30px 0 20px;border-bottom:3px solid #4A90D9;margin-bottom:24px;">
  <h2 style="margin:0;font-size:22px;color:#1a1a1a;font-weight:bold;">📡 情报日报 · {date_str}</h2>
  <p style="margin:8px 0 0;color:#888;font-size:13px;">共 {total} 条情报 | 覆盖 {len(groups)} 个平台</p>
</div>
"""

    # 按平台输出
    source_icons = {
        'hackernews': '🔶', 'github': '🐙', 'producthunt': '🚀',
        '36kr': '💰', 'ithome': '📰', 'tencent': '🐧',
        'bilibili': '📺', 'v2ex': '💬', 'wallstreetcn': '📈',
        'toutiao': '📱', 'weibo_hot': '🔥', 'douyin_hot': '🎵',
        'reddit/LocalLLaMA': '🤖', 'reddit/artificial': '🧠',
        'reddit/technology': '💻', 'reddit/programming': '⚡',
        'gzh': '📝', 'sspai': '✍️',
    }

    # 平台排序（中文平台优先）
    cn_sources = ['weibo_hot', 'toutiao', 'douyin_hot', '36kr', 'ithome', 'tencent', 'wallstreetcn', 'bilibili', 'v2ex', 'sspai', 'gzh']
    en_sources = ['hackernews', 'github', 'producthunt', 'reddit/LocalLLaMA', 'reddit/artificial', 'reddit/technology', 'reddit/programming']

    def sort_key(src):
        if src in cn_sources:
            return (0, cn_sources.index(src))
        elif src in en_sources:
            return (1, en_sources.index(src))
        return (2, 0)

    sorted_sources = sorted(groups.keys(), key=sort_key)

    for src in sorted_sources:
        items = groups[src]
        icon = source_icons.get(src, '📌')
        src_label = src.replace('reddit/', 'r/')

        html += f"""
<!-- 平台：{src} -->
<div style="margin-bottom:24px;">
  <div style="display:flex;align-items:center;margin-bottom:12px;padding:8px 12px;background:#f5f7fa;border-radius:6px;">
    <span style="font-size:18px;margin-right:8px;">{icon}</span>
    <span style="font-weight:bold;color:#4A90D9;font-size:15px;">{src_label}</span>
    <span style="margin-left:auto;color:#999;font-size:12px;">{len(items)} 条</span>
  </div>
"""

        for i, item in enumerate(items[:10], 1):  # 每个平台最多10条
            title = item['title']
            url = item['url']
            desc = item['desc']

            # 截断过长标题
            if len(title) > 60:
                title = title[:58] + '…'

            if url and url.startswith('http'):
                title_html = f'<a href="{url}" style="color:#1a73e8;text-decoration:none;">{title}</a>'
            else:
                title_html = f'<span style="color:#333;">{title}</span>'

            html += f"""
  <div style="padding:8px 12px;margin-bottom:6px;border-left:3px solid #e0e0e0;background:#fafbfc;">
    <div style="font-size:14px;line-height:1.6;">{i}. {title_html}</div>
"""
            if desc and len(desc) > 5:
                desc_short = desc[:80] + '…' if len(desc) > 80 else desc
                html += f'    <div style="font-size:12px;color:#888;margin-top:4px;line-height:1.5;">{desc_short}</div>\n'

            html += '  </div>\n'

        if len(items) > 10:
            html += f'  <div style="font-size:12px;color:#aaa;text-align:center;padding:6px;">…还有 {len(items)-10} 条，详见完整版</div>\n'

        html += '</div>\n'

    # 尾部
    html += f"""
<!-- 尾部 -->
<div style="text-align:center;padding:20px;margin-top:30px;border-top:2px solid #eee;color:#aaa;font-size:12px;">
  <p>📡 情报系统自动生成 · {date_str}</p>
  <p>数据来源：GitHub · HackerNews · ProductHunt · 36氪 · IT之家 · 微博 · 抖音等</p>
</div>

</div>
<!-- END -->
"""

    return html

def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else str(date.today())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"正在生成 {target_date} 的公众号版日报…")

    rows = get_today_items(target_date)
    if not rows:
        print(f"❌ 数据库中没有 {target_date} 的数据，请先运行采集")
        return

    groups = group_by_source(rows)
    html = render_wechat_html(groups, target_date)

    out_file = OUTPUT_DIR / f"{target_date}.html"
    out_file.write_text(html, encoding='utf-8')

    print(f"✅ 已生成：{out_file}")
    print(f"   共 {sum(len(v) for v in groups.values())} 条，{len(groups)} 个平台")
    print(f"\n使用方法：")
    print(f"  1. 用浏览器打开 {out_file}")
    print(f"  2. Ctrl+A 全选 → Ctrl+C 复制")
    print(f"  3. 粘贴到公众号编辑器")
    print(f"  4. 微调样式即可发布")

if __name__ == '__main__':
    main()
