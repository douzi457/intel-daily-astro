#!/usr/bin/env python3
"""
新词监测脚本：从 V4 日报数据中自动发现冒头的新名词（新AI工具/模型/开源项目）。

用法：
  python scripts/new_terms.py --date 2026-10-20

输入：
  - src/data/v4/daily-<today>.json（必需）
  - src/data/v4/daily-<past 14 days>.json（缺哪天跳过哪天）

输出：
  - src/data/v4/new-terms-<today>.json
  - src/data/v4/new-terms-latest.json（覆盖）
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

# ─── 停用表（拉丁词/中文常用词，按需扩充）────────────────────────────────
LATIN_STOPWORDS = {
    # 动词/名词常用词
    "ai", "app", "open", "source", "code", "tool", "platform", "model",
    "chat", "bot", "agent", "learn", "build", "run", "use", "make",
    "new", "big", "top", "best", "first", "last", "high", "low",
    "cloud", "web", "net", "data", "tech", "dev", "ui", "ux",
    "release", "launch", "update", "announced", "released", "introduced",
    "deploy", "train", "fine", "tune", "infer", "prompt",
    "gpt", "llm", "ml", "dl", "nn", "nlp", "cv", "rl",
    "deep", "neural", "network", "learning", "intelligence",
    "stable", "diffusion", "transformer", "attention",
    "microsoft", "google", "meta", "apple", "amazon", "nvidia",
    "github", "hugging", "face", "openai", "anthropic",
    "tech", "crunch", "verge", "port", "review",
    "help", "let", "how", "why", "what", "when", "where", "which",
    "this", "that", "with", "from", "into", "over", "after",
    "also", "even", "still", "well", "back", "just", "only",
    "make", "work", "get", "take", "give", "come", "go", "see",
    "know", "think", "say", "tell", "find", "put", "set",
    "need", "want", "try", "call", "keep", "start", "show",
    "read", "write", "watch", "play", "use", "buy", "sell",
    "run", "build", "create", "develop", "design", "test",
    "report", "study", "paper", "arxiv", "research",
    "agents", "models", "systems", "access", "share", "faster",
    "amid", "without", "around", "across", "about", "above",
    "based", "being", "between", "both", "could", "during",
    "each", "either", "enough", "every", "following", "great",
    "here", "however", "into", "its", "more", "most", "much",
    "must", "name", "never", "next", "other", "out", "over",
    "own", "same", "should", "some", "such", "than", "that",
    "their", "them", "then", "there", "these", "they", "through",
    "under", "until", "very", "was", "were", "what", "when",
    "where", "which", "while", "who", "whom", "why", "will",
    "with", "within", "without", "would", "year", "years",
    # 数字/版本/通用后缀
    "v1", "v2", "beta", "alpha", "pro", "plus", "lite", "max",
    "api", "sdk", "cli", "gui", "hci",
    "inc", "ltd", "corp", "gmbh", "co", "io",
    "2024", "2025", "2026", "2027",
}

ZH_STOPWORDS = {
    # 常见标题动词/连接词
    "发布", "推出", "上线", "开放", "宣布", "推出", "推出",
    "重磅", "最新", "今日", "早报", "晚报", "速递",
    "如何", "怎样", "为什么", "为何", "什么", "哪些",
    "一起", "一起来", "带你", "教你", "教你",
    "终于", "刚刚", "最新", "全新", "深度",
    "解析", "解读", "分析", "评测", "对比",
    "聊聊", "说说", "谈谈", "介绍", "详解",
    "国内", "国际", "全球", "中国", "美国",
    "巨头", "大厂", "中小", "创业", "融资",
    "开源", "闭源", "商用", "免费", "付费",
    "用户", "开发者", "工程师", "研究员",
    "模型", "工具", "平台", "系统", "产品",
    "能力", "性能", "效果", "速度", "成本",
    "挑战", "问题", "风险", "机遇", "趋势",
}


def is_latin_phrase(s: str) -> bool:
    """判断是否为有意义的拉丁词组（非停用词）"""
    s = s.strip().lower()
    if not s:
        return False
    # 纯数字/版本号过滤
    if re.fullmatch(r'\d+([.\-]\d+)*', s):
        return False
    if s in LATIN_STOPWORDS:
        return False
    # 长度过滤：至少2字符
    if len(s) < 2:
        return False
    return True


def extract_github_repo(url: str) -> str | None:
    """从URL中提取 github.com/<owner>/<repo> 的 repo 部分"""
    if not url:
        return None
    m = re.search(r'github\.com/([^/]+)/([^/?#]+)', url)
    if m:
        return m.group(2).lower()
    return None


def extract_latin_phrases(title: str) -> list[str]:
    """从标题中提取拉丁词组（连续英文单词/数字组合，长度>=2）
    过滤规则：
    - 排除常见英语虚词/动词/名词（扩充停用表）
    - 优先保留：驼峰命名、连字符组合、数字版本、全大写缩写
    """
    # 匹配连续的英文字母数字序列（至少2字符）
    tokens = re.findall(r'[A-Za-z][A-Za-z0-9]{1,}', title)
    results = []
    for t in tokens:
        t_low = t.lower()
        # 跳过停用词
        if t_low in LATIN_STOPWORDS:
            continue
        # 保留以下模式：
        # 1. 驼峰命名（如 DeepSeek、MiniMax）
        # 2. 连字符/点号组合（如 TorchNeuron、vLLM）
        # 3. 全大写缩写（如 AI、API、CLI）
        # 4. 含数字的版本号（如 V4.1、M3.1）
        # 5. 非标准大小写的混合词（如 hf、xrpl）
        is_camel = any(c.isupper() for c in t[1:]) and len(t) > 2
        is_hyphenated = '-' in t or '.' in t
        is_all_caps = t.isupper() and len(t) >= 2
        has_digit = any(c.isdigit() for c in t)
        if is_camel or is_hyphenated or is_all_caps or has_digit:
            results.append(t_low)
    return results


def extract_zh_bracketed(title: str) -> list[str]:
    """从标题中提取《》「」"""" 中的中文词组（1-8字，1字符以上即可）"""
    # 同时匹配ASCII引号和Unicode弯引号
    patterns = [
        r'《([^》]{1,8})》',
        r'「([^」]{1,8})」',
        r'"([^"]{1,8})"',  # ASCII double quotes
        '\u201c([^\u201d]{1,8})\u201d',  # Unicode left/right double quotes
        r"'([^']{1,8})'",  # ASCII single quotes
        '\u2018([^\u2019]{1,8})\u2019',  # Unicode left/right single quotes
    ]
    results = []
    for pat in patterns:
        matches = re.findall(pat, title)
        results.extend(matches)
    # 去重并保持顺序
    seen = set()
    unique = []
    for m in results:
        m = m.strip()
        if m and m not in seen and m not in ZH_STOPWORDS:
            seen.add(m)
            unique.append(m)
    return unique
    results = []
    for pat in patterns:
        matches = re.findall(pat, title)
        results.extend(matches)
    # 去重并保持顺序
    seen = set()
    unique = []
    for m in results:
        m = m.strip()
        if m and m not in seen and m not in ZH_STOPWORDS:
            seen.add(m)
            unique.append(m)
    return unique


