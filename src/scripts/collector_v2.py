"""
副业情报系统 v2.0 - Skills串联版
自动调用各Skill采集数据，统一存储，生成简报
"""

import subprocess
import json
import sqlite3
import time
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# ============ 配置 ============
WORKSPACE = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")
SKILLS_DIR = Path(r"C:\Users\douzi457\.qclaw\workspace\skills")
DATA_FILE = WORKSPACE / "intelligence_data.json"
REPORTS_DIR = WORKSPACE / "reports"
LOG_FILE = WORKSPACE / "crawl_log.txt"

# 确保目录存在
WORKSPACE.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# 时区
CST = timezone(timedelta(hours=8))

# ============ 日志 ============
def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

# ============ 调用Skill工具 ============

def run_python_script(script_path, *args):
    """运行Python脚本并返回JSON输出"""
    cmd = [sys.executable, str(script_path)] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, encoding='utf-8')
        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                return {"raw": result.stdout}
        return None
    except Exception as e:
        log(f"  ❌ 脚本异常 {script_path.name}: {e}")
        return None

def run_node_script(script_path, *args):
    """运行Node.js脚本并返回JSON输出"""
    cmd = ['node', str(script_path)] + list(args)
    try:
        # 使用encoding='utf-8'明确指定，避免Windows GBK解码问题
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding='utf-8', errors='replace')
        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout.strip())
            except json.JSONDecodeError as e:
                log(f"  ⚠️ JSON解析失败: {e}, raw: {result.stdout[:100]}")
                return {"raw": result.stdout}
        elif result.returncode != 0:
            log(f"  ⚠️ Node脚本返回码: {result.returncode}, stderr: {result.stderr[:200] if result.stderr else 'none'}")
        return None
    except Exception as e:
        log(f"  ❌ Node脚本异常 {script_path.name}: {e}")
        return None

def read_sqlite(db_path, query, params=None):
    """读取SQLite数据库"""
    if not Path(db_path).exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params or [])
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        log(f"  ❌ SQLite读取失败 {db_path.name}: {e}")
        return []

# ============ 数据采集 ============

def collect_news_aggregator():
    """调用 news-aggregator-skill 采集8大情报源"""
    log("📡 调用 news-aggregator-skill...")
    script = SKILLS_DIR / "news-aggregator-skill" / "scripts" / "fetch_news.py"
    
    # 采集所有源，每源10条
    all_items = []
    sources = ['hackernews', 'github', 'producthunt', '36kr', 'tencent', 'v2ex', 'wallstreetcn', 'ithome', 'chuangye', 'toutiao', 'bilibili']
    
    for src in sources:
        log(f"  → {src}...")
        result = run_python_script(script, "--source", src, "--limit", "10")
        if result and isinstance(result, list):
            for item in result:
                item['source_type'] = 'news_aggregator'
                item['original_source'] = src
                item['collected_at'] = datetime.now().isoformat()
            all_items.extend(result)
            log(f"    获取 {len(result)} 条")
        time.sleep(1)
    
    log(f"  ✅ news-aggregator 共 {len(all_items)} 条")
    return all_items

def collect_douyin():
    """调用 douyin-hot 采集抖音热榜"""
    log("🎵 调用 douyin-hot...")
    script = SKILLS_DIR / "douyin-hot" / "scripts" / "douyin_json.js"
    
    result = run_node_script(script, "50")
    if result and isinstance(result, list):
        items = []
        for item in result:
            if isinstance(item, dict):
                items.append({
                    'source_type': 'douyin',
                    'original_source': 'douyin_hot',
                    'collected_at': datetime.now().isoformat(),
                    'title': item.get('title', ''),
                    'desc': item.get('desc', ''),
                    'url': item.get('url', ''),
                    'hot_value': item.get('hot_value', item.get('popularity', 0)),
                    'rank': item.get('rank', 0),
                    'label': item.get('label', '')
                })
        log(f"  ✅ douyin 获取 {len(items)} 条")
        return items
    
    # 备选：直接读数据库
    db_path = SKILLS_DIR / "douyin-hot" / "data" / "douyin.db"
    if db_path.exists():
        rows = read_sqlite(db_path, "SELECT * FROM hot_items ORDER BY rank LIMIT 50")
        items = []
        for row in rows:
            items.append({
                'source_type': 'douyin',
                'original_source': 'douyin_hot',
                'collected_at': datetime.now().isoformat(),
                'title': row.get('title', ''),
                'desc': row.get('label', ''),
                'url': row.get('url', ''),
                'hot_value': row.get('popularity', 0),
                'rank': row.get('rank', 0)
            })
        log(f"  ✅ douyin 数据库读取 {len(items)} 条")
        return items
    
    log(f"  ⚠️ douyin 无数据")
    return []

