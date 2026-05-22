# -*- coding: utf-8 -*-
"""
rewrite_to_json.py
从 intel.db 读取当日数据 → 调用智谱API改写 → 输出 rewrite/{date}.json
"""
import os, sys, json, sqlite3, re, time
from datetime import date, timedelta
from pathlib import Path

# ── 配置 ──────────────────────────────────────
WORKSPACE   = Path(__file__).parent
DB_PATH     = WORKSPACE / "db" / "intel.db"
OUT_DIR     = WORKSPACE / "rewrite"
OUT_DIR.mkdir(exist_ok=True)

ZHIPU_API   = os.environ.get("ZHIPU_API_KEY", "")
MODEL       = "glm-4-flash"
BATCH_SIZE  = 10          # 每批提交多少条
MAX_RETRIES= 3           # 失败重试次数
CACHE_FILE  = OUT_DIR / "processed_cache.json"   # 记录已改写过的id，避免重复改写

# ── 数据库 ────────────────────────────────────
def get_conn():
    return sqlite3.connect(DB_PATH)

def get_today_items():
    today = date.today().isoformat()
    conn = get_conn()
    cur = conn.execute(
        "SELECT id, title, description, url, source_type, original_source, hot_value, frequency "
        "FROM items WHERE date_key = ? ORDER BY hot_value DESC, score DESC LIMIT 200",
        (today,)
    )
    cols = [c[0] for c in cur.description]
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]

# ── 加载缓存 ──────────────────────────────────
def load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}

def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

# ── 智谱 API ──────────────────────────────────
def rewrite_batch(items, batch_num):
    """把一批items改写成新闻日报口语风格"""
    if not ZHIPU_API:
        # 无API时：纯规则处理（质量稍低但能跑）
        return [rule_rewrite(i) for i in items]

    prompt = build_prompt(items)
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    for attempt in range(MAX_RETRIES):
        try:
            import urllib.request, urllib.error
            req = urllib.request.Request(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Authorization": f"Bearer {ZHIPU_API}", "Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                return parse_response(content, items)
        except Exception as e:
            print(f"  ⚠ 重试 {attempt+1}/{MAX_RETRIES}: {e}")
            time.sleep(2 ** attempt)
    # 全部失败 → 回退规则处理
    return [rule_rewrite(i) for i in items]

def build_prompt(items):
    """构造批量改写prompt"""
    lines = []
    for i, it in enumerate(items):
        orig_title = it.get("title") or ""
        orig_desc  = it.get("description") or ""
        lines.append(
            f"【{i+1}】\n标题：{orig_title}\n描述：{orig_desc[:200]}"
        )
    prompt = (
        "你是一个科技/财经/热点新闻的编辑，擅长把原始信息改写成吸引人的日报风格短文。\n"
        "请将下面的信息逐条改写，每条返回JSON数组中的一个对象。\n"
        "规则：\n"
        "1. 标题：口语化、≤20字、能引发好奇或共鸣，不要标题党\n"
        "2. 描述：50-100字，真实使用感受或内容摘要，不要堆砌关键词\n"
        "3. 内容：原文超过100字则截断至100字，保持语句通顺\n"
        "4. 语言风格：像人整理的，不是AI堆砌的，短句为主\n"
        "5. 只改写【标题】【描述】【内容】，不要添加你自己的评论\n"
        "6. 严格返回JSON数组，不要有其他文字\n\n"
        + "\n\n".join(lines)
        + "\n\n请直接返回JSON数组："
    )
    return prompt

def parse_response(content, items):
    """解析API返回的JSON内容"""
    # 去掉markdown代码块
    content = re.sub(r"```(?:json)?", "", content).strip()
    try:
        arr = json.loads(content)
        if isinstance(arr, list) and len(arr) == len(items):
            results = []
            for i, item in enumerate(items):
                r = arr[i] if i < len(arr) else {}
                results.append({
                    "id":       item["id"],
                    "title":    str(r.get("标题", item.get("title", "")))[:20],
                    "desc":     str(r.get("描述", item.get("description", "")))[:100],
                    "content":  str(r.get("内容", item.get("description", "")))[:100],
                    "url":      item.get("url", ""),
                    "platform": item.get("source_type", ""),
                    "original": item.get("original_source", ""),
                    "hot":      item.get("hot_value", 0),
                })
            return results
    except Exception as e:
        print(f"  ⚠ JSON解析失败: {e}")
    return [rule_rewrite(it) for it in items]

def rule_rewrite(item):
    """纯规则改写（无API时 fallback）"""
    title = item.get("title") or ""
    desc  = item.get("description") or ""
    # 简单处理：截断 + 去除多余空格
    title_clean = re.sub(r"\s+", " ", title).strip()[:20]
    desc_clean  = re.sub(r"<[^>]+>", "", desc)   # 去除HTML标签
    desc_clean  = re.sub(r"\s+", " ", desc_clean).strip()[:100]
    return {
        "id":       item["id"],
        "title":    title_clean,
        "desc":     desc_clean,
        "content":  desc_clean,
        "url":      item.get("url", ""),
        "platform": item.get("source_type", ""),
        "original": item.get("original_source", ""),
        "hot":      item.get("hot_value", 0),
    }

# ── 主流程 ────────────────────────────────────
def main():
    print(f"📡 开始改写 {date.today().isoformat()}")
    items = get_today_items()
    print(f"   获取到 {len(items)} 条数据")

    cache    = load_cache()
    to_write = []
    skipped  = 0

    for it in items:
        if str(it["id"]) in cache:
            skipped += 1
            it["title"]    = cache[str(it["id"])]["title"]
            it["desc"]     = cache[str(it["id"])]["desc"]
            it["content"]  = cache[str(it["id"])]["content"]
            it["platform"] = cache[str(it["id"])]["platform"]
            it["original"] = cache[str(it["id"])]["original"]
            it["hot"]       = cache[str(it["id"])]["hot"]
            it["url"]       = cache[str(it["id"])]["url"]
            to_write.append(it)
        else:
            to_write.append(it)

    new_items = [it for it in to_write if str(it["id"]) not in cache]
    print(f"   已有缓存: {skipped} 条, 需改写: {len(new_items)} 条")

    # 批量改写
    all_results = []
    for i in range(0, len(to_write), BATCH_SIZE):
        batch = to_write[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"   处理批次 {batch_num}/{(len(to_write)+BATCH_SIZE-1)//BATCH_SIZE} ...")
        results = rewrite_batch(batch, batch_num)
        for r in results:
            cache[str(r["id"])] = {"title": r["title"], "desc": r["desc"], "content": r["content"],
                                   "platform": r["platform"], "original": r["original"],
                                   "hot": r["hot"], "url": r["url"]}
        all_results.extend(results)
        time.sleep(0.5)   # 避免请求过快

    save_cache(cache)

    # 输出 JSON
    today_str = date.today().isoformat()
    out_file = OUT_DIR / f"{today_str}.json"
    out_file.write_text(
        json.dumps({"date": today_str, "items": all_results}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ 改写完成 → {out_file}")

if __name__ == "__main__":
    main()
