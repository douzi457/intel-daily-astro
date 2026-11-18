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
   - 刻度校准（2026-11-15）：你正在给当天各分类 Top10 打分，这些已经是当天
     最重要的 80 条，分数量纲是 0-10，应当用满刻度——真正的大事
     （改变行业格局、时间线节点、头部公司战略转向）给 9.0-9.8；
     重要的新能力/新产品/新研究给 7.5-8.9；一般的资讯给 6.5-7.4；
     只有明显水的内容才低于 6.5。不要把所有分都压在 7 分以下
     （此前实测最高分只有 7.5，刻度没用满）。9.5+ 只给当天最重磅的
     1-2 条。压分硬规则仍然有效（营销/例行更新/无数据 PR 按上面的
     上限压），不要为了拉开分布给水文高分。
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
    model = os.environ.get('AGNES_MODEL') or "agnes-3.0-flash"
    if not api_key:
        return None, last_call_time
    # 严格限速：免费档实测易 429 → 每次调用至少间隔 6 秒
    elapsed = time.time() - last_call_time
    if elapsed < 6.0:
        time.sleep(6.0 - elapsed)
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
                    wait = (retry + 1) * 20  # 20s, 40s, 60s
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

def validate_ai_title(original_title, ai_title):
    """校验 LLM 生成的中文标题是否被“截断/错字”污染。
    抓的模式：原标题里的拉丁词被截成片段、且片段紧贴中文
    （例：DeepSeek -> “深Seek”，2026-11-07 真实案例）。
    通过返回 True；不通过时调用方应丢弃 ai_title、回落到原标题。
    2026-11-15 实测：557 条真实 ai_title 里 0 条误拒，目标条被抓到。
    """
    import re
    if not ai_title or not ai_title.strip():
        return False
    # 原标题有中文，改写后不能全丢中文
    if re.search(r'[\u4e00-\u9fff]', original_title or '') and not re.search(r'[\u4e00-\u9fff]', ai_title):
        return False

    def _norm(t):
        return re.sub(r'[-_.]', '', t).lower()

    src_toks = re.findall(r'[A-Za-z][A-Za-z0-9\-\.]{2,}', original_title or '')
    src_norm = {_norm(t) for t in src_toks}
    for at in re.findall(r'[A-Za-z][A-Za-z0-9\-\.]{2,}', ai_title):
        an = _norm(at)
        if len(an) < 3 or an in src_norm:
            continue  # 原样保留的词
        for st in src_toks:
            sn = _norm(st)
            if len(sn) > len(an) and sn.endswith(an):
                m = re.search(re.escape(at), ai_title)
                if m and (m.start() == 0 or re.match(r'[\u4e00-\u9fff]', ai_title[m.start() - 1])):
                    return False
    return True


EXEC_SUMMARY_PROMPT = """你是中文科技资讯编辑。今天最重要的科技新闻如下（按重要性排序，分数 0-10）：

{items}

用一句话写出今天最重要的一条洞察。要求：
1. 必须具体指向一家公司、一项技术或一个数字（三者至少其一）；
2. 不要写统计句（不要写“今天共采集XX条”“今日热点集中在XX领域”这类话）；
3. 不要编造，不要写正确的废话。
只输出 JSON：{{"insight": "一句话"}}，不要输出其他内容。
"""


def generate_executive_summary(items, last_call_time):
    """今日一句话：取当日 ai_score 最高的 8 条，调一次 LLM 写洞察句。
    无 key 或调用失败时返回 ("", last_call_time)，不让整个摘要步失败。
    2026-11-15 新增（管线批次第 4 项）。"""
    import urllib.request
    api_key = os.environ.get('AGNES_API_KEY', '')
    base_url = os.environ.get('AGNES_BASE_URL', 'https://api.agnes-ai.cn/v1')
    model = os.environ.get('AGNES_MODEL') or "agnes-3.0-flash"
    if not api_key:
        return "", last_call_time
    scored = sorted(
        [it for it in items if isinstance(it.get('ai_score'), (int, float))],
        key=lambda x: x.get('ai_score', 0), reverse=True)[:8]
    if not scored:
        return "", last_call_time
    lines = []
    for i, it in enumerate(scored, 1):
        title = it.get('ai_title') or it.get('title', '')
        lines.append(f"{i}. [{it.get('ai_score')}] {title}")
    prompt = EXEC_SUMMARY_PROMPT.format(items="\n".join(lines))
    elapsed = time.time() - last_call_time
    if elapsed < 6.0:
        time.sleep(6.0 - elapsed)
    last_call_time = time.time()
    for attempt_model in [model, "agnes-2.5-flash"]:
        try:
            data = json.dumps({
                "model": attempt_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 200,
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
            insight = (json.loads(text.strip()).get("insight") or "").strip()
            if insight:
                return insight, last_call_time
        except Exception as e:
            print(f"  今日一句话失败 ({attempt_model}): {str(e)[:60]}", flush=True)
            continue
    return "", last_call_time


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
            ai_title = r.get('title', '') or ''
            if not validate_ai_title(it.get('title', ''), ai_title):
                print(f"  ai_title 校验不通过，已回落原标题: {ai_title[:40]}", flush=True)
                ai_title = it.get('title', '')
            it['ai_title'] = ai_title
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

    # 同步摘要到 v4（首页数据源，by_category 结构）
    v4_path = Path(f"src/data/v4/daily-{args.date}.json")
    if v4_path.exists():
        v4 = json.load(open(v4_path, encoding='utf-8'))
        sum_map = {it.get('url'): it for it in items if it.get('ai_summary') and it.get('url')}
        synced = 0
        for cat, v4_items in (v4.get('by_category') or {}).items():
            if not isinstance(v4_items, list):
                continue
            for vi in v4_items:
                src = sum_map.get(vi.get('url'))
                if src:
                    for k in ('ai_summary', 'ai_title', 'ai_reason', 'ai_score', 'content_type', 'content_type_label'):
                        if src.get(k):
                            vi[k] = src[k]
                    synced += 1
        # 今日一句话（执行摘要）：用当日最高分条目调一次 LLM，写进 v4 顶层
        # 防护（2026-11-18）：这一步绝不能拖垮 v4 同步——2026-11-15 起
        # EXEC_SUMMARY_PROMPT 里未转义的 {"insight": ...} 让 .format() 抛
        # KeyError，异常在 v4 写回之前抛出，4 天的 v4 文件都没拿到摘要，
        # 而 workflow 的 || echo 把失败吞掉了。先修转义，再加这层兜底。
        try:
            insight, last_call = generate_executive_summary(items, last_call)
        except Exception as e:
            print(f"  今日一句话异常，已跳过（v4 同步不受影响）: {str(e)[:60]}", flush=True)
            insight = ""
        if insight:
            v4["executive_summary"] = insight
            print(f"  今日一句话: {insight[:60]}", flush=True)
        json.dump(v4, open(v4_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f"已同步 {synced} 条摘要到 {v4_path}")
    else:
        print(f"v4 文件不存在，跳过同步: {v4_path}")

    if failed:
        print(f"失败 {len(failed)} 条（下次补跑）:")
        for t in failed[:10]:
            print(f"  - {t}")

if __name__ == '__main__':
    main()
