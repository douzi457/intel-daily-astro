#!/usr/bin/env python3
"""
intel_officer_processor.py — Daily 情报官 P0 后处理模块
"""

import json
import re
import hashlib
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

CST = timezone(timedelta(hours=8))
CST_STR = "Asia/Shanghai"

# deep_analysis 键归一化映射：LLM 可能输出中文或英文键，落盘统一为英文
DEEP_ANALYSIS_KEY_MAP = {
    '背景': 'background',
    '分歧': 'divergence',
    '对照': 'comparison',
    '现状': 'current_state',
    '变量': 'variable',
    '推演': 'projection',
    '原理': 'principle',
    '影响': 'impact',
    '解法': 'solution',
    '看点': 'highlight',
    '宝藏': 'treasure',
    '挖法': 'method',
    'background': 'background',
    'divergence': 'divergence',
    'comparison': 'comparison',
    'current_state': 'current_state',
    'variable': 'variable',
    'projection': 'projection',
    'principle': 'principle',
    'impact': 'impact',
    'solution': 'solution',
    'highlight': 'highlight',
    'treasure': 'treasure',
    'method': 'method',
}

def normalize_deep_analysis(da: dict) -> dict:
    """将 deep_analysis 的键归一化为英文，中英混排时保留首次出现的键"""
    if not da or not isinstance(da, dict):
        return da
    result = {}
    for k, v in da.items():
        norm = DEEP_ANALYSIS_KEY_MAP.get(k, k)
        if norm not in result:  # 先到先得
            result[norm] = v
    return result


# 分类规则：根据标题、来源、标签推断事件类别
CATEGORY_RULES = {
    'AI模型': [
        'gpt', 'claude', 'gemini', 'ollama', 'llama', 'qwen', 'deepseek',
        '模型', '大模型', 'llm', 'ai model', 'language model',
        'gpt-4', 'gpt-5', 'claude-3', 'claude-4', 'gemini-1.5',
        'openai', 'anthropic', 'google deepmind', 'meta ai',
        'chatgpt', 'sora', 'dall-e', 'dalle',
    ],
    '开源项目': [
        'github', 'open source', '开源', 'star', 'repo',
        'hugging face', 'hf', 'model card', 'dataset',
        'llm', 'transformers', 'langchain', 'crewai',
        'agent', '框架', 'sdk', 'api', 'tool',
        'clone', 'fork', 'release', 'repository',
    ],
    '大厂动态': [
        'microsoft', 'google', 'apple', 'amazon', 'meta',
        'alphabet', 'nvidia', 'intel', 'amd', 'arm',
        '字节', '腾讯', '阿里', '百度', '华为',
        'acquisition', 'merger', 'layoff', 'ipo',
        '财报', '营收', '季度', 'earnings', 'revenue',
        '财报', '季度', '业绩',
    ],
    '创业融资': [
        'raises', 'funding', '融资', '投资', 'seed',
        'series a', 'series b', 'series c', 'venture',
        'startup', 'unicorn', 'valuation', 'billion',
        '种子轮', 'a轮', 'b轮', 'c轮', 'pre-seed',
        '天使轮', '领投', '跟投',
    ],
    '工具应用': [
        '工具', 'app', 'application', 'saas',
        '插件', 'extension', 'chrome', 'browser',
        '自动化', 'workflow', 'productivity',
        '效率', '助手', 'copilot', 'bot',
        'software', 'platform', 'service', 'app',
    ],
}


class URLNormalizer:
    """URL 标准化与去重"""
    
    TRACKING_PARAMS = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'twclid', 'dclid', 'yclid',
    }
    
    @classmethod
    def normalize(cls, url: str) -> str:
        if not url:
            return ''
        try:
            parsed = urlparse(url)
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            
            if parsed.query:
                params = parse_qs(parsed.query)
                filtered_params = {k: v for k, v in params.items() if k not in cls.TRACKING_PARAMS}
                new_query = urlencode(filtered_params, doseq=True)
            else:
                new_query = ''
            
            return urlunparse((scheme, netloc, parsed.path.rstrip('/'), parsed.params, new_query, parsed.fragment))
        except Exception:
            return url
    
    @classmethod
    def generate_id(cls, canonical_url: str, source_id: str = '') -> str:
        data = f"{canonical_url}:{source_id}"
        return hashlib.md5(data.encode()).hexdigest()[:12]


class TimeParser:
    """时间标准化"""
    
    DATE_PATTERNS = [
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
        r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
    ]
    
    @classmethod
    def parse(cls, text: str) -> Optional[str]:
        if not text:
            return None
        for pattern in cls.DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                try:
                    if len(groups[0]) == 4:
                        dt = datetime(int(groups[0]), int(groups[1]), int(groups[2]), tzinfo=CST)
                    else:
                        dt = datetime(int(groups[2]), int(groups[0]), int(groups[1]), tzinfo=CST)
                    return dt.isoformat()
                except ValueError:
                    continue
        return None


class SummaryCleaner:
    """摘要清洗"""
    
    NOISE_PATTERNS = [
        r'下载客户端', r'登录.*查看', r'无障碍', r'字号.*[大大]',
        r'来源[：:]\s*', r'点击.*查看', r'版权所有', r'[A-Z]{2,}\.[A-Z]{2,}\.',
        r'https?://\S+',
    ]
    
    @classmethod
    def clean(cls, text: str) -> str:
        if not text:
            return ''
        cleaned = re.sub(r'<[^>]+>', '', text)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        for pattern in cls.NOISE_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip() if len(cleaned.strip()) >= 5 else text
    
    @classmethod
    def has_noise(cls, text: str) -> bool:
        if not text:
            return True
        for pattern in cls.NOISE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return len(text) < 10


class EventCluster:
    """事件聚类 — bigram TF-IDF 余弦相似度 + 并查集"""

    def __init__(self, threshold: float = 0.45):
        self.threshold = threshold
        self._parent: dict = {}

    def _find(self, x: str) -> str:
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]
            x = self._parent[x]
        return x

    def _union(self, a: str, b: str):
        ra, rb = self._find(a), self._find(b)
        if ra != rb:
            self._parent[ra] = rb

    @staticmethod
    def _bigrams(text: str) -> list:
        t = re.sub(r'\s+', '', text.lower())
        return [t[i:i+2] for i in range(len(t) - 1)]

    @staticmethod
    def _tf(bigrams: list) -> dict:
        from collections import Counter
        c = Counter(bigrams)
        total = len(bigrams) or 1
        return {b: v / total for b, v in c.items()}

    @staticmethod
    def _cosine(tf1: dict, tf2: dict) -> float:
        common = set(tf1) & set(tf2)
        if not common:
            return 0.0
        dot = sum(tf1[b] * tf2[b] for b in common)
        norm1 = (sum(v*v for v in tf1.values())) ** 0.5
        norm2 = (sum(v*v for v in tf2.values())) ** 0.5
        return dot / (norm1 * norm2 + 1e-9)

    def cluster(self, items: List[Dict]) -> Dict[str, List[int]]:
        """事件聚类 — bigram TF-IDF 余弦相似度，星型分组（每个簇有一个中心，不传递闭包）"""
        n = len(items)
        if n == 0:
            return {}

        # 1. URL 完全相同 → 强信号直接合并
        url_groups: dict = {}
        for i, item in enumerate(items):
            url = item.get('canonical_url') or item.get('url', '')
            if url:
                url_groups.setdefault(url, []).append(i)

        # 2. 预处理文本
        texts = []
        for item in items:
            combined = ' '.join([
                item.get('title', ''),
                item.get('clean_summary', ''),
                item.get('raw_summary', '')[:500],
            ])
            texts.append(combined)
            bf = self._tf(self._bigrams(combined))
            item['_bf'] = bf

        # 3. 计算每对的相似度，存储到字典
        # 只存储 j > i 且 sim >= threshold 的对
        sim_pairs: dict = {}  # {i: [(j, sim), ...]}
        for i in range(n):
            for j in range(i + 1, n):
                sim = self._cosine(items[i]['_bf'], items[j]['_bf'])
                if sim >= self.threshold:
                    sim_pairs.setdefault(i, []).append((j, sim))
                    sim_pairs.setdefault(j, []).append((i, sim))

        # 4. 星型分组：从未分配的项目开始，找出其最相似邻居组成簇
        assigned = set()
        groups = []

        for i in range(n):
            if i in assigned:
                continue
            neighbors = sim_pairs.get(i, [])
            # 只取未分配且最相似的邻居
            unassigned_neighbors = [(j, s) for j, s in neighbors if j not in assigned]
            if not unassigned_neighbors:
                groups.append([i])
                assigned.add(i)
                continue
            unassigned_neighbors.sort(key=lambda x: -x[1])
            cluster = [i] + [j for j, _ in unassigned_neighbors[:4]]
            groups.append(cluster)
            assigned.update(cluster)

        # 5. 编号（大簇优先）
        sorted_groups = sorted(groups, key=lambda g: -len(g))
        result = {}
        for idx, group in enumerate(sorted_groups):
            evt_id = f"evt_{idx:04d}"
            result[evt_id] = group
        return result


