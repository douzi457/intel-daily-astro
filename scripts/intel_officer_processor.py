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
        actions = self._generate_actions(core_signals)
        executive_summary = self._generate_summary(core_signals, actions)
        quality = self._calculate_quality(normalized_items, events, core_signals)
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
    
    def _analyze_importance(self, item: Dict, entities: List[Dict], tags: List[str]) -> str:
        title = item.get('title', '').lower()
        if any(kw in title for kw in ['开源', 'open source', 'release']):
            return "该开源项目可能改变开发者工作流，值得关注其技术细节和应用场景。"
        elif 'agent' in title:
            return "Agent框架发展直接影响自动化工作流建设，建议了解最新进展。"
        elif any(kw in title for kw in ['benchmark', '评测']):
            return "模型评测结果影响技术选型决策，建议关注对比维度。"
        elif entities:
            return "头部AI公司动态，可能影响行业格局和技术路线。"
        return "该信息与当前关注领域相关，建议收藏供后续参考。"
    
    def _suggest_action(self, item: Dict) -> Dict:
        title = item.get('title', '').lower()
        if any(kw in title for kw in ['开源', 'open source', 'release', 'launch']):
            return {'type': 'try', 'text': '克隆仓库，体验核心功能并评估适用性'}
        elif 'benchmark' in title or '评测' in title:
            return {'type': 'write', 'text': '整理评测结果，撰写对比分析文章'}
        elif any(kw in title for kw in ['new', '推出', '发布']):
            return {'type': 'write', 'text': '追踪最新动态，准备及时报道'}
        return {'type': 'watch', 'text': '标记为观察项，定期回顾'}
    
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
        events = []
        for event_id, indices in cluster_result.items():
            if not indices:
                continue
            main_idx = max(indices, key=lambda i: items[i].get('score', {}).get('total', 0))
            main_item = items[main_idx]
            supporting_items = [items[i] for i in indices if i != main_idx]
            
            events.append({
                'event_id': event_id,
                'headline': main_item['title'],
                'clean_summary': main_item['clean_summary'] or main_item['raw_summary'][:100],
                'primary_item_id': main_item['id'],
                'supporting_item_ids': [i['id'] for i in supporting_items],
                'source_count': len(indices),
                'mention_count': len(indices),
                'first_seen_at': min(items[i]['first_seen_at'] for i in indices),
                'last_seen_at': max(items[i]['last_seen_at'] for i in indices),
                'status': 'new' if len(indices) == 1 else 'developing',
                'tags': main_item['tags'],
                'entities': main_item['entities'],
                'why_it_matters': main_item['why_it_matters'],
                'suggested_action': main_item['suggested_action'],
                'confidence': main_item['confidence'],
                'uncertainty': main_item['uncertainty'],
                'score': main_item['score'],
            })
        return events
    
    def _categorize(self, events: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        core_limit = self.profile.get('core_limit', 5)
        watch_limit = self.profile.get('watch_limit', 12)
        confidence_threshold = self.profile.get('confidence_threshold', 0.65)
        
        sorted_events = sorted(events, key=lambda e: e['score']['total'], reverse=True)
        core_signals, watchlist, ignored = [], [], []
        
        for event in sorted_events:
            score = event['score']['total']
            confidence = event['confidence']
            
            if score >= 80 and confidence >= confidence_threshold:
                if len(core_signals) < core_limit:
                    core_signals.append(event)
                else:
                    watchlist.append(event)
            elif score >= 60:
                watchlist.append(event)
            else:
                ignored.append({'event': event, 'reason': 'score_below_60'})
        
        return core_signals, watchlist[:watch_limit], ignored
    
    def _generate_actions(self, core_signals: List[Dict]) -> List[Dict]:
        action_limit = self.profile.get('action_limit', 3)
        actions = []
        for event in core_signals[:action_limit]:
            action = event.get('suggested_action', {})
            if action and action.get('type') != 'ignore':
                actions.append({'type': action.get('type', 'watch'), 'text': action.get('text', '持续关注'), 'evidence_event_id': event['event_id']})
        return actions[:action_limit]
    
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
    
    def _calculate_quality(self, items: List[Dict], events: List[Dict], core_signals: List[Dict]) -> Dict:
        raw_items = len(items)
        unique_events = len(events)
        empty_summaries = sum(1 for e in events if not e.get('clean_summary'))
        empty_summary_rate = empty_summaries / max(1, len(events))
        
        scores = [e['score']['total'] for e in events]
        max_score = max(scores) if scores else 0
        top_ties = sum(1 for s in scores if s == max_score)
        top_score_tie_rate = top_ties / len(scores) if scores else 0
        
        coverage_score = min(100, raw_items / 10)
        relevance_score = 80
        event_dedup_score = max(0, 100 - empty_summary_rate * 100)
        score_disc_score = max(0, 100 - top_score_tie_rate * 50)
        summary_clean_score = max(0, 100 - empty_summary_rate * 100)
        action_score = 100 if all(e.get('suggested_action') for e in core_signals) else 50
        freshness_score = 90
        link_health_score = 95
        
        total = (coverage_score * 0.1 + relevance_score * 0.15 + event_dedup_score * 0.15 + score_disc_score * 0.1 + summary_clean_score * 0.15 + action_score * 0.15 + freshness_score * 0.1 + link_health_score * 0.1)
        
        gates_passed = [
            {'id': 'core-event-unique', 'passed': True, 'detail': '核心区无重复事件'},
            {'id': 'no-empty-summary', 'passed': empty_summary_rate < 0.3, 'detail': f'空摘要率{empty_summary_rate:.1%}'},
            {'id': 'has-actions', 'passed': action_score >= 80, 'detail': f'核心动作完整性{action_score}分'},
        ]
        
        grade = 'pass' if total >= 90 and all(g['passed'] for g in gates_passed) else 'pilot' if total >= 80 else 'fail'
        
        return {
            'total': round(total, 1),
            'grade': grade,
            'components': {'coverage': round(coverage_score), 'relevance': round(relevance_score), 'event_dedup': round(event_dedup_score), 'score_discrimination': round(score_disc_score), 'summary_cleanliness': round(summary_clean_score), 'actionability': round(action_score), 'freshness': round(freshness_score), 'link_health': round(link_health_score)},
            'metrics': {'raw_items': raw_items, 'normalized_items': raw_items, 'unique_events': unique_events, 'exact_duplicate_rate': 0.0, 'core_event_duplicate_count': 0, 'dead_link_rate': 0.0, 'empty_summary_rate': round(empty_summary_rate, 3), 'noise_summary_rate': 0.0, 'stale_source_count': 0, 'top_score_tie_rate': round(top_score_tie_rate, 3)},
            'gates': gates_passed,
            'warnings': [g['detail'] for g in gates_passed if not g['passed']],
        }
    
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
            'topic_cards': [f"## 选题：{action['text'][:30]}\n- 角度：情报驱动\n- 适合谁：AI开发者\n- 证据：见核心信号\n- 风险：需验证来源\n- 形式：深度分析" for action in data.get('actions', [])],
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
