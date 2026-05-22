import sys
sys.stdout.reconfigure(encoding='utf-8')

"""
副业情报系统 - 核心爬虫脚本
自动抓取多平台机会信息，汇总、去重、评分
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

# ============ 配置 ============
WORKSPACE = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")
DATA_FILE = WORKSPACE / "intelligence_data.json"
CONFIG_FILE = WORKSPACE / "sources_config.json"
LOG_FILE = WORKSPACE / "crawl_log.txt"

# 确保目录存在
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ============ 工具函数 ============

def log(msg):
    """写入日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

def load_data():
    """加载已有数据"""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"items": [], "last_update": None}

def save_data(data):
    """保存数据"""
    data["last_update"] = datetime.now().isoformat()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def normalize_text(text):
    """标准化文本用于去重"""
    return text.lower().strip().replace("\n", " ").replace("  ", " ")

def calculate_relevance_score(item, keywords):
    """计算相关性分数"""
    score = 0
    text = (item.get("title", "") + " " + item.get("desc", "")).lower()
    
    for kw in keywords:
        if kw.lower() in text:
            score += 10
    
    # 出现次数越多分数越高
    score += item.get("frequency", 1) * 5
    
    # 时效性加成（新发布）
    if item.get("is_new"):
        score += 5
    
    return score

# ============ 数据源定义 ============

SOURCES = {
    "github_trending": {
        "name": "GitHub Trending",
        "url": "https://api.github.com/search/repositories?q=created:>2024-01-01&sort=stars&per_page=20",
        "type": "api",
        "enabled": True
    },
    "product_hunt": {
        "name": "Product Hunt",
        "url": "https://www.producthunt.com/posts.json",
        "type": "json",
        "enabled": True
    }
}

# ============ 爬虫实现 ============

