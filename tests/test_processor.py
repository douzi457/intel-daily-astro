#!/usr/bin/env python3
"""测试 Daily 情报官处理器"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from intel_officer_processor import IntelligenceProcessor, URLNormalizer, SummaryCleaner

def test_url_normalization():
    test_cases = [
        ("https://example.com/post?utm_source=newsletter", "https://example.com/post"),
        ("https://techcrunch.com/2026/06/10/test/?fbclid=abc123", "https://techcrunch.com/2026/06/10/test"),
    ]
    print("测试URL标准化:")
    for url, expected in test_cases:
        result = URLNormalizer.normalize(url)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {url[:50]}...")

def test_processing():
    print("\n测试完整处理流程:")
    with open('public/data/daily-2026-10-11.json') as f:
        data = json.load(f)
    
    processor = IntelligenceProcessor({
        'id': 'ai-open-source-agent-creator',
        'name': 'AI 开源与 Agent 创作者',
        'include_keywords': ['AI', '开源', 'Agent'],
        'core_limit': 5,
        'watch_limit': 12,
        'action_limit': 3,
        'confidence_threshold': 0.65,
    })
    
    result = processor.process(data)
    print(f"  原始条目: {result['stats']['raw_items']}")
    print(f"  唯一事件: {result['stats']['unique_events']}")
    print(f"  核心信号: {result['stats']['core_signals']}")
    print(f"  观察名单: {result['stats']['watchlist']}")
    print(f"  质量评分: {result['quality']['total']}/100 ({result['quality']['grade']})")
    
    gates_passed = sum(1 for g in result['quality']['gates'] if g['passed'])
    print(f"  硬门槛通过: {gates_passed}/{len(result['quality']['gates'])}")

if __name__ == '__main__':
    test_url_normalization()
    test_processing()
    print("\n✅ 测试完成")