def load_daily_data(date_str: str) -> dict | None:
    """加载指定日期的 V4 数据"""
    data_dir = Path(__file__).parent.parent / 'src' / 'data' / 'v4'
    file_path = data_dir / f'daily-{date_str}.json'
    if not file_path.exists():
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_terms_from_item(item: dict) -> list[tuple[str, str]]:
    """从单个条目提取候选词及其类型"""
    title = item.get('title_cn') or item.get('title', '')
    url = item.get('url', '')
    score = item.get('score', 0) or 0
    
    terms = []
    
    # 通道A：GitHub 仓库名
    repo = extract_github_repo(url)
    if repo:
        terms.append((repo, 'repo', score))
    
    # 通道A：标题中的拉丁词组
    for phrase in extract_latin_phrases(title):
        terms.append((phrase, 'latin', score))
    
    # 通道B：中文括号词组
    for phrase in extract_zh_bracketed(title):
        terms.append((phrase, 'zh', score))
    
    return terms


def compute_new_terms(today_data: dict, history: list[tuple[str, dict]]) -> list[dict]:
    """计算新词候选清单"""
    today = today_data.get('date', '')
    
    # 按天统计每个词的出现情况
    # word_stats[word] = {
    #   'kind': str,
    #   'days_seen': set(),       # 过去14天出现的天数集合
    #   'day_counts': dict,       # {date: count}
    #   'today_items': list,      # 今天的条目信息
    #   'scores': list,           # 所有出现过的score列表
    # }
    word_stats: dict[str, dict] = {}
    
    # 处理历史数据（过去14天）
    for hist_date, hist_data in history:
        if not hist_data or 'by_category' not in hist_data:
            continue
        for cat_items in hist_data['by_category'].values():
            for item in cat_items:
                for term, kind, score in extract_terms_from_item(item):
                    if term not in word_stats:
                        word_stats[term] = {
                            'kind': kind,
                            'days_seen': set(),
                            'day_counts': {},
                            'today_items': [],
                            'scores': [],
                        }
                    ws = word_stats[term]
                    ws['days_seen'].add(hist_date)
                    ws['day_counts'][hist_date] = ws['day_counts'].get(hist_date, 0) + 1
                    ws['scores'].append(score)
    
    # 处理今天数据
    today_items_by_term: dict[str, list[dict]] = {}
    if today_data and 'by_category' in today_data:
        for cat_items in today_data['by_category'].values():
            for item in cat_items:
                for term, kind, score in extract_terms_from_item(item):
                    if term not in word_stats:
                        word_stats[term] = {
                            'kind': kind,
                            'days_seen': set(),
                            'day_counts': {},
                            'today_items': [],
                            'scores': [],
                        }
                    ws = word_stats[term]
                    ws['day_counts'][today] = ws['day_counts'].get(today, 0) + 1
                    ws['today_items'].append({
                        'title': item.get('title_cn') or item.get('title', ''),
                        'url': item.get('url', ''),
                        'score': score,
                    })
                    ws['scores'].append(score)
                    # 收集 sample
                    if term not in today_items_by_term:
                        today_items_by_term[term] = []
                    today_items_by_term[term].append({
                        'title': item.get('title_cn') or item.get('title', ''),
                        'url': item.get('url', ''),
                        'score': score,
                    })
    
    # 判定 new / rising
    candidates = []
    for term, ws in word_stats.items():
        today_count = ws['day_counts'].get(today, 0)
        if today_count == 0:
            continue
        
        days_before = len(ws['days_seen'])
        
        # 计算过去14天单日平均
        total_days = len(ws['day_counts'])
        avg_daily = sum(ws['day_counts'].values()) / max(total_days, 1)
        
        status = None
        if days_before == 0 and today_count >= 2:
            status = 'new'
        elif days_before >= 1 and today_count >= max(3 * avg_daily, 3):
            status = 'rising'
        
        if status is None:
            continue
        
        # 计算分数
        avg_score_today = sum(it['score'] for it in ws['today_items']) / max(len(ws['today_items']), 1)
        score = today_count * avg_score_today
        
        # 取 Top 3 samples（按 score 排序）
        samples = sorted(ws['today_items'], key=lambda x: x['score'], reverse=True)[:3]
        
        # 判断强信号
        max_score = max((it['score'] for it in ws['today_items']), default=0)
        strong = False
        # 条件1：今天出现条数 >= 5 且最高 score >= 8
        if today_count >= 5 and max_score >= 8:
            strong = True
        # 条件2：通道A的仓库词且其条目进入当日高价值集合（score >= 8）
        if ws['kind'] == 'repo' and max_score >= 8:
            strong = True
        
        # 找首次出现日期
        all_dates = sorted(ws['day_counts'].keys())
        first_seen = all_dates[0] if all_dates else today
        
        candidates.append({
            'term': term,
            'kind': ws['kind'],
            'status': status,
            'first_seen': first_seen,
            'today_count': today_count,
            'max_score': round(max_score, 1),
            'avg_score_today': round(avg_score_today, 1),
            'strong': strong,
            'samples': [{'title': it['title'][:80], 'url': it['url']} for it in samples],
        })
    
    # 按 score 降序排序，取 Top 15
    candidates.sort(key=lambda x: x['today_count'] * x['avg_score_today'], reverse=True)
    return candidates[:15]


