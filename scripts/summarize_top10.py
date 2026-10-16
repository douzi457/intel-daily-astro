#!/usr/bin/env python3
"""
summarize_top10.py — 每分类 Top10 生成 LLM 摘要（2026-10-15）

逻辑（对标 AIHOT）：
- 8 个分类各取评分 Top10，共 80 条
- 每条调 Agnes 生成：中文标题 + 2-3句摘要（答案前置）+ 内容类型7选1
- 写回 src/data/rewrite/zh/YYYY-MM-DD.json（加 ai_summary、content_type 字段）
- Token：80条 × ~1050 ≈ 84K/天，可忽略

用法：python scripts/summarize_top10.py --date 2026-10-15
"""
import json, os, sys, time
from pathlib import Path
from datetime import datetime

# 7 种内容类型（对标 AIHOT）
CONTENT_TYPES = {
    'model_release': '模型发布',
    'product_launch': '产品更新',
    'tool_or_prompt': '工具技巧',
    'research_paper': '论文研究',
    'industry_event': '行业动态',
    'opinion_analysis': '观点分析',
    'tutorial_explainer': '教程评测',
}

SUMMARY_PROMPT = """你是中文科技资讯编辑。给下面这条资讯写中文标题和摘要。

要求：
1. 中文标题：20字内，交代谁做了什么。如原标题是英文，直接翻译改写，不要照搬。
2. 摘要2-3句：第一句必须回答"谁做了什么、关键结果是什么"（30-70字），不要"本文介绍了"这类套话；后面补1-2个关键事实/数字。
3. 内容类型7选1：model_release(新模型)、product_launch(新产品/功能)、tool_or_prompt(方法技巧)、research_paper(论文)、industry_event(融资/监管/商业)、opinion_analysis(观点访谈)、tutorial_explainer(教程评测)
4. 推荐理由1句：说明"读者可据此判断/评估什么"，20-40字，不要套话
5. 注意力评分：按五轴打分后加权（0-10，保留1位小数）
   - sig实质份量(0-10)：时间线节点/周变化/当天脚注
   - nov信息增量(0-10)：新能力/新结果/新事实/新方法
   - cred证据强度(0-10)：材料对核心事实的支持度
   - reson共振面(0-10)：多少读者觉得与自己有关
   - act可用性(0-10)：能否马上用/学/迁移
   - 按内容类型加权：model_release[3,2,2,2,1] product_launch[2,2,1,2,3] tool_or_prompt[1,2,1,2,4] research_paper[5,3,1,0,1] industry_event[3,1,2,4,0] opinion_analysis[1,3,1,4,1] tutorial_explainer[1,1,1,3,4]，加权和除以10
   - 压分硬规则（防分数膨胀，必须执行）：
     * 营销软文、课程推广、活动宣传、招聘：sig ≤ 2
     * 例行小版本、常规功能更新、语言/地区补齐：sig ≤ 3
     * 客户案例、PR稿无明确数据（任务/规模/成本/时间）：sig ≤ 4
     * 只有预告、抢先体验、无实质参数：nov ≤ 3 且 cred ≤ 4
     * 禁止把多个普通理由堆成高分；禁止四舍五入到整十
   - 盲评：只根据标题和正文内容打分，不要因来源是大厂/知名媒体而加分

只输出JSON：{{"title": "中文标题", "summary": "2-3句摘要", "content_type": "7选1的英文key", "reason": "推荐理由", "score": 7.5}}
不要输出其他内容。

标题：{title}
来源：{source}
正文/描述：{desc}
"""

