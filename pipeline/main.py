# main.py — Pipeline 编排入口
# 用法: python -m pipeline.main
import json
import time
from datetime import datetime, timezone, timedelta
from .config import OUT_BASE, NOISY_PLATFORMS, NOISE_SCORE_THRESHOLD, MAX_NOISE_REMOVAL_RATIO
from .log import log, write_pipeline_log
from .fetch import fetch_newsnow_rss, fetch_direct_rss
from .process import process_ai_batch, baidu_translate, dedup_items
from .process.translate import translate_titles, contains_chinese
from .export import export_json, generate_focus, generate_daily_report


def filter_noisy_items(items):
    """筛掉低信噪比平台中的低质内容，带安全帽避免删太多。"""
    total = len(items)
    if total == 0:
        return items

    # 第一轮：按规则筛选
    filtered = []
    removed_count = 0
    for item in items:
        platform = item.get('platform', '')
        score = item.get('score', 0)
        category = item.get('category', '')

        if platform in NOISY_PLATFORMS:
            tech_categories = {'AI模型', '开源/开发者', '安全', '云服务', '消费电子'}
            if score >= NOISE_SCORE_THRESHOLD or category in tech_categories:
                filtered.append(item)
            else:
                removed_count += 1
        else:
            filtered.append(item)

    # 安全帽：如果删除量超过总量 30%，只删除最低分的，保留其余
    max_removal = int(total * MAX_NOISE_REMOVAL_RATIO)
    if removed_count > max_removal:
        # 把被删的按评分排序，只保留最低分的 N 条真正删除
        noisy_removed = sorted(
            [it for it in items if it.get('platform', '') in NOISY_PLATFORMS
             and it.get('score', 0) < NOISE_SCORE_THRESHOLD
             and it.get('category', '') not in {'AI模型', '开源/开发者', '安全', '云服务', '消费电子'}],
            key=lambda x: x.get('score', 0)
        )
        keep_back = noisy_removed[:removed_count - max_removal]  # 把分最高的几条救回来
        filtered.extend(keep_back)
        removed_count = max_removal
        log(f"  [Filter] safety cap: kept back {len(keep_back)} items (max removal {max_removal}/{total})")

    if removed_count > 0:
        log(f"  [Filter] removed {removed_count} low-quality items ({total} → {len(filtered)})")
    return filtered


def collect_all():
    """执行完整采集流水线。"""
    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz).strftime("%Y-%m-%d")
    log(f"=== Pipeline: {today} (Asia/Shanghai) ===")
    source_health = {}

    # ===== Step 1: 抓取 =====
    log("--- Stage 1: Fetch ---")
    all_items, newsnow_health = fetch_newsnow_rss()
    source_health['newsnow'] = newsnow_health

    supp_items = fetch_direct_rss()
    source_health['supplementary_rss'] = {"status": "success", "items": len(supp_items), "duration_ms": 0}
    all_items.extend(supp_items)
    log(f"  Total fetched: {len(all_items)} items")

    # ===== Step 2: AI 评分 + 翻译 =====
    log("--- Stage 2: AI Process ---")
    unprocessed = [it for it in all_items if it.get('score', 0) == 0]
    processed = [it for it in all_items if it.get('score', 0) > 0]
    log(f"  AI queue: {len(unprocessed)} new, {len(processed)} scored")

    unprocessed = process_ai_batch(unprocessed)
    all_items = unprocessed + processed

    # 英文标题翻译
    log("  Translating English titles...")
    all_items = translate_titles(all_items)

    # ===== Step 3: 去重 =====
    log("--- Stage 3: Dedup ---")
    total_before = len(all_items)
    all_items = dedup_items(all_items)
    log(f"  {total_before} → {len(all_items)} items")

    # 低信噪比平台筛选
    log("--- Stage 3.5: Quality Filter ---")
    all_items = filter_noisy_items(all_items)

    # 按评分降序
    all_items.sort(key=lambda x: x.get('score', 0), reverse=True)

    # ===== Step 4: 导出 =====
    log("--- Stage 4: Export ---")
    export_json(all_items, today)

    # Source health
    health_out = OUT_BASE / "source-health.json"
    with open(health_out, "w", encoding="utf-8") as f:
        json.dump({"date": today, "sources": source_health}, f, ensure_ascii=False, indent=2)

    # ===== Step 5: 今日重点 =====
    log("--- Stage 5: Focus ---")
    generate_focus(all_items, today)

    # ===== Step 6: 日报扩写 =====
    log("--- Stage 6: Daily Report ---")
    generate_daily_report(all_items, today)

    # 完成
    ai_scored = sum(1 for it in all_items if it.get('ai_summary'))
    log(f"=== Finished: {len(all_items)} items, {ai_scored} AI-scored ===")
    write_pipeline_log(today, "success", {
        "total_items": len(all_items),
        "ai_scored": ai_scored,
        "sources": {k: v.get("items", 0) for k, v in source_health.items()},
    })


if __name__ == "__main__":
    collect_all()