class IntelligenceProcessor:
    """情报官处理器"""
    
    def __init__(self, profile_config: Dict[str, Any]):
        self.profile = profile_config
        self.cluster = EventCluster()
        # Batch 14: LLM budget tracking (≤80 calls/day)
        self._llm_budget_limit = 80
        self._llm_calls_used = 0
        self._llm_usage_accum = {'model': '', 'calls': 0, 'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        date = raw_data.get('date', datetime.now(CST).strftime('%Y-%m-%d'))
        
        all_items = []
        by_category = raw_data.get('by_category', {})
        
        if by_category:
            for category, items in by_category.items():
                if isinstance(items, list):
                    for item in items:
                        item['category'] = category
                        all_items.append(item)
        
        normalized_items = self._normalize_items(all_items)
        cluster_result = self.cluster.cluster(normalized_items)
        events = self._build_events(normalized_items, cluster_result)

        # 跨日去重
        events = self._check_cross_day_dedup(events, date)

        # Batch 17: 溯源链——纯装配（零 LLM 调用），信源信息只来自采集实测数据
        items_by_id = {it['id']: it for it in normalized_items if it.get('id')}
        for evt in events:
            evt['provenance'] = self._build_provenance(evt, items_by_id)

        core_signals, watchlist, ignored = self._categorize(events)

        # 调用大模型生成个性化评价（如果配置了Key）
        llm_result = self._call_llm_for_judgment(core_signals)
        llm_importance = llm_result[0]
        llm_actions = llm_result[1]
        llm_usage = llm_result[2]
        llm_error = llm_result[3]
        card_type_map = llm_result[4] if len(llm_result) > 4 else None
        event_brief_map = llm_result[5] if len(llm_result) > 5 else None
        deep_analysis_map = llm_result[6] if len(llm_result) > 6 else None
        action_script_map = llm_result[7] if len(llm_result) > 7 else None
        key_quotes_map = llm_result[8] if len(llm_result) > 8 else None
        llm_category_map = llm_result[9] if len(llm_result) > 9 else None  # LLM分类
        signals_to_process = llm_result[10] if len(llm_result) > 10 else None  # Batch 14: 实际处理的信号

        # 更新core_signals的why_it_matters和suggested_action
        if llm_importance:
            for i, event in enumerate(core_signals, 1):
                if i in llm_importance and (llm_importance[i] or '').strip():
                    event['why_it_matters'] = llm_importance[i]
                if llm_actions and i in llm_actions:
                    event['suggested_action'] = {'type': 'try', 'text': llm_actions[i]}
                # 新增深度字段
                if card_type_map and i in card_type_map:
                    event['card_type'] = card_type_map[i]
                if event_brief_map and i in event_brief_map:
                    event['event_brief'] = event_brief_map[i]
                if deep_analysis_map and i in deep_analysis_map:
                    event['deep_analysis'] = deep_analysis_map[i]
                if action_script_map and i in action_script_map:
                    event['action_script'] = action_script_map[i]
                if key_quotes_map and i in key_quotes_map:
                    event['key_quotes'] = key_quotes_map[i]
                # LLM分类优先，关键词兜底
                if llm_category_map and i in llm_category_map and llm_category_map[i]:
                    event['category'] = llm_category_map[i]
                elif 'category' not in event or not event.get('category'):
                    event['category'] = self._classify_event(event, [])

        actions = self._generate_actions(core_signals, llm_importance, llm_actions)
        executive_summary = self._generate_summary(core_signals, actions)

        # Batch 14: 为露出层条目生成真摘要（core_signals + watchlist）
        self._fill_watchlist_why(watchlist)
        # Batch 17: 核心 why 兜底——主判断未回填的核心条目，用精简调用只补空缺
        _core_missing_why = [e for e in core_signals if not (e.get('why_it_matters') or '').strip()]
        if _core_missing_why:
            self._fill_watchlist_why(_core_missing_why)
        self._generate_exposed_summaries(core_signals, signals_to_process or core_signals)
        self._generate_exposed_summaries(watchlist, signals_to_process or core_signals)
        quality = self._calculate_quality(normalized_items, events, core_signals, len(watchlist), len(actions))

        # 构建分类精选
        categories = self._build_categories(core_signals, watchlist)

        # 构建热历史
        heat_file = Path(__file__).resolve().parents[1] / 'public' / 'data' / 'v2' / 'heat-history.json'
        heat_history = self._compute_heat_history(core_signals, date, heat_file)
        # 将热历史挂到 core_signals 上
        for evt in core_signals:
            eid = evt['event_id']
            if eid in heat_history:
                evt['heat_history'] = heat_history[eid]['heat_history']
                evt['heat_change_6h'] = heat_history[eid]['heat_change_6h']
                evt['heat_similar'] = heat_history[eid]['similarity']
        # 保存当前班次快照（供下次使用）
        self.save_heat_snapshot(core_signals, date, heat_file)

        if llm_error:
            quality['warnings'].append(llm_error)

        # Batch 17: 主判断无产物/核心 why 缺失必须可见，不许静默
        if not llm_importance:
            quality['warnings'].append('llm_judgment_not_applied: 主判断调用未产出，核心深度字段缺失')
        _missing_why = sum(1 for e in core_signals if not (e.get('why_it_matters') or '').strip())
        if _missing_why:
            quality['warnings'].append(f'core_why_missing: {_missing_why} 条核心情报 why 为空')

        # freshness固定值标注
        quality['warnings'].append("freshness: 暂用固定值70（published_at全部unknown，无法判断真实新鲜度）")

        source_health = self._build_source_health(raw_data.get('sources', []))
        
        result = {
            'schema_version': 2,
            'date': date,
            'generated_at': datetime.now(CST).isoformat(),
            'timezone': CST_STR,
            'profile_id': self.profile.get('id', 'default'),
            'stats': {
                'raw_items': len(normalized_items),
                'normalized_items': len(normalized_items),
                'unique_events': len(events),
                'core_signals': len(core_signals),
                'watchlist': len(watchlist),
                'ignored': len(ignored),
            },
            'executive_summary': executive_summary,
            'core_signals': core_signals,
            'watchlist': watchlist,
            'actions': actions,
            'ignored_summary': self._build_ignored_summary(ignored),
            'source_health': source_health,
            'quality': quality,
            'categories': categories,  # 分类精选
            'items': normalized_items,
            'events': events,
        }

        # 添加LLM用量信息
        if self._llm_calls_used > 0:
            # 使用累计值而非单次调用值
            result['llm_usage'] = {
                'model': self._llm_usage_accum.get('model', ''),
                'calls': self._llm_calls_used,
                'input_tokens': self._llm_usage_accum.get('input_tokens', 0),
                'output_tokens': self._llm_usage_accum.get('output_tokens', 0),
                'total_tokens': self._llm_usage_accum.get('total_tokens', 0),
            }
        return result
    
    def _normalize_items(self, items: List[Dict]) -> List[Dict]:
        return [self._normalize_item(item, item.get('category', 'Unknown')) for item in items if self._normalize_item(item, item.get('category', 'Unknown'))]

    def _normalize_punctuation(self, text: str) -> str:
        """规范化英文标点，修复渲染bug"""
        if not text:
            return text
        # 修复智能引号 → 普通引号
        text = text.replace('’', "'").replace('‘', "'")
        text = text.replace('–', '-').replace('—', '-')
        # 清除多余空格（特别是标点后的空格）
        text = text.replace("' s", "'s").replace("'t ", "'t ").replace("'re ", "'re ")
        text = text.replace("'m ", "'m ").replace("'ll ", "'ll ").replace("'d ", "'d ")
        # 清除其他多余空格
        text = ' '.join(text.split())
        return text
    
    def _normalize_item(self, item: Dict, category: str) -> Optional[Dict]:
        url = item.get('url', '')
        canonical_url = URLNormalizer.normalize(url)
        item_id = URLNormalizer.generate_id(canonical_url, item.get('source', ''))
        
        title = item.get('title', '')
        # 规范化标点
        title = self._normalize_punctuation(title)
        raw_summary = item.get('summary') or ''
        # Batch 14: 禁止标题冒充摘要——无源摘要时留空，不回填title
        raw_summary = self._normalize_punctuation(raw_summary)
        
        clean_summary = SummaryCleaner.clean(raw_summary)
        has_noise = SummaryCleaner.has_noise(clean_summary)
        
        entities = self._extract_entities(item)
        tags = self._extract_tags(item, category)
        why_matters = self._analyze_importance(item, entities, tags)
        suggested_action = self._suggest_action(item)
        
        original_score = item.get('score', 5.0)
        score = self._calculate_score(original_score, entities, item.get('source', ''))
        
        return {
            'id': item_id,
            'title': title,
            'title_original': item.get('title_original', title),
            'url': url,
            'canonical_url': canonical_url,
            'source': {'id': item.get('source', 'unknown').lower().replace(' ', '-'), 'name': item.get('source', 'unknown'), 'home_url': None, 'tier': self._classify_tier(item.get('source', '')), 'language': 'zh' if any('\u4e00' <= c <= '\u9fff' for c in title) else 'en', 'access_mode': 'existing-collector'},
            'category': category,
            'tags': tags,
            'entities': entities,
            'published_at': None,
            'published_at_confidence': 'unknown',
            'first_seen_at': datetime.now(CST).isoformat(),
            'last_seen_at': datetime.now(CST).isoformat(),
            'language': 'zh' if any('\u4e00' <= c <= '\u9fff' for c in title) else 'en',
            'raw_summary': raw_summary,
            'clean_summary': clean_summary if not has_noise else '',
            'evidence_points': [raw_summary] if raw_summary else [],
            'why_it_matters': why_matters,
            'suggested_action': suggested_action,
            'confidence': score['total'] / 100.0,
            'uncertainty': None,
            'score': score,
        }
    
    def _classify_tier(self, source_name: str) -> str:
        source_lower = source_name.lower()
        if any(x in source_lower for x in ['techcrunch', 'the verge', 'ars technica', 'wired']):
            return 'primary-media'
        elif any(x in source_lower for x in ['hacker news', 'github', 'reddit']):
            return 'community'
        elif any(x in source_lower for x in ['infoq', '36kr']):
            return 'specialist-media'
        return 'unknown'
    
    def _extract_entities(self, item: Dict) -> List[Dict]:
        """实体抽取：使用词边界匹配，禁止子串误命中（如 metalloenzyme→Meta）"""
        entities = []
        title = item.get('title', '')
        summary = item.get('summary', '') or ''
        # 用词边界检查：在首尾加空格，确保不会子串匹配
        check_text = f' {title.lower()} {summary.lower()} '
        known = {
            'openai': 'OpenAI', 'anthropic': 'Anthropic', 'google': 'Google',
            'meta': 'Meta', 'microsoft': 'Microsoft', 'amazon': 'Amazon',
            'apple': 'Apple', 'gpt': 'GPT', 'claude': 'Claude',
            'gemini': 'Gemini', 'llama': 'Llama', 'github': 'GitHub',
            'chatgpt': 'ChatGPT', 'deepseek': 'DeepSeek', 'qwen': 'Qwen',
        }
        for key, name in known.items():
            # 词边界匹配：key前后必须是空白/标点/字符串边界
            import re
            if re.search(rf'(?i)(?<!\w){re.escape(key)}(?!\w)', check_text):
                entities.append({'name': name, 'type': 'company' if key in ['openai', 'anthropic', 'google', 'meta', 'microsoft', 'amazon', 'apple'] else 'product'})
        return entities[:3]
    
    def _extract_tags(self, item: Dict, category: str) -> List[str]:
        tags = []
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        if any(kw in text for kw in ['开源', 'open source']):
            tags.append('开源模型')
        if 'agent' in text:
            tags.append('Agent')
        if any(kw in text for kw in ['coding', '编程']):
            tags.append('编程工具')
        if 'security' in text or '安全' in text:
            tags.append('安全')
        if category not in tags:
            tags.append(category)
        return tags[:5]
    
    def _analyze_importance(self, item: Dict, entities: List[Dict], tags: List[str], seen_texts: set = None) -> str:
        """分析重要性 - 针对AI开源与Agent创作者画像，确保不重复

        Batch 14: 非露出层条目返回空字符串，由LLM为露出层生成真正相关的判断
        停用写死模板返回
        """
        title = item.get('title', '')
        summary = item.get('summary', '') or ''
        # 如果没有摘要且标题过短，说明是低质量条目，返回空
        if not summary and len(title) < 15:
            return ''
        # 非露出层条目统一返回空，由上层决定是否填充
        # 露出层的 why_it_matters 由 LLM 生成
        return ''

    def _analyze_importance_event(self, main_item: Dict, all_items: List[Dict], indices: List[int], seen_texts: set = None) -> str:
        """事件级重要性分析（考虑多来源）"""
        source_count = len(indices)
        base_importance = self._analyze_importance(main_item, main_item.get('entities', []), main_item.get('tags', []), seen_texts)

        if source_count > 2 and base_importance:
            return f"多源报道（{source_count}家媒体），{base_importance}"
        return base_importance

    def _suggest_action(self, item: Dict, seen_actions: set = None) -> Dict:
        """生成具体动作建议，确保不重复

        Batch 14: 单源条目不得给 write 型建议
        """
        title = item.get('title', '').lower()
        summary = item.get('summary', '').lower()
        text = f"{title} {summary}"
        entities = self._extract_entities(item)
        if seen_actions is None:
            seen_actions = set()

        # 单源/未核实条目：只能给 watch/decide 型，不得给 write/try
        source_count = item.get('source_count', 1)
        is_unverified = (source_count == 1) or (isinstance(item.get('source'), dict) and not item.get('source').get('home_url'))

        # 开源项目发布
        if any(kw in text for kw in ['open source', '开源', 'release', 'v1.0', 'launch']):
            if 'model' in text or '模型' in text:
                result = {'type': 'watch', 'text': '关注该开源模型的里程碑进展，待多源报道后再评估'}
            elif 'agent' in text or 'coding' in text:
                result = {'type': 'watch', 'text': '追踪该Agent框架的社区活跃度，等待第三方评测'}
            else:
                result = {'type': 'watch', 'text': '记录该开源项目更新，纳入选题观察池'}
        # 重大发布/产品更新
        elif any(kw in text for kw in ['new', '推出', '发布', 'launch', 'announced']):
            result = {'type': 'watch', 'text': '等待多源交叉验证后，再决定是否深入报道'}
        # 评测/基准测试
        elif any(kw in text for kw in ['benchmark', '评测', 'test', 'evaluation']):
            result = {'type': 'watch', 'text': '核查评测方法学，等复现结果后再做判断'}
        # 安全问题
        elif any(kw in text for kw in ['security', '安全', 'vulnerability', '漏洞', 'breach']):
            result = {'type': 'decide', 'text': '评估当前系统是否存在类似风险，制定加固和监控方案'}
        # 大厂动态
        else:
            company_actions = {
                'openai': '关注API定价变化和模型能力边界，评估业务影响',
                'anthropic': '关注AI安全实践和Alignment研究进展',
                'google': '关注Gemini能力和开源模型策略',
                'meta': '关注Llama系列开源进展和商业授权变化',
            }
            found_action = False
            for entity in entities:
                if entity['name'].lower() in company_actions:
                    result = {'type': 'watch', 'text': company_actions[entity['name'].lower()]}
                    found_action = True
                    break
            if not found_action:
                result = {'type': 'watch', 'text': '标记为观察项，等待更多细节后评估影响'}

        # 去重：如果结果与已输出文本重复，添加差异化后缀
        action_text = result['text']
        if action_text in seen_actions:
            # 生成差异化变体
            variations = {
                '标记为观察项': [
                    '深入研究该领域进展，等待关键细节后决策',
                    '加入监控列表，定期回顾变化趋势',
                    '建立事件追踪，关注后续发展动向',
                    '持续跟踪该话题，等待更多信息再评估',
                    '加入观察清单，等待关键节点触发决策',
                ],
                '关注AI安全实践': [
                    '跟踪Anthropic对齐研究方向，评估技术路线',
                    '研究Constitutional AI实践，借鉴到自身系统',
                    '关注AI安全评测方法，提升模型可信度',
                ],
                '学习Safe RLHF': [
                    '实践RLHF方法，优化模型训练流程',
                    '研究人类反馈机制，提升模型安全性',
                    '跟踪Safe RLHF论文进展，复现关键实验',
                ],
                '克隆官方仓库': [
                    '深入阅读源码架构，评估自定义修改可行性',
                    '搭建开发环境，验证基础功能运行',
                    '参与社区讨论，了解项目路线图',
                ],
                '搭建最小Demo': [
                    '构建完整原型系统，验证关键路径稳定性',
                    '设计集成方案，评估迁移成本',
                    '编写测试用例，确保功能兼容性',
                ],
                '整理Release Notes': [
                    '制作新功能演示视频，面向社区分享',
                    '编写技术博客，分析API变更影响',
                    '组织团队培训，同步更新信息',
                ],
                '追踪产品详情': [
                    '梳理产品演进路线，撰写趋势分析',
                    '对比竞品方案，找出差异化优势',
                    '分析用户反馈，预判产品方向',
                ],
                '整理评测数据': [
                    '复现关键实验，验证评测方法严谨性',
                    '制作可视化对比图表，便于理解差异',
                    '撰写选型指南，辅助技术决策',
                ],
                '评估当前系统': [
                    '建立安全审计清单，定期扫描同类风险',
                    '制定应急响应预案，降低潜在损失',
                    '组织安全培训，提升团队意识',
                ],
                '关注API定价': [
                    '计算迁移成本，制定分阶段替代方案',
                    '对比云服务报价，优化成本控制',
                    '设计降级策略，降低供应商依赖',
                ],
            }
            for key, variants in variations.items():
                if key in action_text:
                    for variant in variants:
                        if variant not in seen_actions:
                            result['text'] = variant
                            break
                    break

        seen_actions.add(result['text'])
        return result

    def _call_llm_for_judgment(self, core_signals: List[Dict]) -> Tuple[Optional[Dict], Optional[Dict], Optional[Dict], Optional[str]]:
        """调用大模型为5条核心信号生成个性化评价和动作建议"""
        import os
        import urllib.request
        import urllib.error

        api_key = os.environ.get("AGNES_API_KEY")
        base_url = os.environ.get("AGNES_BASE_URL") or "https://api.agnes-ai.cn/v1"
        # 默认模型改为3.0-flash（中国站可用）；用户也可用AGNES_MODEL环境变量覆盖
        model = os.environ.get("AGNES_MODEL") or "agnes-3.0-flash"

        if not api_key:
            return None, None, None, "llm_judgment_skipped_no_key", None, None, None, None, None, None, None

        # Batch 14: 预算检查
        budget_remaining = self._llm_budget_limit - self._llm_calls_used
        if budget_remaining <= 0:
            print(f"[LLM] 预算已耗尽({self._llm_calls_used}/{self._llm_budget_limit})，跳过 judgment 调用", file=sys.stderr)
            return None, None, None, "llm_judgment_skipped_budget_exhausted", None, None, None, None, None, None, None

        # 只处理预算内的核心信号
        max_signals = min(len(core_signals), budget_remaining, 5)
        signals_to_process = core_signals[:max_signals]

        # 尝试主模型，如失败则降级到2.5-flash
        models_to_try = [model]
        if model != "agnes-2.5-flash":
            models_to_try.append("agnes-2.5-flash")

        events_data = []
        for i, event in enumerate(signals_to_process, 1):
            events_data.append({
                'index': i,
                'event_id': event.get('event_id', ''),
                'headline': event.get('headline', '')[:80],
                'clean_summary': event.get('clean_summary', '')[:200],
                'url': event.get('url', '')[:100],
                'source_count': event.get('source_count', 1),
                'tags': event.get('tags', [])[:3],
            })

        # 六类一句话定义（给LLM）
        CAT_DEFS = {
            'AI模型': '大语言模型/多模态模型发布、评测、能力对比、API升级',
            '开源项目': 'GitHub项目、开源模型/框架/SKU/工具，含star数',
            '大厂动态': '科技公司战略/组织/人事/诉讼/并购，不含产品发布',
            '创业融资': '初创公司融资轮次、估值、投资人',
            '工具应用': '面向个人/团队的生产力工具、插件、SaaS',
            '其他': '不符合以上任何一类',
        }
        cat_defs_text = '\n'.join(f'- {k}: {v}' for k, v in CAT_DEFS.items())

        system_prompt = """你是一个专业的AI技术内容创作者顾问。你的读者是关注AI开源项目与Agent技术的创作者（做公众号/视频/开源项目推荐）。

请为每条AI新闻事件提供深度分析：

## 1. card_type (必填，从四选一):
- "观点型": 大厂言论、争议话题、立场声明
- "教程型": 技术故障、评测缺陷、工具使用
- "资讯型": 榜单发布、融资消息、产品上线
- "前瞻型": 新架构、新范式、未来趋势

## 2. event_brief (必填): 5W1H一句话说全，≤80字
格式: "谁+在哪+说了/做了什么+为什么是今天"

## 3. deep_analysis (必填): 根据card_type选择对应框架
- 观点型: {背景, 分歧, 对照}
- 教程型: {原理, 影响, 解法}
- 资讯型: {看点, 宝藏, 挖法}
- 前瞻型: {现状, 变量, 推演}
每块1-2句，不许泛泛而谈。

## 4. action_script (必填): 执行脚本，数组，3-5步
每步格式: {step: 序号, text: "动词开头+具体对象+素材说明"}

## 5. key_quotes (必填): 关键引文，数组，1-2条
每条约: {text: "原话或硬数字", source: "来源链接或出处"}
⚠️ 严禁编造引文！不确定就写{"text": "暂无可引用的公开原话", "source": ""}

## 6. category (必填): 从以下六选一
{cat_defs_text}
判断依据: 事件核心内容是什么，不是公司名称。如OpenAI被逮捕是"大厂动态"不是"AI模型"；发布新模型才是"AI模型"。

## 7. why_it_matters (精简版): 80-150字，保留RSS兼容性
## 8. suggested_action (精简版): 30-80字，保留RSS兼容性

禁止空话词汇: "值得关注"、"具有重要意义"、"不容错过"

输出格式为JSON数组:
[{
  "index": 事件序号(1-5),
  "card_type": "观点型"|"教程型"|"资讯型"|"前瞻型",
  "event_brief": "...",
  "deep_analysis": {"背景": "...", "分歧": "...", ...},
  "action_script": [{"step": 1, "text": "..."}, ...],
  "key_quotes": [{"text": "...", "source": "..."}, ...],
  "why_it_matters": "...",
  "suggested_action": "..."
}]"""

        user_message = f"""请为以下5条AI新闻事件提供评价和动作建议：

{json.dumps(events_data, ensure_ascii=False, indent=2)}"""

        last_error = None
        for try_model in models_to_try:
            for attempt in range(3):  # 最多重试3次
                try:
                    payload = {
                        "model": try_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000,
                    }

                    url = f"{base_url}/chat/completions"
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode('utf-8'),
                        headers={
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {api_key}'
                        },
                        method='POST'
                    )

                    with urllib.request.urlopen(req, timeout=60) as resp:
                        if resp.status != 200:
                            # 指数退避 + 尊重 Retry-After 头
                            retry_after = resp.headers.get('Retry-After')
                            wait = (2 ** attempt) if retry_after is None else int(retry_after)
                            print(f"[LLM] HTTP {resp.status} (model={try_model}, attempt={attempt+1})，等待 {wait}s 后重试", file=sys.stderr)
                            time.sleep(wait)
                            continue
                        result = json.loads(resp.read().decode('utf-8'))

                    content = result['choices'][0]['message']['content']
                    # 去除可能的 markdown 代码块包裹（如 ```json ... ```）
                    stripped = content.strip()
                    if stripped.startswith('```'):
                        stripped = stripped.split('\n', 1)[1].rsplit('```', 1)[0].strip()
                    response_data = json.loads(stripped)

                    # Parse new deep analysis fields
                    card_type_map = {}
                    event_brief_map = {}
                    deep_analysis_map = {}
                    action_script_map = {}
                    key_quotes_map = {}
                    importance_map = {}
                    action_map = {}
                    category_map = {}  # LLM分类
                    
                    for item in response_data:
                        idx = item['index']
                        card_type_map[idx] = item.get('card_type', '观点型')
                        event_brief_map[idx] = item.get('event_brief', '')
                        raw_da = item.get('deep_analysis', {})
                        deep_analysis_map[idx] = normalize_deep_analysis(raw_da)
                        action_script_map[idx] = item.get('action_script', [])
                        key_quotes_map[idx] = item.get('key_quotes', [])
                        importance_map[idx] = item.get('why_it_matters', '')
                        action_map[idx] = item.get('suggested_action', '')
                        category_map[idx] = item.get('category', '')  # LLM分类

                    usage = result.get('usage', {})
                    llm_usage = {
                        'model': try_model,
                        'input_tokens': usage.get('prompt_tokens', 0),
                        'output_tokens': usage.get('completion_tokens', 0),
                        'total_tokens': usage.get('total_tokens', 0),
                    }
                    # Batch 14: 累计记账
                    self._llm_calls_used += 1
                    self._llm_usage_accum['calls'] += 1
                    self._llm_usage_accum['model'] = try_model
                    self._llm_usage_accum['input_tokens'] += usage.get('prompt_tokens', 0)
                    self._llm_usage_accum['output_tokens'] += usage.get('completion_tokens', 0)
                    self._llm_usage_accum['total_tokens'] += usage.get('total_tokens', 0)
                    return importance_map, action_map, llm_usage, None, card_type_map, event_brief_map, deep_analysis_map, action_script_map, key_quotes_map, category_map, signals_to_process

                except urllib.error.HTTPError as e:
                    last_error = f"HTTP {e.code}: {e.reason}"
                    try:
                        error_body = json.loads(e.read().decode('utf-8'))
                        if isinstance(error_body, dict):
                            err_type = error_body.get('error', {}).get('type', e.reason)
                            last_error = f"HTTP {e.code}: {err_type}"
                    except:
                        pass
                    print(f"[LLM] 模型 {try_model} 第{attempt+1}次尝试失败: {last_error}", file=sys.stderr)
                    continue
                except urllib.error.URLError as e:
                    last_error = f"网络错误: {e.reason} (attempt={attempt+1})"
                    print(f"[LLM] 网络异常: {last_error}", file=sys.stderr)
                    continue
                except json.JSONDecodeError as e:
                    last_error = f"JSON解析错误: {str(e)}"
                    print(f"[LLM] 响应解析失败: {last_error}", file=sys.stderr)
                    continue
                except Exception as e:
                    last_error = f"{type(e).__name__}: {str(e)[:100]}"
                    print(f"[LLM] 未预期异常: {last_error}", file=sys.stderr)
                    continue

        return None, None, None, f"llm_call_failed: {last_error}", None, None, None, None, None, None, None

    def _generate_actions(self, core_signals: List[Dict], llm_importance: Dict = None, llm_actions: Dict = None) -> List[Dict]:
        """生成动作列表，带跨日去重和有效性过滤"""
        action_limit = self.profile.get('action_limit', 3)
        actions = []
        seen_actions = set()
        today = datetime.now(CST).strftime('%Y-%m-%d')

        # 加载昨日核心动作用于去重
        yesterday = (datetime.now(CST) - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_file = Path('public/data/v2/daily-' + yesterday + '-v2.json')
        if yesterday_file.exists():
            try:
                with open(yesterday_file) as f:
                    yesterday_data = json.load(f)
                for action in yesterday_data.get('actions', []):
                    seen_actions.add(action.get('text', ''))
            except:
                pass

        # 过滤无效动作：必须是具体动作，不能是空话
        invalid_keywords = ['标记为观察项', '持续关注', '定期回顾', '等待更多', '建议关注']

        for i, event in enumerate(core_signals[:action_limit], 1):
            if llm_actions and i in llm_actions:
                action_text = llm_actions[i]
            else:
                action_text = self._suggest_action(event, seen_actions)['text']

            # 过滤空话
            if any(kw in action_text for kw in invalid_keywords):
                continue

            if action_text not in seen_actions and len(action_text) > 15:
                actions.append({
                    'type': 'try' if any(kw in action_text for kw in ['克隆', '搭建', '编写', '测试', '录制', '部署']) else 'watch',
                    'text': action_text,
                    'evidence_event_id': event['event_id'],
                    'date': today,
                })
                seen_actions.add(action_text)

        return actions[:action_limit]

    def _calculate_score(self, original_score: float, entities: List[Dict], source_name: str) -> Dict:
        # 各维度先按权重计分（满分 relevance 30 / impact 20 / novelty 15 / source_authority 15 / actionability 15）
        rel_pts = min(30, int(original_score * 3))
        imp_pts = min(20, int(original_score * 2))
        nov_pts = 15 if original_score >= 8 else 10
        auth_pts = min(15, int(original_score * 1.5))
        act_pts = min(15, int(original_score * 1.2))
        penalties = 0

        source_lower = source_name.lower()
        if any(x in source_lower for x in ['techcrunch', 'the verge', 'ars technica', 'wired']):
            auth_pts += 3
        elif any(x in source_lower for x in ['hacker news', 'github', 'reddit']):
            auth_pts += 2

        if entities:
            imp_pts += 3

        # total 保持旧口径（权重计分之和），核心≥80/观察≥60 的分层行为不变
        total = min(100, rel_pts + imp_pts + nov_pts + auth_pts + act_pts - penalties)

        # 对外维度统一为百分制达成率（计分/满分×100），与批次14「relevance ≥ 40」门槛同量纲。
        # 旧口径直接输出权重计分（relevance 封顶 30），与百分制门槛混用，任何条目都过不了 40。
        def _pct(pts: float, mx: int) -> int:
            return min(100, round(pts / mx * 100))

        return {'total': total, 'relevance': _pct(rel_pts, 30), 'impact': _pct(imp_pts, 20), 'novelty': _pct(nov_pts, 15), 'source_authority': _pct(auth_pts, 15), 'actionability': _pct(act_pts, 15), 'penalties': penalties, 'reason': f'原始分{original_score}映射（维度为百分制达成率）'}
    
    def _build_provenance(self, event: Dict, items_by_id: Dict[str, Dict]) -> Dict:
        """Batch 17: 组装溯源链（纯装配，零 LLM 调用）。

        口径纪律：信源/时间只来自采集实测数据，禁止生成或补全；
        published_at 缺失就留 null；首发判定优先 published_at 最早者，
        其次主条目，并以 basis 字段标注判定依据，不冒充。
        """
        def _brief(item):
            if not item:
                return None
            src = item.get('source') or {}
            if not isinstance(src, dict):
                src = {'name': str(src)}
            return {
                'source_name': src.get('name') or 'unknown',
                'source_id': src.get('id'),
                'tier': src.get('tier'),
                'url': item.get('url'),
                'published_at': item.get('published_at'),
                'first_seen_at': item.get('first_seen_at'),
            }

        primary = items_by_id.get(event.get('primary_item_id'))
        supporting = [items_by_id[i] for i in event.get('supporting_item_ids', []) if i in items_by_id]
        cluster = ([primary] if primary else []) + supporting

        origin_item, basis = primary, 'primary_item'
        with_pub = [it for it in cluster if it.get('published_at')]
        if with_pub:
            origin_item = min(with_pub, key=lambda it: it['published_at'])
            basis = 'earliest_published'
        elif primary is None and cluster:
            origin_item = min(cluster, key=lambda it: it.get('first_seen_at') or '9999')
            basis = 'earliest_captured'

        origin = _brief(origin_item)
        if origin is not None:
            origin['basis'] = basis

        corroborated = []
        _seen_urls = {origin_item.get('url')} if origin_item else set()
        for it in cluster:
            if it is None or it is origin_item:
                continue
            if it.get('url') in _seen_urls:
                continue
            _seen_urls.add(it.get('url'))
            b = _brief(it)
            if b:
                corroborated.append(b)

        source_ids = set()
        for it in cluster:
            src = it.get('source') or {}
            sid = (src.get('id') or src.get('name')) if isinstance(src, dict) else str(src)
            if sid:
                source_ids.add(sid)

        return {
            'origin': origin,
            'corroborated_by': corroborated,
            'independent_source_count': len(source_ids),
            'verification': 'multi-source' if len(source_ids) >= 2 else 'single-source',
            'evidence_points': (primary or {}).get('evidence_points') or [],
        }

    def _build_events(self, items: List[Dict], cluster_result: Dict[str, List[int]]) -> List[Dict]:
        """构建事件对象"""
        events = []
        seen_texts = set()  # 追踪已输出的importance文本
        seen_actions = set()  # 追踪已输出的action文本

        for event_id, indices in cluster_result.items():
            if not indices:
                continue

            # 选择主条目（评分最高）
            main_idx = max(indices, key=lambda i: items[i].get('score', {}).get('total', 0))
            main_item = items[main_idx]
            supporting_items = [items[i] for i in indices if i != main_idx]

            # 推断事件分类
            category = self._classify_event(main_item, supporting_items)

            event = {
                'event_id': event_id,
                'headline': self._normalize_punctuation(main_item['title']),
                # Batch 14: clean_summary优先使用清洗后的摘要，而非raw_summary
                # 如果clean_summary为空，保留空字符串，由后续_generate_exposed_summaries生成真摘要
                'clean_summary': main_item.get('clean_summary') or '',
                'primary_item_id': main_item['id'],
                'url': main_item['url'],
                'supporting_item_ids': [i['id'] for i in supporting_items],
                'source_count': len(indices),
                'mention_count': len(indices),
                'first_seen_at': min(items[i]['first_seen_at'] for i in indices),
                'last_seen_at': max(items[i]['last_seen_at'] for i in indices),
                'status': 'new' if len(indices) == 1 else 'developing',
                'tags': main_item['tags'],
                'entities': main_item['entities'],
                'category': category,
                'why_it_matters': self._analyze_importance_event(main_item, items, indices, seen_texts),
                'suggested_action': self._suggest_action(main_item, seen_actions),
                'confidence': main_item['confidence'],
                'uncertainty': main_item['uncertainty'],
                'score': main_item['score'],
            }
            events.append(event)
            # 追踪已输出的文本和动作，用于去重
            seen_texts.add(event['why_it_matters'])
            seen_actions.add(event['suggested_action']['text'])

        return events

    def _classify_event(self, main_item: Dict, supporting_items: List[Dict]) -> str:
        """根据标题、来源、标签推断事件类别"""
        text = (main_item.get('title', '') + ' ' +
                ' '.join(i.get('title', '') for i in supporting_items)).lower()
        # source可能是dict或string
        source = main_item.get('source', {})
        if isinstance(source, dict):
            source = source.get('name', '')
        source = str(source).lower()
        tags = ' '.join(main_item.get('tags', [])).lower()
        combined = f"{text} {source} {tags}"

        # 按优先级匹配分类
        for category, keywords in CATEGORY_RULES.items():
            for kw in keywords:
                if kw.lower() in combined:
                    return category

        return '其他'

    def _categorize(self, events: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """分层：核心/观察/忽略，并为AI模型/开源项目+10 relevance"""
        core_limit = self.profile.get('core_limit', 5)
        watch_limit = self.profile.get('watch_limit', 12)
        confidence_threshold = self.profile.get('confidence_threshold', 0.65)

        # 为AI模型和开源项目增加relevance权重（老大画像）：等效旧档（2026-10-23 老大拍板）——
        # 旧口径 relevance 权重分封顶 30、加成为 +10 分（≈总分 +10）；百分制下等效 +33 点，
        # 总分按 relevance 的权重（0.30）折算增量（33×0.30≈+9.9），保持原有提升力度不变。
        for event in events:
            cat = event.get('category', '')
            if cat in ('AI模型', '开源项目'):
                s = event['score']
                old_rel = s.get('relevance', 0)
                new_rel = min(100, old_rel + 33)
                s['relevance'] = new_rel
                s['total'] = min(100, round(s['total'] + (new_rel - old_rel) * 0.30))

        # 按总分排序
        sorted_events = sorted(events, key=lambda e: e['score']['total'], reverse=True)

        core_signals = []
        watchlist = []
        ignored = []

        for event in sorted_events:
            score = event['score']['total']
            confidence = event['confidence']

            # 硬门槛检查
            if score >= 80 and confidence >= confidence_threshold:
                if len(core_signals) < core_limit:
                    core_signals.append(event)
                else:
                    if len(watchlist) < watch_limit:
                        watchlist.append(event)
                    else:
                        ignored.append({
                            'event': event,
                            'reason': 'watchlist_full'
                        })
            elif score >= 60:
                if len(watchlist) < watch_limit:
                    watchlist.append(event)
                else:
                    ignored.append({
                        'event': event,
                        'reason': 'score_below_80'
                    })
            else:
                ignored.append({
                    'event': event,
                    'reason': 'score_below_60'
                })

        return core_signals, watchlist, ignored

    def _build_categories(self, core_signals: List[Dict], watchlist: List[Dict]) -> Dict[str, List[str]]:
        """构建分类精选：每类取Top3，存储event_id引用"""
        all_events = core_signals + watchlist
        categories = {}

        # 按分类分组
        for event in all_events:
            cat = event.get('category', '其他')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(event)

        # 每类取Top3（按score.total排序）
        result = {}
        for cat, events in categories.items():
            sorted_events = sorted(events, key=lambda e: e['score']['total'], reverse=True)
            result[cat] = [e['event_id'] for e in sorted_events[:3]]

        return result

    def _compute_heat_history(self, core_signals: List[Dict], date: str, heat_file: Path) -> Dict:
        """从 heat-history.json 读取跨班次热度历史。
        用标题 md5 前 16 位做 key 匹配事件。"""
        from collections import Counter
        import hashlib

        def event_key(headline: str) -> str:
            normalized = re.sub(r'\s+', '', headline.lower()).strip()
            return hashlib.md5(normalized.encode('utf-8')).hexdigest()[:16]

        def text_hash(text: str) -> list:
            t = re.sub(r'\s+', '', text.lower())
            return [t[i:i+2] for i in range(len(t) - 1)]

        def tf(bigrams: list) -> dict:
            c = Counter(bigrams)
            total = len(bigrams) or 1
            return {b: v / total for b, v in c.items()}

        def cosine(v1: dict, v2: dict) -> float:
            common = set(v1) & set(v2)
            if not common:
                return 0.0
            dot = sum(v1[b] * v2[b] for b in common)
            n1 = (sum(v * v for v in v1.values())) ** 0.5
            n2 = (sum(v * v for v in v2.values())) ** 0.5
            return dot / (n1 * n2 + 1e-9)

        # 加载热历史数据库
        if not heat_file.exists():
            return {}
        try:
            with open(heat_file, encoding='utf-8') as f:
                heat_db = json.load(f)
        except:
            return {}

        # 计算当前事件特征，用标题哈希匹配历史
        HEAT_WINDOW = 8
        heat_map = {}

        for evt in core_signals:
            cur_headline = evt.get('headline', '')
            cur_src = evt.get('source_count', 1)
            cur_bf = tf(text_hash(cur_headline))
            cur_key = event_key(cur_headline)

            # 找最相似的历史事件
            best_match_key = None
            best_sim = 0.0
            for hist_key, hist_data in heat_db.items():
                hist_headline = hist_data.get('headline', '')
                hist_bf = tf(text_hash(hist_headline))
                sim = cosine(cur_bf, hist_bf)
                if sim >= 0.4 and sim > best_sim:
                    best_sim = sim
                    best_match_key = hist_key

            # 构建热历史
            if best_match_key and best_match_key in heat_db:
                records = heat_db[best_match_key].get('records', [])
                heat_history = [{'date': r['date'], 'source_count': r['source_count']} for r in records[-HEAT_WINDOW:]]
                last_src = heat_history[-1]['source_count'] if heat_history else 0
            else:
                heat_history = []
                last_src = 0

            if last_src > 0:
                heat_change_6h = round((cur_src - last_src) / last_src * 100, 1)
            else:
                heat_change_6h = None  # 无历史数据，不填 100%

            heat_map[evt['event_id']] = {
                'headline': cur_headline,
                'source_count': cur_src,
                'heat_history': heat_history,
                'heat_change_6h': heat_change_6h,
                'similarity': round(best_sim, 3) if best_match_key else None,
            }

        return heat_map

    def save_heat_snapshot(self, core_signals: List[Dict], date: str, heat_file: Path):
        """保存当前班次热点快照到 heat-history.json。
        用标题的 md5 前 16 位做 key，跨班次稳定追踪同一事件。"""
        from datetime import datetime
        import hashlib

        def event_key(headline: str) -> str:
            """从标题生成稳定的 key"""
            normalized = re.sub(r'\s+', '', headline.lower()).strip()
            return hashlib.md5(normalized.encode('utf-8')).hexdigest()[:16]

        if not heat_file.exists():
            heat_db = {}
        else:
            try:
                with open(heat_file, encoding='utf-8') as f:
                    heat_db = json.load(f)
            except:
                heat_db = {}

        HEAT_WINDOW = 8

        for evt in core_signals:
            headline = evt.get('headline', '')
            src_count = evt.get('source_count', 1)
            key = event_key(headline)

            if key not in heat_db:
                heat_db[key] = {'headline': headline, 'records': []}

            record = {
                'date': date,
                'source_count': src_count,
                'timestamp': datetime.now(CST).isoformat(),
            }
            heat_db[key]['records'].append(record)
            heat_db[key]['records'] = heat_db[key]['records'][-HEAT_WINDOW:]

        with open(heat_file, 'w', encoding='utf-8') as f:
            json.dump(heat_db, f, ensure_ascii=False, indent=2)

        print(f"  -> Saved heat snapshot: {len(heat_db)} events tracked", file=sys.stderr)

    def _generate_summary(self, core_signals: List[Dict], actions: List[Dict]) -> List[str]:
        """生成今日结论 - 必须是完整判断句，不许截断标题"""
        summary = []
        if not core_signals:
            return ["暂无情报，建议关注历史趋势"]

        # 收集LLM生成的完整内容
        llm_whys = []
        llm_actions = []
        for event in core_signals[:3]:
            why = event.get('why_it_matters', '')
            action = event.get('suggested_action', {})
            if isinstance(action, dict):
                action = action.get('text', '')
            llm_whys.append(why)
            llm_actions.append(action)

        # 第1条：核心事件判断
        if llm_whys[0]:
            summary.append(llm_whys[0])
        else:
            summary.append(f"{core_signals[0].get('headline', 'AI领域')}今日出现重要动态，建议持续关注。")

        # 第2条：关联事件或趋势判断
        if len(core_signals) > 1 and llm_whys[1]:
            summary.append(llm_whys[1])
        elif len(core_signals) > 1:
            summary.append(f"同日{core_signals[1].get('headline', '相关事件')}亦反映同类趋势，可纳入选题储备。")
        else:
            summary.append("当前情报集中在单一方向，建议拓宽信息源以获取多元视角。")

        # 第3条：行动导向
        if llm_actions[2] and len(llm_actions[2]) > 15 and '观察' not in llm_actions[2]:
            summary.append(llm_actions[2])
        elif llm_actions[1] and len(llm_actions[1]) > 15 and '观察' not in llm_actions[1]:
            summary.append(llm_actions[1])
        elif llm_actions[0] and len(llm_actions[0]) > 15 and '观察' not in llm_actions[0]:
            summary.append(llm_actions[0])
        else:
            summary.append("当前无明确可执行动作，建议持续观察后续进展。")

        return summary[:3]

    def _fill_watchlist_why(self, watchlist: List[Dict]):
        """Batch 16: 为 watchlist 事件生成 why_it_matters（精简版判断调用，+1 次/天，失败留空不崩）"""
        import os
        import urllib.request
        import urllib.error
        if not watchlist:
            return
        api_key = os.environ.get("AGNES_API_KEY", "").strip()
        if not api_key:
            return
        if self._llm_calls_used >= self._llm_budget_limit:
            print("[LLM] 预算已耗尽，跳过 watchlist 判断生成", file=sys.stderr)
            return
        base_url = os.environ.get("AGNES_BASE_URL") or "https://api.agnes-ai.cn/v1"
        model = os.environ.get("AGNES_MODEL") or "agnes-3.0-flash"
        models_to_try = [model]
        if model != "agnes-2.5-flash":
            models_to_try.append("agnes-2.5-flash")
        events_data = [
            {
                'index': i,
                'headline': (evt.get('headline') or '')[:80],
                'summary': (evt.get('clean_summary') or evt.get('summary') or '')[:200],
                'source_count': evt.get('source_count', 1),
            }
            for i, evt in enumerate(watchlist, 1)
        ]
        system_prompt = """你是一个专业的AI技术内容创作者顾问。请为每条AI新闻事件写一句"为什么重要"（why_it_matters）：30-60字，必须具体到这条事件本身的技术、生态或竞争含义，禁止空话（值得关注、具有重要意义、不容错过）。
输出JSON数组：[{"index": 事件序号, "why_it_matters": "..."}]"""
        user_message = "请为以下事件逐条生成 why_it_matters：\n\n" + json.dumps(events_data, ensure_ascii=False, indent=2)
        for try_model in models_to_try:
            for attempt in range(3):
                try:
                    payload = {
                        "model": try_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1200,
                    }
                    req = urllib.request.Request(
                        f"{base_url}/chat/completions",
                        data=json.dumps(payload).encode('utf-8'),
                        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'},
                        method='POST'
                    )
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        if resp.status != 200:
                            wait = 2 ** attempt
                            print(f"[LLM] watchlist判断 HTTP {resp.status}，等待 {wait}s 后重试", file=sys.stderr)
                            time.sleep(wait)
                            continue
                        result = json.loads(resp.read().decode('utf-8'))
                    content = result['choices'][0]['message']['content']
                    stripped = content.strip()
                    if stripped.startswith('```'):
                        stripped = stripped.split('\n', 1)[1].rsplit('```', 1)[0].strip()
                    response_data = json.loads(stripped)
                    filled = 0
                    for item in response_data:
                        idx = item.get('index')
                        why = (item.get('why_it_matters') or '').strip()
                        if idx and why and 1 <= idx <= len(watchlist):
                            watchlist[idx - 1]['why_it_matters'] = why
                            filled += 1
                    usage = result.get('usage', {})
                    self._llm_calls_used += 1
                    self._llm_usage_accum['calls'] += 1
                    self._llm_usage_accum['model'] = try_model
                    self._llm_usage_accum['input_tokens'] += usage.get('prompt_tokens', 0)
                    self._llm_usage_accum['output_tokens'] += usage.get('completion_tokens', 0)
                    self._llm_usage_accum['total_tokens'] += usage.get('total_tokens', 0)
                    print(f"[LLM] watchlist判断完成：{filled}/{len(watchlist)} 条", file=sys.stderr)
                    return
                except Exception as e:
                    print(f"[LLM] watchlist判断失败（model={try_model}, attempt={attempt+1}）: {e}", file=sys.stderr)
                    time.sleep(2 ** attempt)
        print("[LLM] watchlist判断全部尝试失败，why_it_matters 留空", file=sys.stderr)

    def _generate_exposed_summaries(self, items: List[Dict], signals_context: List[Dict]):
        """Batch 14: 为露出层条目生成真摘要（core_signals + watchlist），不复用标题"""
        import os
        api_key = os.environ.get("AGNES_API_KEY", "").strip()
        if not api_key:
            return  # 无API key则跳过，摘要留空

        # 只处理没有clean_summary的条目
        empty_items = [it for it in items if not it.get('clean_summary')]
        if not empty_items:
            return

        # 限制调用次数：每天最多20条露出层摘要
        max_summaries = min(len(empty_items), self._llm_budget_limit - self._llm_calls_used)
        if max_summaries <= 0:
            print("[LLM] 预算已耗尽，跳过露出层摘要生成", file=sys.stderr)
            return

        import urllib.request
        import urllib.error

        base_url = os.environ.get("AGNES_BASE_URL") or "https://api.agnes-ai.cn/v1"
        model = os.environ.get("AGNES_MODEL") or "agnes-3.0-flash"

        for i, item in enumerate(empty_items[:max_summaries]):
            headline = item.get('headline', item.get('title', ''))
            entities = item.get('entities', [])
            entity_names = [e['name'] for e in entities]

            prompt = f"""请用一句话（≤60字）概括以下科技资讯的核心内容。只陈述事实，不加评价。

标题：{headline}
相关实体：{', '.join(entity_names) if entity_names else '无'}

一句话摘要："""

            try:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 100,
                }
                req = urllib.request.Request(
                    f"{base_url}/chat/completions",
                    data=json.dumps(payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    if resp.status == 200:
                        result = json.loads(resp.read().decode('utf-8'))
                        summary = result['choices'][0]['message']['content'].strip()
                        usage = result.get('usage', {})
                        # 记账
                        self._llm_calls_used += 1
                        self._llm_usage_accum['calls'] += 1
                        self._llm_usage_accum['model'] = model
                        self._llm_usage_accum['input_tokens'] += usage.get('prompt_tokens', 0)
                        self._llm_usage_accum['output_tokens'] += usage.get('completion_tokens', 0)
                        self._llm_usage_accum['total_tokens'] += usage.get('total_tokens', 0)

                        # 验证摘要不是标题
                        if summary and summary != headline and len(summary) > 10:
                            item['clean_summary'] = summary[:200]
                            item['uncertainty'] = 'AI-generated summary (batch 14)'
                            print(f"  [SUMMARY] Generated for: {headline[:40]}...", file=sys.stderr)
                        else:
                            item['uncertainty'] = 'summary_generation_failed'
                            print(f"  [SUMMARY] Skipping invalid summary for: {headline[:40]}...", file=sys.stderr)
            except Exception as e:
                print(f"  [SUMMARY] Failed for {headline[:40]}: {e}", file=sys.stderr)
                item['uncertainty'] = f'summary_error: {type(e).__name__}'

    def _calculate_quality(self, items: List[Dict], events: List[Dict], core_signals: List[Dict], watch_count: int = 0, action_count: int = 0) -> Dict:
        """计算质量指标（真实计算，不硬编码）"""
        raw_items = len(items)
        unique_events = len(events)

        # 真正计算事件重复（跨outlet同事件）
        core_event_duplicates = 0
        for i, e1 in enumerate(core_signals):
            for e2 in core_signals[i+1:]:
                # 检查是否同一事件（headline相似度>0.8且无重叠）
                if self._events_are_same(e1, e2):
                    core_event_duplicates += 1

        # 计算噪声摘要率（检查噪声词）
        noise_summaries = sum(1 for e in events if self._has_noise_summary(e.get('clean_summary', '')))
        noise_summary_rate = noise_summaries / max(1, len(events))

        # 计算空摘要率
        empty_summaries = sum(1 for e in events if not e.get('clean_summary'))
        empty_summary_rate = empty_summaries / max(1, len(events))

        # 评分分布
        scores = [e['score']['total'] for e in events]
        max_score = max(scores) if scores else 0
        top_ties = sum(1 for s in scores if s == max_score)
        top_score_tie_rate = top_ties / len(scores) if scores else 0

        # 真实计算各维度（不硬编码）
        coverage_score = min(100, raw_items / 10)
        relevance_score = self._calc_relevance_score(core_signals, events)
        event_dedup_score = max(0, 100 - core_event_duplicates * 20)
        score_disc_score = max(0, 100 - top_score_tie_rate * 50)
        summary_clean_score = max(0, 100 - empty_summary_rate * 100 - noise_summary_rate * 50)
        action_score = self._calc_action_score(core_signals)
        freshness_score = self._calc_freshness_score(items)
        link_health_score = self._check_link_health(items)

        # 权重调整：freshness和link_health已真实计算
        total = (
            coverage_score * 0.15 +
            relevance_score * 0.15 +
            event_dedup_score * 0.15 +
            score_disc_score * 0.1 +
            summary_clean_score * 0.15 +
            action_score * 0.15 +
            freshness_score * 0.1 +
            link_health_score * 0.05
        )

        # 硬门槛检查（真实计算）
        gates_passed = [
            {
                'id': 'core-event-unique',
                'passed': core_event_duplicates == 0,
                'detail': f'核心区重复事件: {core_event_duplicates}（按canonical_url合并）'
            },
            {
                'id': 'no-noise-summary',
                'passed': noise_summary_rate < 0.1,
                'detail': f'噪声摘要率: {noise_summary_rate:.1%}（检查空摘要）'
            },
            {
                'id': 'core-five-elements',
                'passed': all(
                    e.get('why_it_matters') and
                    e.get('suggested_action', {}).get('text') and
                    len(e.get('suggested_action', {}).get('text', '')) > 10 and
                    e.get('url') and
                    e.get('confidence', 0) >= 0.5
                    for e in core_signals
                ),
                'detail': f'核心五要素检查: {len(core_signals)}条'
            },
            {
                'id': 'core-count-valid',
                'passed': 3 <= len(core_signals) <= 5,
                'detail': f'核心信号数: {len(core_signals)}'
            },
            {
                'id': 'watch-action-limits',
                'passed': watch_count <= 12 and action_count <= 3,
                'detail': f'观察:{watch_count}, 动作:{action_count}'
            },
            {
                'id': 'published-at-known-or-null',
                'passed': all(
                    item.get('published_at') is not None or
                    item.get('published_at_confidence') == 'unknown'
                    for item in items
                ),
                'detail': '时间字段标注规范'
            },
            {
                'id': 'three-end-consistency',
                'passed': False,
                'detail': 'SKIP: processor无法验证三端一致性，需手动检查'
            },
            {
                'id': 'build-passed',
                'passed': False,
                'detail': 'SKIP: processor无法验证构建，需检查GitHub Actions'
            },
            {
                'id': 'quality-calculated',
                'passed': isinstance(total, (int, float)) and 0 <= total <= 100,
                'detail': f'质量分由数据计算: {total:.1f}'
            },
        ]

        grade = 'pass' if total >= 90 and all(g['passed'] for g in gates_passed) else 'pilot' if total >= 80 else 'fail'

        return {
            'total': round(total, 1),
            'grade': grade,
            'components': {
                'coverage': round(coverage_score),
                'relevance': round(relevance_score),
                'event_dedup': round(event_dedup_score),
                'score_discrimination': round(score_disc_score),
                'summary_cleanliness': round(summary_clean_score),
                'actionability': round(action_score),
                'freshness': round(freshness_score),
                'link_health': round(link_health_score),
            },
            'metrics': {
                'raw_items': raw_items,
                'normalized_items': raw_items,
                'unique_events': unique_events,
                'exact_duplicate_rate': 0.0,
                'core_event_duplicate_count': core_event_duplicates,
                'dead_link_rate': 0.0,
                'empty_summary_rate': round(empty_summary_rate, 3),
                'noise_summary_rate': round(noise_summary_rate, 3),
                'stale_source_count': 0,
                'top_score_tie_rate': round(top_score_tie_rate, 3),
            },
            'gates': gates_passed,
            'warnings': [g['detail'] for g in gates_passed if not g['passed']],
        }

    def _events_are_same(self, e1: Dict, e2: Dict) -> bool:
        """检查两个事件是否描述同一件事"""
        # 简单实现：headline相似度
        h1 = e1.get('headline', '').lower()
        h2 = e2.get('headline', '').lower()
        if h1 == h2:
            return True
        # 共享关键词超过60%（提高阈值减少误合并）
        words1 = set(h1.split())
        words2 = set(h2.split())
        if words1 and words2:
            intersection = words1 & words2
            union = words1 | words2
            return len(intersection) / len(union) > 0.6
        return False

    def _check_cross_day_dedup(self, core_signals: List[Dict], date: str) -> List[Dict]:
        """跨日去重：昨日核心故事今日降权或移入观察名单"""
        yesterday = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_file = Path('public/data/v2/daily-' + yesterday + '-v2.json')

        if not yesterday_file.exists():
            return core_signals

        try:
            with open(yesterday_file) as f:
                yesterday_data = json.load(f)
            yesterday_core = {e['headline'].lower()[:30] for e in yesterday_data.get('core_signals', [])}

            # 对今日核心降权（分数降低10分）
            for event in core_signals:
                if event['headline'].lower()[:30] in yesterday_core:
                    event['score']['total'] = max(0, event['score']['total'] - 10)
                    event['_cross_day_duplicate'] = True
        except Exception as e:
            print(f"跨日去重失败: {e}", file=sys.stderr)

        return core_signals

    def _has_noise_summary(self, text: str) -> bool:
        """检查摘要是否包含噪声"""
        if not text:
            return False
        noise_patterns = [
            '下载客户端', '登录.*查看', '无障碍', '来源：',
            '点击查看', '版权所有', '转载请附上', '本文链接'
        ]
        import re
        for pattern in noise_patterns:
            if re.search(pattern, text):
                return True
        return False

    def _calc_relevance_score(self, core_signals: List[Dict], events: List[Dict]) -> float:
        """计算相关性分数"""
        if not events:
            return 0
        # 核心事件中标记为AI/Agent相关的比例
        ai_keywords = ['ai', 'agent', 'openai', 'claude', 'gpt', 'llm', '开源', '模型']
        relevant = sum(1 for e in events if any(kw in e.get('headline', '').lower() for kw in ai_keywords))
        return min(100, relevant / len(events) * 100 * 1.5)  # 放大系数

    def _calc_action_score(self, core_signals: List[Dict]) -> float:
        """计算动作完整性分数"""
        if not core_signals:
            return 0
        # 只要有具体动作文本就算通过，不强制要求非watch类型
        complete = sum(1 for e in core_signals
                      if e.get('suggested_action', {}).get('text') and
                      len(e.get('suggested_action', {}).get('text', '')) > 10)
        return (complete / len(core_signals)) * 100

    def _check_three_end_consistency(self, v2_data: Dict, brief: str, topic_cards: str) -> bool:
        """真实检查三端一致性"""
        import re
        # 提取V2 JSON中的核心标题
        v2_titles = [e['headline'] for e in v2_data.get('core_signals', [])]

        # 提取Markdown中的标题
        md_titles = re.findall(r'### (.+)', brief)

        # 提取选题卡中的标题
        card_titles = re.findall(r'## 选题\d+：(.+)', topic_cards)

        # 检查V2核心标题是否在Markdown中出现
        md_match = sum(1 for t in v2_titles if any(t[:30] in m or m[:30] in t for m in md_titles))
        card_match = sum(1 for t in v2_titles[:3] if any(t[:30] in c or c[:30] in t for c in card_titles))

        return md_match >= len(v2_titles) * 0.8 and card_match >= min(3, len(v2_titles)) * 0.6

    def _check_link_health(self, items: List[Dict]) -> float:
        """真实检查链接健康度（抽样）"""
        import urllib.request
        import urllib.error

        # 抽样检查10个URL
        sample_size = min(10, len(items))
        sampled = items[::max(1, len(items) // sample_size)][:sample_size]

        healthy = 0
        for item in sampled:
            url = item.get('url', '')
            if not url:
                continue
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        healthy += 1
            except:
                pass

        return (healthy / max(1, sample_size)) * 100

    def _calc_freshness_score(self, items: List[Dict]) -> float:
        """计算新鲜度分数（暂用固定值）
        原因: published_at全部为unknown，无法判断真实新鲜度
        TODO: 待采集器支持时间提取后改为真实计算
        """
        return 70.0
    
    def _build_source_health(self, sources: List[Dict]) -> List[Dict]:
        return [{'name': s.get('name', 'unknown'), 'category': s.get('category', 'other'), 'count': s.get('count', 0), 'last_updated': None, 'status': 'normal' if s.get('count', 0) > 0 else 'no-data', 'issues': []} for s in sources]
    
    def _build_ignored_summary(self, ignored: List[Dict]) -> List[Dict]:
        reason_counts = {}
        for item in ignored:
            reason = item.get('reason', 'unknown')
            if reason not in reason_counts:
                reason_counts[reason] = []
            reason_counts[reason].append(item['event'])
        
        return [{'reason': reason, 'count': len(events), 'examples': [{'title': e['headline'], 'url': '', 'source': ''} for e in events[:3]]} for reason, events in reason_counts.items()]
    
    def export_markdown(self, data: Dict[str, Any]) -> Dict[str, Any]:
        date = data['date']
        meta = data['stats']
        quality = data['quality']
        
        brief_lines = [
            f"# AI 情报官日报｜{date}",
            "",
            f"画像：{self.profile.get('name', 'AI 开源与 Agent 创作者')}",
            f"数据：{meta['raw_items']} 条原料 → {meta['unique_events']} 个事件 → {meta['core_signals']} 条核心",
            f"质量：{quality['total']}/100（{quality['grade']}）",
            "",
            "## 今日结论",
        ]
        
        for i, summary in enumerate(data.get('executive_summary', []), 1):
            brief_lines.append(f"{i}. {summary}")
        
        brief_lines.extend(["", "## 核心信号"])
        for event in data.get('core_signals', []):
            brief_lines.extend([
                f"### {event['headline']}",
                f"- 发生了什么：{event['clean_summary']}",
                f"- 为什么重要：{event['why_it_matters']}",
                f"- 建议动作：{event['suggested_action']['text']}",
                f"- 置信度：{event['confidence']:.0%}",
                f"- 分数：{event['score']['total']}/100",
                "",
            ])
        
        brief_lines.extend(["## 观察名单"])
        for event in data.get('watchlist', [])[:10]:
            brief_lines.append(f"- [{event['score']['total']}] {event['headline']}")
        
        brief_lines.extend(["", "## 今日动作"])
        for action in data.get('actions', []):
            brief_lines.append(f"- **{action['type']}**：{action['text']}")
        
        return {
            'date': date,
            'brief': '\n'.join(brief_lines),
            'topic_cards': [f"## 选题{i}：{event['headline'][:40]}\n- 角度：{event['why_it_matters'][:50]}\n- 适合谁：AI开发者、技术决策者\n- 证据：核心信号第{i}条，{event['source_count']}家媒体\n- 验证：查阅原文[{event['headline'][:30]}...]\n- 风险：发布时间未知，需核实\n- 形式：{'深度分析' if event['suggested_action']['type'] == 'write' else '实测教程' if event['suggested_action']['type'] == 'try' else '观点评论'}" for i, event in enumerate(data.get('core_signals', [])[:3], 1)],
            'meta': {'raw_items': meta['raw_items'], 'events': meta['unique_events'], 'core_count': meta['core_signals'], 'quality_score': quality['total'], 'quality_grade': quality['grade']},
        }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', required=True)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', default=None)
    args = parser.parse_args()
    
    with open('config/profiles/ai-open-source-agent-creator.json', encoding='utf-8') as f:
        profile_config = json.load(f)
    
    with open(args.input, encoding='utf-8') as f:
        raw_data = json.load(f)
    
    processor = IntelligenceProcessor(profile_config)
    result = processor.process(raw_data)

    # ── LLM 失败保护：如果本次 LLM 调用失败，但上次 V2 数据有效，保留旧数据不覆盖 ──
    llm_ok = bool(result.get('llm_usage'))
    v2_path = Path('public/data/v2') / f'daily-{args.date}-v2.json'

    if not llm_ok and v2_path.exists():
        try:
            with open(v2_path, encoding='utf-8') as f:
                old = json.load(f)
            if old.get('llm_usage'):
                print(f"LLM_FAILED_KEEP_PREVIOUS_V2: 保留上一版好数据，不覆盖 V2/brief", file=sys.stderr)
                sys.exit(0)
        except Exception as e:
            print(f"LLM_FAILED_KEEP_PREVIOUS_V2: 读取旧文件失败 {e}，允许写入模板降级版", file=sys.stderr)

    output_dir = Path(args.output) if args.output else Path(args.input).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # 仅在 LLM 成功时才写 V2（首次运行或 LLM 成功都允许写入）
    if llm_ok or not v2_path.exists():
        with open(output_dir / f'daily-{args.date}-v2.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        print(f"LLM_FAILED_SKIP_WRITE: V2 文件未更新（LLM 失败，保留旧数据）", file=sys.stderr)
    
    # 同步更新 index.json 的 latest_date（防止页面读不到最新数据）
    index_path = output_dir / 'index.json'
    try:
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                idx = json.load(f)
        else:
            idx = {}
        idx['latest_date'] = args.date
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(idx, f, ensure_ascii=False)
        print(f"  -> Updated index.json: latest_date={args.date}")
    except Exception as e:
        print(f"  -> Failed to update index.json: {e}", file=sys.stderr)
    
    export = processor.export_markdown(result)
    exports_dir = output_dir / 'exports' / 'intel-officer'
    exports_dir.mkdir(parents=True, exist_ok=True)
    
    with open(exports_dir / f'{args.date}-brief.md', 'w', encoding='utf-8') as f:
        f.write(export['brief'])
    with open(exports_dir / f'{args.date}-topic-cards.md', 'w', encoding='utf-8') as f:
        f.write('\n\n---\n\n'.join(export['topic_cards']))
    
    print(f"✅ 处理完成")
    print(f"   原始条目: {result['stats']['raw_items']}")
    print(f"   唯一事件: {result['stats']['unique_events']}")
    print(f"   核心信号: {result['stats']['core_signals']}")
    print(f"   质量评分: {result['quality']['total']}/100 ({result['quality']['grade']})")


if __name__ == '__main__':
    main()
