# to_json.py — JSON 导出模块
import json
from ..config import PLATFORM_META, OUT_BASE
from ..log import log


def categorize_item(title, platform=""):
    """基于关键词的简单分类。"""
    title_lower = title.lower()
    if any(k in title_lower for k in ['ai', '人工智能', 'gpt', '模型', 'llm', '大模型', '机器学习', 'deep learning', 'neural']):
        return "AI模型"
    if any(k in title_lower for k in ['融资', '上市', 'ipo', '收购', '投资', '估值', '财报']):
        return "资本市场"
    if any(k in title_lower for k in ['iphone', '华为', '小米', 'oppo', 'vivo', '手机', '芯片', '半导体', '骁龙', '天玑']):
        return "消费电子"
    if any(k in title_lower for k in ['汽车', '新能源', '特斯拉', '比亚迪', '蔚来', '小鹏', '理想']):
        return "智能汽车"
    if any(k in title_lower for k in ['微信', '抖音', 'tiktok', '小红书', '快手', 'instagram', 'twitter']):
        return "社交平台"
    if any(k in title_lower for k in ['安全', '漏洞', '攻击', '勒索', '数据泄露', 'privacy']):
        return "安全"
    if any(k in title_lower for k in ['开源', 'github', 'docker', 'kubernetes', 'rust', 'python', 'javascript', 'react']):
        return "开源/开发者"
    if any(k in title_lower for k in ['腾讯云', '阿里云', 'aws', 'azure', 'cloud', '云服务']):
        return "云服务"
    return "其他"


def export_json(items, date_key):
    """导出中英双语 JSON 数据文件。"""
    zh_items = []
    en_items = []

    for idx, item in enumerate(items, 1):
        platform = item.get('platform', 'news_aggregator')
        meta = PLATFORM_META.get(platform, {"label": platform, "color": "#94A3B8", "icon": "📌"})
        title = item.get('title', '')
        clean_desc = (item.get('desc', '') or item.get('ai_summary', '') or '').replace("摘要：", "").replace("Summary:", "").strip()

        base = {
            "id": idx,
            "url": item.get('url', ''),
            "platform": platform,
            "platform_label": meta["label"],
            "platform_color": meta["color"],
            "platform_icon": meta["icon"],
            "hot": item.get('hot', 0),
            "date": date_key,
            "score": item.get('score', 0),
            "category": item.get('category', categorize_item(title, platform)),
            "cross_sources": len(item.get('merged_sources', [])) if item.get('merged_sources') else 0,
        }

        zh_item = dict(base, title=item.get('zh_title', '') or title, desc=clean_desc)
        en_item = dict(base, title=item.get('en_title', '') or title, desc=item.get('en_summary', '') or clean_desc)

        if item.get('merged_sources'):
            zh_item['merged_sources'] = item['merged_sources']
            en_item['merged_sources'] = item['merged_sources']

        zh_items.append(zh_item)
        en_items.append(en_item)

    out_zh = OUT_BASE / "zh"
    out_zh.mkdir(parents=True, exist_ok=True)
    with open(out_zh / f"{date_key}.json", "w", encoding="utf-8") as f:
        json.dump({"date": date_key, "items": zh_items}, f, ensure_ascii=False, indent=2)
    log(f"  zh: {len(zh_items)} items exported")

    out_en = OUT_BASE / "en"
    out_en.mkdir(parents=True, exist_ok=True)
    with open(out_en / f"{date_key}.json", "w", encoding="utf-8") as f:
        json.dump({"date": date_key, "items": en_items}, f, ensure_ascii=False, indent=2)
    log(f"  en: {len(en_items)} items exported")
