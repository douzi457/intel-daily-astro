# daily_report.py — AI 日报扩写（严格事实约束）
#
# 核心原则：只组织和解读已有信息，绝不编造
import json
import re
from datetime import datetime
from pathlib import Path
from ..config import OUT_BASE
from ..log import log
from ..process.ai_score import call_zhipu


# 日报输出目录
DAILY_MD_DIR = OUT_BASE / "daily"
DAILY_MD_DIR.mkdir(parents=True, exist_ok=True)


def _build_items_text(items, max_items=15):
    """将高评分条目格式化为文本供 AI 使用。"""
    scored = [it for it in items if it.get('score', 0) >= 5]
    scored.sort(key=lambda x: x.get('score', 0), reverse=True)
    top = scored[:max_items]

    if len(top) < 3:
        log(f"  [DailyReport] insufficient high-score items ({len(top)}), skip")
        return None

    lines = []
    for i, it in enumerate(top, 1):
        title = it.get('title', '')
        platform = it.get('platform', '')
        platform_label = it.get('platform_label', platform)
        score = it.get('score', 0)
        desc = it.get('desc', '') or it.get('ai_summary', '') or '无摘要'
        url = it.get('url', '')
        category = it.get('category', '其他')

        lines.append(
            f"{i}. [{platform_label}] {title}\n"
            f"   评分: {score}/10 | 分类: {category}\n"
            f"   摘要: {desc[:100]}\n"
            f"   链接: {url}"
        )

    return "\n".join(lines)


def _build_stats_text(items):
    """生成统计信息文本。"""
    total = len(items)
    high_score = sum(1 for it in items if it.get('score', 0) >= 7)
    platforms = len(set(it.get('platform', '') for it in items))
    return f"- 今日采集：{total} 条\n- 高价值信号：{high_score} 条（评分≥7）\n- 覆盖平台：{platforms} 个"


def _build_links_text(items, max_links=8):
    """生成值得关注链接。"""
    scored = [it for it in items if it.get('score', 0) >= 5 and it.get('url')]
    scored.sort(key=lambda x: x.get('score', 0), reverse=True)

    links = []
    for it in scored[:max_links]:
        title = it.get('title', '')
        url = it.get('url', '')
        platform = it.get('platform_label', it.get('platform', ''))
        score = it.get('score', 0)
        links.append(f"- [{title}]({url}) — {platform} · 信号 {score}")

    return "\n".join(links) if links else "- 暂无"


DAILY_REPORT_PROMPT = """你是豆子实验室的编辑。根据今日自动采集的真实情报数据，撰写一份简洁的日报。

⚠️ 严格规则（必须遵守）：
1. 只使用下方提供的真实标题和摘要内容
2. 不编造任何原文未提及的信息：包括数字、人名、时间、地点
3. 不猜测因果关系，不推测未来走向
4. 如果某条信息不足以展开，宁可不写也不要编造细节
5. 观点只从已有事实推导，推导不出来就不写
6. 用"据报道""消息指出"等措辞表示非确定性信息
7. 如果某条摘要为"无摘要"，只转述标题，不要补充内容

今日情报数据（按评分排序）：
{items_text}

统计信息：
{stats_text}

请输出 Markdown 格式日报，结构严格如下：

---
title: "豆子实验室日报 | {date}"
date: "{date}"
totalItems: {total}
highScoreCount: {high_score}
platforms: {platforms}
trends: [{trends_placeholder}]
---

# 豆子实验室日报 | {date}

> 一句话总结今日趋势（必须基于上述数据推导）

## 📡 今日信号

（选评分≥6的条目，每条2-3句解读。解读 = 复述已有信息 + 补充行业常识性背景，不编造细节）

### 1. 原标题写在这里
- 来源：平台名 | 评分：X/10
- 解读：（基于已有标题和摘要的事实性解读，2-3句，不编造）

### 2. ...

## 📊 数据看板

{stats_text}

趋势关键词：（从已有标题中提取3-5个出现频率最高的关键词，不编造）

## 🔗 值得关注

{links_text}

---
*本日报由 AI 基于自动采集的真实资讯生成，仅做信息整合与解读，不编造任何内容。*
"""


def generate_daily_report(items, date_key):
    """生成 AI 日报 Markdown 文件。"""
    items_text = _build_items_text(items)
    if not items_text:
        log("  [DailyReport] skipped (insufficient data)")
        return

    total = len(items)
    high_score = sum(1 for it in items if it.get('score', 0) >= 7)
    platforms = len(set(it.get('platform', '') for it in items))
    stats_text = _build_stats_text(items)
    links_text = _build_links_text(items)

    # 从标题中提取高频关键词（简单实现，不依赖AI）
    from collections import Counter
    keyword_candidates = []
    for it in items:
        if it.get('score', 0) >= 5:
            title = it.get('title', '')
            # 简单提取2-4字中文词和英文词
            words = re.findall(r'[\u4e00-\u9fff]{2,4}|[A-Za-z]{2,}', title)
            keyword_candidates.extend(words)
    # 过滤停用词
    stopwords = {'今日', '今年', '最新', '发布', '宣布', '报道', '显示', '目前', '已经', '这些', '这个', '那个', '之后', '之前', '通过', '进行', 'the', 'for', 'and', 'with', 'from', 'this', 'that', 'has', 'are', 'was', 'will', 'can', 'not', 'but', 'new'}
    filtered = [w for w in keyword_candidates if w.lower() not in stopwords]
    top_keywords = [kw for kw, _ in Counter(filtered).most_common(5)]
    trends_str = ", ".join(f'"{kw}"' for kw in top_keywords) if top_keywords else '"科技"'

    prompt = DAILY_REPORT_PROMPT.format(
        items_text=items_text,
        stats_text=stats_text,
        links_text=links_text,
        date=date_key,
        total=total,
        high_score=high_score,
        platforms=platforms,
        trends_placeholder=trends_str,
    )

    result = call_zhipu("glm-4-air", prompt, temperature=0.3)
    if not result:
        log("  [DailyReport] AI generation failed, skip")
        return

    # 清理 AI 可能返回的 markdown 代码块包裹
    content = result.strip()
    if content.startswith("```"):
        content = re.sub(r'^```\w*\n?', '', content)
        content = re.sub(r'\n?```$', '', content)
    content = content.strip()

    # 确保有 frontmatter
    if not content.startswith("---"):
        # AI 可能没输出 frontmatter，手动加
        frontmatter = f"""---
title: "豆子实验室日报 | {date_key}"
date: "{date_key}"
totalItems: {total}
highScoreCount: {high_score}
platforms: {platforms}
trends: [{trends_str}]
---

"""
        content = frontmatter + content

    out_path = DAILY_MD_DIR / f"{date_key}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    log(f"  [DailyReport] written to {out_path} ({len(content)} chars)")
