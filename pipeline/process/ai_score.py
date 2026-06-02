# ai_score.py — AI 评分 + 摘要（智谱 GLM）
import json
import re
import time
import requests
from ..config import API_KEY, PLATFORM_WEIGHTS
from ..log import log


def call_zhipu(model, prompt, temperature=0.2, max_retries=3):
    """调用智谱 API，带指数退避重试。"""
    if not API_KEY:
        return None
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": temperature}

    for attempt in range(max_retries):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content']
                log(f"  AI API unexpected response: {str(data)[:100]}")
            elif resp.status_code == 429:
                wait = 2 ** attempt
                log(f"  AI API rate limited, retrying in {wait}s...")
                time.sleep(wait)
                continue
            else:
                log(f"  AI API HTTP {resp.status_code}: {resp.text[:100]}")
        except requests.exceptions.Timeout:
            log(f"  AI API timeout (attempt {attempt + 1}/{max_retries})")
        except Exception as e:
            log(f"  AI API Error (attempt {attempt + 1}/{max_retries}): {e}")
        if attempt < max_retries - 1:
            time.sleep(1 * (attempt + 1))

    log(f"  AI API failed after {max_retries} attempts")
    return None


def heuristic_score(title, platform=""):
    """AI 不可用时的启发式打分，含来源权重。"""
    score = 3
    title_lower = title.lower()

    # 来源权重
    weight = PLATFORM_WEIGHTS.get(platform, 0)
    score += weight

    # 内容信号
    if any(k in title_lower for k in ['突破', '发布', '开源', '融资', '上市', '收购', 'launch', 'release', 'funding', 'open source', 'breakthrough']):
        score += 2
    if any(k in title_lower for k in ['ai', 'gpt', 'llm', '大模型', '人工智能', 'deep learning']):
        score += 2
    if any(k in title_lower for k in ['安全', '漏洞', '攻击', '数据泄露', 'cve', 'vulnerability', 'security']):
        score += 1
    if any(k in title_lower for k in ['八卦', '绯闻', '综艺', '直播带货', '出轨']):
        score -= 2

    return max(0, min(score, 10))


def get_dual_language_data(title, content, platform=""):
    """单条 AI 评分 + 中英摘要。"""
    weight = PLATFORM_WEIGHTS.get(platform, 0)
    weight_hint = ""
    if weight > 0:
        weight_hint = f"\nNote: This item comes from a high-quality developer source. The base score should be higher than average."
    elif weight < 0:
        weight_hint = f"\nNote: This item comes from an entertainment/social source. Score it on pure informational merit, ignoring hype/popularity."

    prompt = f"""You are an expert intelligence analyst.

Title: {title}
Content: {content[:300]}{weight_hint}

TASKS:
1. Score from 0-10 based on informational value to tech/business readers.
2. Chinese summary (under 30 words).
3. English summary (under 30 words).

Return EXACTLY this JSON format:
{{"score": <number>, "zh": {{"summary": "中文摘要"}}, "en": {{"summary": "English Summary"}}}}
"""
    res = call_zhipu("glm-4-air", prompt)
    if not res:
        return None
    try:
        match = re.search(r'\{.*\}', res, re.DOTALL)
        result = json.loads(match.group())
        if 'score' in result:
            result['score'] = max(0, min(int(result['score']), 10))
        return result
    except Exception as e:
        log(f"  AI parse error: {e}")
        return None


def process_ai_batch(unprocessed):
    """批量 AI 处理：评分 + 摘要 + 降级。"""
    for item in unprocessed:
        title = item.get('title', '')
        desc = item.get('desc', '')
        platform = item.get('platform', '')
        log(f"  [AI] {title[:40]}...")
        dual = get_dual_language_data(title, desc, platform)

        if isinstance(dual, dict) and dual.get('score', 0) > 0:
            item['score'] = dual.get('score', 5)
            zh = dual.get('zh', {})
            en = dual.get('en', {})
            if isinstance(zh, dict):
                item['ai_summary'] = zh.get('summary', '')
            if isinstance(en, dict):
                item['en_summary'] = en.get('summary', '')
        else:
            item['score'] = heuristic_score(title, platform)
            log(f"  [FB] heuristic score: {item['score']}")

        time.sleep(0.5)
    return unprocessed
