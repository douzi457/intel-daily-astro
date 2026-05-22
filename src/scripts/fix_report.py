import re

with open('collector_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the generate_report function body
old_pattern = r'(    # 生成报告\n    report = \[\]\n    report\.append.*?    # 保存报告)'
new_code = '''    # 生成报告
    report = []
    report.append(f"# 副业情报简报")
    report.append(f"**时间**: {date_str} (北京时间)")
    report.append(f"**数据总量**: {len(items)} 条")
    report.append("")
    
    # 各源统计
    report.append("## 数据源统计")
    for src, src_items in by_source.items():
        report.append(f"- **{src}**: {len(src_items)} 条")
    report.append("")
    
    # 每个分类显示5条
    source_labels = {
        "news_aggregator": "📡 科技情报 (HN/GitHub/PH/36Kr/WSJ/V2Ex)",
        "douyin": "🎵 抖音热榜",
        "gzh": "📝 公众号爆款",
        "weibo": "🐚 微博热搜",
        "xiaohongshu": "📕 小红书",
        "github": "🐙 GitHub Trending",
        "hackernews": "📰 Hacker News",
        "producthunt": "🚀 Product Hunt",
        "36kr": "📰 36Kr",
        "unknown": "❓ 其他"
    }
    
    for src, src_items in by_source.items():
        label = source_labels.get(src, src)
        report.append(f"## {label}")
        for i, item in enumerate(src_items[:5], 1):
            title = item.get("title", "无标题")[:50]
            score = item.get("score", 0)
            url = item.get("url", "")
            report.append(f"**{i}. {title}**")
            if score:
                report.append(f"   - 分数: {score}")
            if url:
                report.append(f"   - {url[:60]}")
        report.append("")
    
    # 保存报告'''

new_content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)

with open('collector_v2.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done')