def collect_gzh():
    """调用 gzh-explosive-content-detector 采集公众号爆款"""
    log("📝 调用 gzh-explosive-content-detector...")
    script = SKILLS_DIR / "gzh-explosive-content-detector" / "scripts" / "fetch_gzh_trends.py"
    
    # gzh脚本需要 --keyword 参数，输出到文件
    # 使用环境变量设置UTF-8编码避免Windows打印问题
    keywords = ["副业", "赚钱", "变现", "创业"]
    all_items = []
    
    for kw in keywords:
        log(f"  → 搜索: {kw}")
        output_file = SKILLS_DIR / "gzh-explosive-content-detector" / "scripts" / f"{kw}_爆款数据.json"
        
        cmd = [sys.executable, str(script), "--keyword", kw, "--max-items", "10", "--output-format", "json"]
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8', env=env)
            
            # 读取输出文件
            if output_file.exists():
                with open(output_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("items", []):
                        if isinstance(item, dict):
                            all_items.append({
                                'source_type': 'gzh',
                                'original_source': f'gzh_{kw}',
                                'collected_at': datetime.now().isoformat(),
                                'title': item.get('title', ''),
                                'desc': item.get('summary', ''),
                                'url': item.get('noteLink', ''),
                                'author': item.get('accountName', ''),
                                'read_count': item.get('interactiveCount', 0),
                                'data_score': item.get('dataScore', 0)
                            })
                    log(f"    {kw}: {len(data.get('items', []))} 条")
        except Exception as e:
            log(f"    ⚠️ {kw} 失败: {e}")
    
    log(f"  ✅ gzh 共 {len(all_items)} 条")
    return all_items

def collect_xiaohongshu():
    """调用 xiaohongshu 采集小红书数据"""
    log("📕 调用 xiaohongshu...")
    # 小红书skill主要是发布/管理，内容采集有限
    # 这里做个占位，后续可扩展
    log(f"  ⚠️ xiaohongshu 需手动操作，暂跳过")
    return []

def collect_weibo():
    """采集微博热搜数据"""
    log("🐚 调用 weibo-trending...")
    try:
        import requests
        url = 'https://weibo.com/ajax/statuses/hot_band'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://weibo.com',
            'Accept': 'application/json'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        data = resp.json()
        band_list = data.get('data', {}).get('band_list', [])
        
        items = []
        for item in band_list[:30]:
            word = item.get('word', item.get('hot_word', ''))
            raw_hot = item.get('raw_hot', 0)
            label = item.get('label', '')
            if word:
                items.append({
                    'source_type': 'weibo',
                    'original_source': 'weibo_hot',
                    'collected_at': datetime.now().isoformat(),
                    'title': word,
                    'desc': f'热度:{raw_hot} 标签:{label}',
                    'url': f'https://s.weibo.com/weibo?q={word}',
                    'author': '',
                    'read_count': int(raw_hot) if raw_hot else 0,
                    'data_score': min(100, int(raw_hot) / 10000) if raw_hot else 0
                })
        
        log(f"  ✅ weibo 获取 {len(items)} 条")
        return items
    except Exception as e:
        log(f"  ⚠️ weibo 失败: {e}")
        return []

def collect_app_store():
    """采集App Store新上架应用"""
    log("📱 调用 app-store-changelog...")
    # app-store-changelog是git changelog工具，不是数据采集
    # 我们用Product Hunt来监控新平台机会（已集成在news-aggregator）
    log(f"  ℹ️ App Store监控通过Product Hunt覆盖，跳过")
    return []

# ============ 数据处理 ============

def load_existing():
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
    if not text:
        return ""
    return str(text).lower().strip()[:200]

def merge_items(new_items, existing_items):
    """合并新旧数据，去重"""
    existing_map = {}
    for item in existing_items:
        key = normalize_text(item.get("title", ""))
        if key:
            existing_map[key] = item
    
    merged = list(existing_items)
    new_count = 0
    
    for item in new_items:
        key = normalize_text(item.get("title", ""))
        if key and key in existing_map:
            # 已存在，更新
            existing = existing_map[key]
            existing["last_seen"] = datetime.now().isoformat()
            existing["frequency"] = existing.get("frequency", 1) + 1
            # 保留更高分
            if item.get("hot_value", 0) > existing.get("hot_value", 0):
                existing["hot_value"] = item["hot_value"]
        elif key:
            # 新条目
            item["first_seen"] = datetime.now().isoformat()
            item["last_seen"] = datetime.now().isoformat()
            item["frequency"] = 1
            existing_map[key] = item
            merged.append(item)
            new_count += 1
    
    # 保留30天内的数据
    cutoff = datetime.now() - timedelta(days=30)
    result = []
    for item in merged:
        try:
            last_seen = datetime.fromisoformat(item.get("last_seen", "1970-01-01"))
            if last_seen > cutoff:
                result.append(item)
        except:
            result.append(item)
    
    log(f"  合并后总计: {len(result)} 条 (新增 {new_count} 条)")
    return result

def score_items(items):
    """评分排序"""
    keywords_high = ["AI", "GPT", "LLM", "Claude", "赚钱", "变现", "副业", "独立开发者", "收入", "MMR", "收入分享", "热榜", "爆款"]
    keywords_mid = ["工具", "开源", "产品", "创业", "开发者", "自动化", "工作流"]
    
    for item in items:
        score = item.get("frequency", 1) * 5
        score += min(item.get("hot_value", 0) / 1000, 30)  # 热值加成，封顶30分
        
        title_text = str(item.get("title", "")) + str(item.get("desc", ""))
        for kw in keywords_high:
            if kw.lower() in title_text.lower():
                score += 20
        for kw in keywords_mid:
            if kw.lower() in title_text.lower():
                score += 8
        
        item["score"] = min(score, 100)  # 封顶100分
    
    return sorted(items, key=lambda x: x.get("score", 0), reverse=True)

# ============ 生成简报 ============

def generate_report(items):
    """生成每日简报"""
    now = datetime.now(CST)
    date_str = now.strftime("%Y-%m-%d %H:%M")
    
    # 按类型分组
    by_source = {}
    for item in items:
        src = item.get("source_type", "unknown")
        if src not in by_source:
            by_source[src] = []
        by_source[src].append(item)
    
    # 生成报告
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
    
    # 保存报告
    report_file = REPORTS_DIR / f"daily_{now.strftime('%Y%m%d_%H%M')}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    log(f"  报告已保存: {report_file.name}")
    
    return "\n".join(report)

# ============ 主流程 ============

def run():
    """执行完整采集"""
    log("=" * 60)
    log("🚀 副业情报系统 v2.0 开始采集...")
    log("=" * 60)
    
    # 加载已有数据
    data = load_existing()
    existing_items = data.get("items", [])
    log(f"已有数据: {len(existing_items)} 条")
    
    # 采集各源
    all_new_items = []
    
    # 1. news-aggregator (8大源)
    items1 = collect_news_aggregator()
    all_new_items.extend(items1)
    time.sleep(2)
    
    # 2. 抖音
    items2 = collect_douyin()
    all_new_items.extend(items2)
    time.sleep(2)
    
    # 3. 公众号
    items3 = collect_gzh()
    all_new_items.extend(items3)
    time.sleep(2)
    
    # 4. 微博热搜
    items4 = collect_weibo()
    all_new_items.extend(items4)
    
    log(f"本次采集: {len(all_new_items)} 条")
    
    # 合并
    merged_items = merge_items(all_new_items, existing_items)
    
    # 评分
    scored_items = score_items(merged_items)
    
    # 保存
    save_data({"items": scored_items})
    
    # 生成简报
    log("📋 生成简报...")
    report = generate_report(scored_items)
    
    log("\n" + "=" * 60)
    log("✅ 采集完成!")
    log(f"总计: {len(scored_items)} 条 | 报告: {REPORTS_DIR}")
    log("=" * 60)
    
    return report

# ============ 入口 ============

if __name__ == "__main__":
    report = run()
    print("\n" + report)