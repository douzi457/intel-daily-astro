# focus.py — AI 今日重点生成
import json
import re
from datetime import datetime
from ..config import OUT_BASE
from ..log import log
from ..process.ai_score import call_zhipu


def generate_focus(items, date_key):
    """用 AI 生成今日重点推荐。"""
    scored = [it for it in items if it.get('score', 0) >= 5]
    scored.sort(key=lambda x: x['score'], reverse=True)
    top_items = scored[:8]  # 更多候选让 AI 选

    if len(top_items) < 3:
        log(f"  [Focus] insufficient data ({len(top_items)} items), skip")
        fallback = {"date": date_key, "generated_at": datetime.now().isoformat(), "highlights": [], "trends": []}
        with open(OUT_BASE / "today-focus.json", "w", encoding="utf-8") as f:
            json.dump(fallback, f, ensure_ascii=False, indent=2)
        return

    items_text = "\n".join([
        f"{i+1}. [{it.get('platform','?')}] {it.get('title','')} (评分:{it.get('score',0)}) | {it.get('desc','') or it.get('ai_summary','') or '无摘要'}"
        for i, it in enumerate(top_items)
    ])

    prompt = f"""你是豆子实验室的首席编辑。今天是{date_key}，请从今日情报中提炼最有价值的发现。

今日情报列表:
{items_text}

请以 JSON 格式返回（不要包含其他内容）:
{{
  "summary": "今日整体趋势一句话总结（20字以内，要有态度，像编辑部头条）",
  "trendAnalysis": "📊 编辑手记：分析今日资讯的核心主线、值得关注的变化信号。要有洞察力，像真人编辑在写日报引言。60-100字。",
  "dailyPick": "🔖 今日必读：从所有条目中，选出一条编辑认为最值得读的，写一句有力的推荐理由。15字以内。",
  "highlights": [
    {{
      "rank": 1,
      "title": "原标题",
      "reason": "为什么这条信息值得关注（20字以内）",
      "insight": "背后的趋势或含义（40字以内）",
      "summary": "60字以内的中文要点摘要",
      "source": "来源",
      "url": "原文链接"
    }}
  ],
  "trends": ["趋势关键词1", "趋势关键词2", "趋势关键词3"]
}}

要求:
- 选最重要的 5 条，不只是评分最高，而是最有新闻价值/趋势信号/实操意义的
- reason 写这条信息对读者的实际价值
- insight 要有编辑级别的洞察力
- trends 写 3 个今日最值得关注的主题方向
- dailyPick 必须是一条具体条目，给出有力的推荐理由
"""

    result = call_zhipu("glm-4-air", prompt, temperature=0.4)
    if result:
        try:
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                data = json.loads(match.group())
                data['date'] = date_key
                data['generated_at'] = datetime.now().isoformat()
                with open(OUT_BASE / "today-focus.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                log(f"  [Focus] {len(data.get('highlights', []))} highlights generated")
                return
        except Exception as e:
            log(f"  [Focus] parse error: {e}")

    log("  [Focus] AI failed, writing empty")
    fallback = {"date": date_key, "generated_at": datetime.now().isoformat(), "highlights": [], "trends": []}
    with open(OUT_BASE / "today-focus.json", "w", encoding="utf-8") as f:
        json.dump(fallback, f, ensure_ascii=False, indent=2)