def crawl_github_trending():
    """抓取GitHub趋势"""
    items = []
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        resp = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": "created:>2024-01-01", "sort": "stars", "per_page": 15},
            headers=headers,
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            for repo in data.get("items", [])[:10]:
                items.append({
                    "source": "github",
                    "title": repo.get("full_name", ""),
                    "desc": repo.get("description", "") or "",
                    "url": repo.get("html_url", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "tags": repo.get("topics", []),
                    "category": "tech"
                })
                log(f"  GitHub: {repo.get('full_name', '')}")
        else:
            log(f"  GitHub API 失败: {resp.status_code}")
    except Exception as e:
        log(f"  GitHub 爬取异常: {e}")
    return items

def crawl_product_hunt():
    """抓取Product Hunt"""
    items = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }
        resp = requests.get(
            "https://producthunt.com/frontend/posts/list",
            headers=headers,
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            posts = data.get("posts", []) if isinstance(data, dict) else []
            for post in posts[:10]:
                items.append({
                    "source": "producthunt",
                    "title": post.get("name", ""),
                    "desc": post.get("tagline", "") or "",
                    "url": f"https://producthunt.com{post.get('url', '')}",
                    "votes": post.get("votes_count", 0),
                    "category": "product"
                })
                log(f"  PH: {post.get('name', '')}")
        else:
            log(f"  Product Hunt 失败: {resp.status_code}")
    except Exception as e:
        log(f"  Product Hunt 爬取异常: {e}")
    return items

def crawl_tech_news():
    """抓取科技新闻"""
    items = []
    sources = [
        ("36kr", "https://36kr.com/"),
        ("少数派", "https://sspai.com/"),
    ]
    for name, url in sources:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                log(f"  {name}: OK ({len(resp.text)} bytes)")
                # 简单记录，实际生产需要更复杂的解析
                items.append({
                    "source": name,
                    "title": f"{name} 最新内容",
                    "desc": f"从 {url} 获取",
                    "url": url,
                    "category": "news"
                })
        except Exception as e:
            log(f"  {name} 失败: {e}")
    return items

# ============ 去重与合并 ============

def deduplicate_and_merge(new_items, existing_items):
    """去重并合并新旧数据"""
    existing_map = {}
    for item in existing_items:
        key = normalize_text(item.get("title", ""))
        existing_map[key] = item
    
    merged = list(existing_items)
    new_count = 0
    
    for item in new_items:
        key = normalize_text(item.get("title", ""))
        if key in existing_map:
            # 已存在，增加频率计数
            existing_map[key]["frequency"] = existing_map[key].get("frequency", 1) + 1
            existing_map[key]["last_seen"] = datetime.now().isoformat()
            # 保留更高的分数
            if item.get("stars", 0) > existing_map[key].get("stars", 0):
                existing_map[key]["stars"] = item["stars"]
            if item.get("votes", 0) > existing_map[key].get("votes", 0):
                existing_map[key]["votes"] = item["votes"]
        else:
            # 新条目
            item["frequency"] = 1
            item["first_seen"] = datetime.now().isoformat()
            item["last_seen"] = datetime.now().isoformat()
            item["is_new"] = True
            existing_map[key] = item
            new_count += 1
    
    # 超过7天的数据降权
    cutoff = datetime.now() - timedelta(days=7)
    result = []
    for item in existing_map.values():
        last_seen = datetime.fromisoformat(item["last_seen"])
        if last_seen > cutoff:
            result.append(item)
    
    return result, new_count

def score_items(items):
    """对所有条目评分"""
    # 高价值关键词
    keywords = [
        "AI", "GPT", "Llama", "RAG", "知识库", "自动化",
        "模板", "工具", "工作流", "workflow", "automation",
        "API", "部署", "deploy", "开源", "open source"
    ]
    
    for item in items:
        item["score"] = calculate_relevance_score(item, keywords)
    
    return sorted(items, key=lambda x: x.get("score", 0), reverse=True)

# ============ 主流程 ============

def run_crawl():
    """执行一次完整爬取"""
    log("=" * 50)
    log("开始爬取...")
    
    # 加载现有数据
    data = load_data()
    existing_items = data.get("items", [])
    log(f"现有数据: {len(existing_items)} 条")
    
    # 爬取各平台
    all_new_items = []
    
    log("抓取 GitHub Trending...")
    all_new_items.extend(crawl_github_trending())
    time.sleep(2)
    
    log("抓取 Product Hunt...")
    all_new_items.extend(crawl_product_hunt())
    time.sleep(2)
    
    log("抓取科技新闻...")
    all_new_items.extend(crawl_tech_news())
    
    log(f"本次新获取: {len(all_new_items)} 条")
    
    # 去重合并
    merged_items, new_count = deduplicate_and_merge(all_new_items, existing_items)
    log(f"去重后总计: {len(merged_items)} 条 (新增 {new_count} 条)")
    
    # 评分排序
    scored_items = score_items(merged_items)
    log(f"评分完成，最高分: {scored_items[0].get('score', 0) if scored_items else 0}")
    
    # 保存
    save_data({"items": scored_items, "last_update": datetime.now().isoformat()})
    log(f"数据已保存到 {DATA_FILE}")
    
    # 输出Top5
    log("\n📊 TOP 5 机会:")
    for i, item in enumerate(scored_items[:5], 1):
        print(f"  {i}. [{item.get('source', '')}] {item.get('title', '')} (分数:{item.get('score', 0)}, 频率:{item.get('frequency', 1)})")
    
    log("\n爬取完成!")
    return scored_items

def get_daily_summary():
    """生成每日摘要"""
    data = load_data()
    items = data.get("items", [])
    
    if not items:
        return "今日情报：暂无数据，请先运行爬取"
    
    # 取Top10
    top_items = items[:10]
    
    summary = "📡 每日情报汇总\n" + "=" * 40 + "\n\n"
    
    # 按类别分组
    by_category = {}
    for item in top_items:
        cat = item.get("category", "other")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    for cat, cat_items in by_category.items():
        summary += f"📁 {cat.upper()}\n"
        for item in cat_items:
            freq = item.get("frequency", 1)
            score = item.get("score", 0)
            summary += f"  • {item.get('title', '')}\n"
            summary += f"    {item.get('desc', '')}\n"
            summary += f"    🔗 {item.get('url', '')}\n"
            summary += f"    📊 分数:{score} | 出现:{freq}次\n\n"
    
    summary += "=" * 40 + "\n"
    summary += f"更新时间: {data.get('last_update', '未知')}\n"
    
    return summary

# ============ 入口 ============

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--summary":
        print(get_daily_summary())
    else:
        run_crawl()
