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

def test_parse_llm_json():
    from intel_officer_processor import _parse_llm_json
    print("\n测试LLM JSON容错解析:")
    cases = [
        ("plain array", '[{"index": 1, "card_type": "观点型"}]', True, 'strict'),
        ("json fence", '```json\n[{"index": 1}]\n```', True, 'strict'),
        ("fence no newline", '```[{"index": 1}]```', True, 'strict'),
        ("prose wrapped", '以下是结果：\n```json\n[{"index": 1}]\n```\n希望有帮助', True, 'strict'),
        ("trailing comma", '[{"index": 1,}]', True, 'repaired'),
        ("truncated", '[{"index": 1, "card_type": "观点型"', True, 'repaired'),
        ("no json", '这不是 JSON', False, 'none'),
        ("double comma", '[{"index": 1,, "card_type": "x"}]', False, 'none'),
    ]
    ok = True
    for name, text, want_ok, want_method in cases:
        data, diag = _parse_llm_json(text)
        good = (data is not None) == want_ok and diag['method'] == want_method
        if want_ok:
            good = good and isinstance(data, list) and data[0].get('index') == 1
        print(f"  {'✅' if good else '❌'} {name}: ok={diag['ok']} method={diag['method']}")
        ok = ok and good
    assert ok, "解析用例失败"

def test_judgment_accounting():
    import os
    import urllib.request
    import urllib.error
    from intel_officer_processor import IntelligenceProcessor
    print("\n测试主判断记账与降级（mock urlopen，不发真实请求）:")
    signals = [
        {'event_id': 'e1', 'headline': 'h1', 'clean_summary': 's1', 'url': 'http://x/1', 'source_count': 1, 'tags': []},
        {'event_id': 'e2', 'headline': 'h2', 'clean_summary': 's2', 'url': 'http://x/2', 'source_count': 1, 'tags': []},
    ]
    good_items = [
        {"index": 1, "card_type": "观点型", "event_brief": "b1", "deep_analysis": {}, "action_script": [], "key_quotes": [], "why_it_matters": "w1", "suggested_action": "a1", "category": "AI模型"},
        {"index": 2, "card_type": "资讯型", "event_brief": "b2", "deep_analysis": {}, "action_script": [], "key_quotes": [], "why_it_matters": "w2", "suggested_action": "a2", "category": "开源项目"},
    ]
    class FakeResp:
        def __init__(self, body):
            self.status = 200
            self._body = body.encode('utf-8')
        def read(self):
            return self._body
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
    def body_for(content):
        return json.dumps({"choices": [{"message": {"content": content}}], "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}}, ensure_ascii=False)
    real_urlopen = urllib.request.urlopen
    old_key = os.environ.get("AGNES_API_KEY")
    os.environ["AGNES_API_KEY"] = "test-dummy-key"
    try:
        # 1) 成功：attempts==calls==1
        proc = IntelligenceProcessor({'id': 'test', 'name': 'test'})
        urllib.request.urlopen = lambda req, timeout=60: FakeResp(body_for(json.dumps(good_items, ensure_ascii=False)))
        r = proc._call_llm_for_judgment(signals)
        assert r[3] is None and r[0] and r[0][1] == "w1", f"成功路径异常: {r[3]}"
        assert proc._llm_attempts == 1 and proc._llm_calls_used == 1, f"成功记账异常: attempts={proc._llm_attempts} calls={proc._llm_calls_used}"
        print("  ✅ 成功：attempts==calls==1")
        # 2) 单条坏其余好：降级产出，不报错
        proc2 = IntelligenceProcessor({'id': 'test', 'name': 'test'})
        mixed = [dict(good_items[0]), {"card_type": "资讯型"}]
        urllib.request.urlopen = lambda req, timeout=60: FakeResp(body_for(json.dumps(mixed, ensure_ascii=False)))
        r = proc2._call_llm_for_judgment(signals)
        assert r[3] is None and r[0] and 1 in r[0] and 2 not in r[0], f"降级异常: {r[3]} {r[0]}"
        print("  ✅ 单条坏其余好：降级产出，无报错")
        # 3) 全坏：llm_parse_failed，attempts==parse_failed>=3，calls==0
        proc3 = IntelligenceProcessor({'id': 'test', 'name': 'test'})
        urllib.request.urlopen = lambda req, timeout=60: FakeResp(body_for('[{"index": 1,, "card_type": "x"}]'))
        r = proc3._call_llm_for_judgment(signals)
        assert r[3] and r[3].startswith("llm_parse_failed:"), f"全坏应报 llm_parse_failed，实际: {r[3]}"
        assert proc3._llm_attempts == proc3._llm_parse_failed and proc3._llm_attempts >= 3 and proc3._llm_calls_used == 0, f"全坏记账异常: attempts={proc3._llm_attempts} parse_failed={proc3._llm_parse_failed} calls={proc3._llm_calls_used}"
        print(f"  ✅ 全坏：llm_parse_failed，attempts==parse_failed=={proc3._llm_attempts}，calls==0")
        # 4) HTTP 失败：llm_call_failed（不是 parse）
        proc4 = IntelligenceProcessor({'id': 'test', 'name': 'test'})
        def raise_http(req, timeout=60):
            raise urllib.error.HTTPError(req.full_url, 500, "Internal", {}, None)
        urllib.request.urlopen = raise_http
        r = proc4._call_llm_for_judgment(signals)
        assert r[3] and r[3].startswith("llm_call_failed: HTTP 500"), f"HTTP 失败应报 llm_call_failed，实际: {r[3]}"
        print("  ✅ HTTP 失败：llm_call_failed")
    finally:
        urllib.request.urlopen = real_urlopen
        if old_key is None:
            os.environ.pop("AGNES_API_KEY", None)
        else:
            os.environ["AGNES_API_KEY"] = old_key

if __name__ == '__main__':
    test_url_normalization()
    test_processing()
    test_parse_llm_json()
    test_judgment_accounting()
    print("\n✅ 测试完成")