def main():
    parser = argparse.ArgumentParser(description='新词监测：发现日报中的冒头新名词')
    parser.add_argument('--date', required=True, help='目标日期 YYYY-MM-DD')
    parser.add_argument('--window', type=int, default=14, help='回溯天数（默认14）')
    args = parser.parse_args()
    
    target_date = args.date
    data_dir = Path(__file__).parent.parent / 'src' / 'data' / 'v4'
    
    # 加载今天数据
    today_data = load_daily_data(target_date)
    if not today_data:
        print(f'ERROR: 找不到数据文件 src/data/v4/daily-{target_date}.json', file=sys.stderr)
        sys.exit(1)
    
    # 加载历史数据
    history = []
    for i in range(1, args.window + 1):
        hist_date = (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=i)).strftime('%Y-%m-%d')
        hist_data = load_daily_data(hist_date)
        if hist_data:
            history.append((hist_date, hist_data))
    
    print(f'Loaded {len(history)} days of history (target: {target_date})')
    
    # 计算新词
    candidates = compute_new_terms(today_data, history)
    
    # 构建输出
    output = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'window_days': args.window,
        'target_date': target_date,
        'total_candidates': len(candidates),
        'terms': candidates,
    }
    
    # 写入文件
    out_filename = f'new-terms-{target_date}.json'
    out_path = data_dir / out_filename
    latest_path = data_dir / 'new-terms-latest.json'
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # 同步 latest
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'Output: {out_path}')
    print(f'Latest: {latest_path}')
    print(f'Candidates: {len(candidates)}')
    
    # 打印清单
    if candidates:
        print('\n=== 新词清单 ===')
        for i, c in enumerate(candidates, 1):
            strong_mark = ' ★' if c['strong'] else ''
            print(f"{i}. [{c['status']}] {c['term']} ({c['kind']}) ×{c['today_count']} score={c['avg_score_today']:.1f}{strong_mark}")
            for s in c['samples']:
                print(f"   - {s['title'][:60]}")
    else:
        print('\n无新词候选')
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