def call_agnes(title, source, desc, last_call_time):
    """调 Agnes 生成摘要（严格限速 + 429 重试）"""
    import urllib.request
    api_key = os.environ.get('AGNES_API_KEY', '')
    base_url = os.environ.get('AGNES_BASE_URL', 'https://api.agnes-ai.cn/v1')
    model = "agnes-3.0-flash"  # 老大指定写死（2026-10-15）
    if not api_key:
        return None, last_call_time
    # 严格限速：免费档 20 RPM → 每次调用至少间隔 3.2 秒
    elapsed = time.time() - last_call_time
    if elapsed < 3.2:
        time.sleep(3.2 - elapsed)
    prompt = SUMMARY_PROMPT.format(
        title=title[:200], source=source[:50], desc=(desc or title)[:800])
    last_call_time = time.time()
    for attempt_model in [model, "agnes-2.5-flash"]:
        for retry in range(3):  # 429 重试 3 次
            try:
                data = json.dumps({
                    "model": attempt_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 400,
                }).encode()
                req = urllib.request.Request(
                    f"{base_url}/chat/completions", data=data,
                    headers={"Authorization": f"Bearer {api_key}",
                             "Content-Type": "application/json"})
                resp = urllib.request.urlopen(req, timeout=30)
                result = json.load(resp)
                text = result["choices"][0]["message"]["content"].strip()
                if "```" in text:
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                return json.loads(text.strip()), last_call_time
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait = (retry + 1) * 10  # 10s, 20s, 30s
                    print(f"  429 限流，等待 {wait}s 后重试 ({retry+1}/3)", flush=True)
                    time.sleep(wait)
                    continue
                else:
                    print(f"  {attempt_model} HTTP {e.code}: {str(e)[:50]}", flush=True)
                    break
            except Exception as e:
                print(f"  {attempt_model} 失败: {str(e)[:60]}", flush=True)
                break
    return None, last_call_time

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'))
    ap.add_argument('--limit', type=int, default=10, help='每分类取几条')
    args = ap.parse_args()

    data_path = Path(f"src/data/rewrite/zh/{args.date}.json")
    if not data_path.exists():
        print(f"数据文件不存在: {data_path}")
        sys.exit(1)
    data = json.load(open(data_path, encoding='utf-8'))
    items = data.get('items', [])
    print(f"共 {len(items)} 条", flush=True)

    # 按分类分组取 TopN
    from collections import defaultdict
    by_cat = defaultdict(list)
    for it in items:
        by_cat[it.get('category', '其他')].append(it)
    targets = []
    for cat, lst in by_cat.items():
        top = sorted(lst, key=lambda x: x.get('score', 0), reverse=True)[:args.limit]
        # 跳过已有摘要的
        top = [t for t in top if not t.get('ai_summary')]
        targets.extend(top)
        print(f"[{cat}]: {len(top)} 条待摘要", flush=True)
    print(f"共 {len(targets)} 条需调用 LLM", flush=True)

    ok = 0
    failed = []
    last_call = 0.0
    for i, it in enumerate(targets):
        print(f"[{i+1}/{len(targets)}] {it.get('title','')[:40]}", flush=True)
        try:
            r, last_call = call_agnes(it.get('title',''), it.get('platform_label') or it.get('source',''), it.get('desc',''), last_call)
        except Exception as e:
            print(f"  异常跳过: {str(e)[:60]}", flush=True)
            failed.append(it.get('title','')[:50])
            continue
        if r and r.get('summary'):
            it['ai_summary'] = r['summary']
            it['ai_title'] = r.get('title', '')
            it['ai_reason'] = r.get('reason', '')
            try:
                it['ai_score'] = round(float(r.get('score', 0)), 1)
            except:
                pass
            ct = r.get('content_type', '')
            it['content_type'] = ct
            it['content_type_label'] = CONTENT_TYPES.get(ct, ct)
            ok += 1
        else:
            failed.append(it.get('title','')[:50])

    json.dump(data, open(data_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"完成: {ok}/{len(targets)} 成功，已写回 {data_path}")
    if failed:
        print(f"失败 {len(failed)} 条（下次补跑）:")
        for t in failed[:10]:
            print(f"  - {t}")

if __name__ == '__main__':
    main()
