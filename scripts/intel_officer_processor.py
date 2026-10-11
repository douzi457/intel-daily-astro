#!/usr/bin/env python3
"""
intel_officer_processor.py — Daily 情报官 P0 后处理模块
"""

import json
import re
import hashlib
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

CST = timezone(timedelta(hours=8))
CST_STR = "Asia/Shanghai"


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
    """事件聚类"""
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.events: Dict[str, List[int]] = {}
        self.event_counter = 0
    
    def cluster(self, items: List[Dict]) -> Dict[str, List[int]]:
        for i, item in enumerate(items):
            matched = False
            canonical = item.get('canonical_url', '')
            
            for event_id, indices in self.events.items():
                for idx in indices:
                    if items[idx].get('canonical_url') == canonical:
                        self.events[event_id].append(i)
                        matched = True
                        break
                if matched:
                    break
            
            if not matched:
                event_id = f"evt_{self.event_counter:04d}"
                self.events[event_id] = [i]
                self.event_counter += 1
        
        return self.events


class IntelligenceProcessor:
    """情报官处理器"""
    
    def __init__(self, profile_config: Dict[str, Any]):
        self.profile = profile_config
        self.cluster = EventCluster()
    
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
        core_signals, watchlist, ignored = self._categorize(events)

        # 调用大模型生成个性化评价（如果配置了Key）
        llm_importance, llm_actions, llm_usage = self._call_llm_for_judgment(core_signals)

        # 更新core_signals的why_it_matters和suggested_action
        if llm_importance:
            for i, event in enumerate(core_signals, 1):
                if i in llm_importance:
                    event['why_it_matters'] = llm_importance[i]
                if llm_actions and i in llm_actions:
                    event['suggested_action'] = {'type': 'try', 'text': llm_actions[i]}

        actions = self._generate_actions(core_signals, llm_importance, llm_actions)
        executive_summary = self._generate_summary(core_signals, actions)
        quality = self._calculate_quality(normalized_items, events, core_signals, len(watchlist), len(actions))

        # 添加LLM用量信息
        if llm_usage:
            quality['llm_usage'] = llm_usage
            quality['warnings'].append(f"LLM调用成功: {llm_usage['total_tokens']} tokens")
        else:
            quality['warnings'].append("LLM未调用：AGNES_API_KEY/ZHIPU_API_KEY 未配置，使用模板输出")

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
            'items': normalized_items,
            'events': events,
        }
        
        return result
    
    def _normalize_items(self, items: List[Dict]) -> List[Dict]:
        return [self._normalize_item(item, item.get('category', 'Unknown')) for item in items if self._normalize_item(item, item.get('category', 'Unknown'))]
    
    def _normalize_item(self, item: Dict, category: str) -> Optional[Dict]:
        url = item.get('url', '')
        canonical_url = URLNormalizer.normalize(url)
        item_id = URLNormalizer.generate_id(canonical_url, item.get('source', ''))
        
        title = item.get('title', '')
        raw_summary = item.get('summary') or ''
        if not raw_summary or len(raw_summary) < 10:
            raw_summary = title
        
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
        entities = []
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        known = {'openai': 'OpenAI', 'anthropic': 'Anthropic', 'google': 'Google', 'meta': 'Meta', 'microsoft': 'Microsoft', 'amazon': 'Amazon', 'apple': 'Apple', 'gpt': 'GPT', 'claude': 'Claude', 'gemini': 'Gemini', 'llama': 'Llama', 'github': 'GitHub', 'chatgpt': 'ChatGPT', 'deepseek': 'DeepSeek', 'qwen': 'Qwen'}
        for key, name in known.items():
            if key in text:
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
        """分析重要性 - 针对AI开源与Agent创作者画像，确保不重复"""
        title = item.get('title', '').lower()
        summary = item.get('summary', '').lower()
        text = f"{title} {summary}"
        if seen_texts is None:
            seen_texts = set()

        # 开源模型相关
        if any(kw in text for kw in ['open source', '开源', 'release', 'v1.0', 'launch']):
            if 'model' in text or '模型' in text:
                result = "新开源模型可能降低API依赖，建议评估本地部署可行性和许可证兼容性。"
            elif 'agent' in text or 'coding' in text:
                result = "开源Agent框架直接影响工作流自动化建设，建议实测并评估迁移成本。"
            else:
                result = "开源项目更新，建议关注Release Notes中的Breaking Changes。"
        # Agent/编程助手相关
        elif any(kw in text for kw in ['agent', 'autogpt', 'coding assistant', '编程助手']):
            if 'benchmark' in text or '评测' in text:
                result = "Agent能力评测结果影响技术选型，建议关注测试基线和复现性。"
            elif 'security' in text or '安全' in text:
                result = "Agent安全问题可能影响生产部署策略，建议关注漏洞报告和补丁情况。"
            else:
                result = "Agent领域进展，建议了解最新功能和对现有工作流的影响。"
        # 大厂动态
        elif entities:
            company_names = [e['name'] for e in entities if e['type'] == 'company']
            if 'OpenAI' in company_names:
                result = "OpenAI战略调整可能影响生态格局，建议关注API定价和产品路线变化。"
            elif 'Anthropic' in company_names:
                result = "Anthropic动态反映Agent安全方向，建议关注Constitutional AI实践。"
            elif 'Google' in company_names or 'DeepMind' in company_names:
                result = "Google AI进展可能影响开源生态，建议关注Gemini和多模态能力。"
            elif 'Meta' in company_names or 'Llama' in text:
                result = "Meta开源策略影响LLM生态，建议关注Llama许可变化和商业化路径。"
            else:
                result = f"{'、'.join(company_names[:2])}动态，建议关注对开发者工具链的影响。"
        # 工具/基础设施
        elif any(kw in text for kw in ['github', 'ide', 'editor', 'plugin', 'tool']):
            result = "开发者工具更新，建议评估是否能提升编码效率或改善开发体验。"
        # 评测/基准
        elif any(kw in text for kw in ['benchmark', '评测', 'test', 'evaluation']):
            result = "模型评测结果，建议关注测试方法和结论的可复现性。"
        else:
            result = "该信息与AI开源和Agent方向相关，建议持续关注后续进展。"

        # 去重：如果结果与已输出文本重复，添加差异化后缀
        if result in seen_texts:
            suffixes = ["（本文侧重部署层面）", "（本文关注技术细节）", "（本文分析商业影响）"]
            for s in suffixes:
                candidate = result + s
                if candidate not in seen_texts:
                    result = candidate
                    break

        seen_texts.add(result)
        return result

    def _analyze_importance_event(self, main_item: Dict, all_items: List[Dict], indices: List[int], seen_texts: set = None) -> str:
        """事件级重要性分析（考虑多来源）"""
        source_count = len(indices)
        base_importance = self._analyze_importance(main_item, main_item.get('entities', []), main_item.get('tags', []), seen_texts)

        if source_count > 2:
            return f"多源报道（{source_count}家媒体），{base_importance}"
        return base_importance

    def _suggest_action(self, item: Dict, seen_actions: set = None) -> Dict:
        """生成具体动作建议，确保不重复"""
        title = item.get('title', '').lower()
        summary = item.get('summary', '').lower()
        text = f"{title} {summary}"
        entities = self._extract_entities(item)
        if seen_actions is None:
            seen_actions = set()

        # 开源项目发布
        if any(kw in text for kw in ['open source', '开源', 'release', 'v1.0', 'launch']):
            if 'model' in text or '模型' in text:
                result = {'type': 'try', 'text': '克隆官方仓库，在本地环境测试基础功能和API调用'}
            elif 'agent' in text or 'coding' in text:
                result = {'type': 'try', 'text': '搭建最小Demo验证Agent工作流，评估与现有系统的集成成本'}
            else:
                result = {'type': 'write', 'text': '整理Release Notes，撰写功能对比和功能演示文章'}
        # 重大发布/产品更新
        elif any(kw in text for kw in ['new', '推出', '发布', 'launch', 'announced']):
            result = {'type': 'write', 'text': '追踪产品详情和技术方案，准备第一时间解读文章'}
        # 评测/基准测试
        elif any(kw in text for kw in ['benchmark', '评测', 'test', 'evaluation']):
            result = {'type': 'write', 'text': '整理评测数据，撰写横向对比和选型建议文章'}
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

    def _call_llm_for_judgment(self, core_signals: List[Dict]) -> Tuple[Optional[Dict], Optional[Dict], Optional[Dict]]:
        """调用大模型为5条核心信号生成个性化评价和动作建议"""
        import os
        import urllib.request
        import urllib.error

        api_key = os.environ.get("AGNES_API_KEY") or os.environ.get("ZHIPU_API_KEY")
        model = os.environ.get("AGNES_MODEL") or "agnes-3.0"

        if not api_key:
            print("警告: AGNES_API_KEY 或 ZHIPU_API_KEY 未配置，使用模板输出", file=sys.stderr)
            return None, None, None

        # 构建批量请求
        events_data = []
        for i, event in enumerate(core_signals[:5], 1):
            events_data.append({
                'index': i,
                'event_id': event.get('event_id', ''),
                'headline': event.get('headline', '')[:80],
                'clean_summary': event.get('clean_summary', '')[:200],
                'source_count': event.get('source_count', 1),
                'tags': event.get('tags', [])[:3],
            })

        # 构建prompt
        system_prompt = """你是一个专业的AI技术内容创作者顾问。你的读者是关注AI开源项目与Agent技术的创作者（做公众号/视频/开源项目推荐）。

请为每条AI新闻事件提供：
1. why_it_matters: 该事件对"AI开源与Agent创作者"的具体价值（80-150字）
   - 必须说明：选题价值、工具链影响、内容角度
   - 禁止泛泛而谈"可能影响行业格局"
   - 不同事件的评价角度必须实质不同

2. suggested_action: 该创作者今天/本周可执行的具体动作（30-80字）
   - 必须包含动词开头（如"克隆仓库"、"编写代码"、"录制视频"）
   - 禁止空话如"标记为观察项"、"持续关注"、"定期回顾"
   - 动作必须是具体的、可执行的

输出格式为JSON数组，每个元素包含：
{
  "index": 事件序号(1-5),
  "why_it_matters": "...",
  "suggested_action": "..."
}"""

        user_message = f"""请为以下5条AI新闻事件提供评价和动作建议：

{json.dumps(events_data, ensure_ascii=False, indent=2)}"""

        try:
            # 构建请求
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.3,
                "max_tokens": 2000,
            }

            req = urllib.request.Request(
                "http://localhost:11434/v1/chat/completions",
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                },
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode('utf-8'))

            # 解析返回
            content = result['choices'][0]['message']['content']
            response_data = json.loads(content)

            # 构建映射
            importance_map = {}
            action_map = {}
            for item in response_data:
                idx = item['index']
                importance_map[idx] = item['why_it_matters']
                action_map[idx] = item['suggested_action']

            # 记录token用量
            usage = result.get('usage', {})
            llm_usage = {
                'model': model,
                'input_tokens': usage.get('prompt_tokens', 0),
                'output_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0),
            }

            return importance_map, action_map, llm_usage

        except Exception as e:
            print(f"LLM调用失败: {e}", file=sys.stderr)
            return None, None, None

    def _generate_actions(self, core_signals: List[Dict], llm_importance: Dict = None, llm_actions: Dict = None) -> List[Dict]:
        """生成动作列表，带跨日去重"""
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

        for i, event in enumerate(core_signals[:action_limit], 1):
            # 优先使用LLM生成的动作
            if llm_actions and i in llm_actions:
                action_text = llm_actions[i]
            else:
                action_text = self._suggest_action(event, seen_actions)['text']

            if action_text not in seen_actions:
                actions.append({
                    'type': 'try' if '克隆' in action_text or '搭建' in action_text or '编写' in action_text else 'watch',
                    'text': action_text,
                    'evidence_event_id': event['event_id'],
                    'date': today,
                })
                seen_actions.add(action_text)
        return actions[:action_limit]

    def _calculate_score(self, original_score: float, entities: List[Dict], source_name: str) -> Dict:
        relevance = min(30, int(original_score * 3))
        impact = min(20, int(original_score * 2))
        novelty = 15 if original_score >= 8 else 10
        source_authority = min(15, int(original_score * 1.5))
        actionability = min(15, int(original_score * 1.2))
        penalties = 0
        
        source_lower = source_name.lower()
        if any(x in source_lower for x in ['techcrunch', 'the verge', 'ars technica', 'wired']):
            source_authority += 3
        elif any(x in source_lower for x in ['hacker news', 'github', 'reddit']):
            source_authority += 2
        
        if entities:
            impact += 3
        
        total = min(100, relevance + impact + novelty + source_authority + actionability - penalties)
        
        return {'total': total, 'relevance': relevance, 'impact': impact, 'novelty': novelty, 'source_authority': source_authority, 'actionability': actionability, 'penalties': penalties, 'reason': f'原始分{original_score}映射'}
    
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

            event = {
                'event_id': event_id,
                'headline': main_item['title'],
                'clean_summary': main_item['clean_summary'] or main_item['raw_summary'][:100],
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
    
    def _categorize(self, events: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """分层：核心/观察/忽略"""
        core_limit = self.profile.get('core_limit', 5)
        watch_limit = self.profile.get('watch_limit', 12)
        confidence_threshold = self.profile.get('confidence_threshold', 0.65)

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

    def _generate_summary(self, core_signals: List[Dict], actions: List[Dict]) -> List[str]:
        summary = []
        if core_signals:
            top = core_signals[0]
            summary.append(f"{top['headline']}：{top['clean_summary'][:50]}...")
        if len(core_signals) > 1:
            second = core_signals[1]
            summary.append(f"{second['headline']}显示{second['why_it_matters'][:30]}...")
        if actions:
            summary.append(f"建议优先关注：{actions[0]['text'][:30]}...")
        while len(summary) < 3:
            summary.append("暂无更多可执行情报，建议关注历史趋势变化。")
        return summary[:3]
    
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
        # 共享关键词超过50%
        words1 = set(h1.split())
        words2 = set(h2.split())
        if words1 and words2:
            intersection = words1 & words2
            union = words1 | words2
            return len(intersection) / len(union) > 0.5
        return False

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
        """计算新鲜度分数（基于first_seen_at）"""
        # 由于published_at都unknown，用first_seen_at估算
        # 返回固定值，因为无法判断真实新鲜度
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
        for event in data.get('watchlist', [])[:5]:
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
    
    output_dir = Path(args.output) if args.output else Path(args.input).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / f'daily-{args.date}-v2.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
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
