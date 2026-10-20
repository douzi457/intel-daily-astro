"""
单元测试：scripts/new_terms.py 的核心逻辑
"""

import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from new_terms import (
    extract_latin_phrases,
    extract_zh_bracketed,
    extract_github_repo,
    compute_new_terms,
    load_daily_data,
)


def test_extract_latin_phrases():
    """测试拉丁词组提取"""
    # 驼峰命名应保留
    assert 'deepseek' in extract_latin_phrases('DeepSeek releases V4.1')
    assert 'torchneuron' in extract_latin_phrases('AWS TorchNeuron announcement')
    assert 'minimax' in extract_latin_phrases('MiniMax M3.1 Flash')

    # 停用词应过滤
    assert 'without' not in extract_latin_phrases('without buying its label')
    assert 'faster' not in extract_latin_phrases('answers questions faster')
    assert 'models' not in extract_latin_phrases('AI models are changing')
    assert 'agents' not in extract_latin_phrases('AI agents adoption')

    # 普通名词应过滤
    assert 'folder' not in extract_latin_phrases('folder called Saudi Gov Docs')
    assert 'soldier' not in extract_latin_phrases('drone evacuation of wounded soldier')

    # 版本号应保留
    assert 'v4' in extract_latin_phrases('DeepSeek-V4.1-Flash')
    assert 'm3' in extract_latin_phrases('MiniMax M3.1')


def test_extract_zh_bracketed():
    """测试中文括号词提取"""
    # 书名号
    assert '厨菜记' in extract_zh_bracketed('小程序「厨菜记」上线满月')
    assert 'GTA6' in extract_zh_bracketed('《GTA6》全新宣传片发布')

    # 引号
    assert '家' in extract_zh_bracketed('苹果为"家"开场')
    assert '语音+屏幕' in extract_zh_bracketed('绕不开"语音+屏幕"')

    # 停用词应过滤
    assert '发布' not in extract_zh_bracketed('《发布》新品')
    assert '最新' not in extract_zh_bracketed('《最新》资讯')


def test_extract_github_repo():
    """测试GitHub仓库名提取"""
    assert extract_github_repo('https://github.com/owner/repo') == 'repo'
    assert extract_github_repo('https://github.com/openai/gpt-4') == 'gpt-4'
    assert extract_github_repo('https://example.com') is None
    assert extract_github_repo('') is None


def test_new_term_detection():
    """测试新词判定逻辑（fixture-based）"""

    # 构造3天数据
    base = Path(tempfile.mkdtemp())
    (base / 'v4').mkdir(parents=True, exist_ok=True)

    # Day 1 (10天前): 词X不出现
    day1 = {
        'date': '2026-10-10',
        'by_category': {
            'Other': [
                {'title': 'Normal news about something', 'title_cn': '普通新闻',
                 'url': 'https://example.com/1', 'score': 7.0,
                 'source': 'Example', 'source_count': 1, 'sources': ['Example']}
            ]
        }
    }

    # Day 2 (9天前): 词X仍然不出现
    day2 = {
        'date': '2026-10-11',
        'by_category': {
            'Other': [
                {'title': 'Another normal news', 'title_cn': '另一条普通新闻',
                 'url': 'https://example.com/2', 'score': 6.0,
                 'source': 'Example', 'source_count': 1, 'sources': ['Example']}
            ]
        }
    }

    # Day 3 (今天): 词X出现3条 → 应该是 [new]
    day3 = {
        'date': '2026-10-20',
        'by_category': {
            'AI Model': [
                {'title': 'TestX launches new feature', 'title_cn': 'TestX发布新功能',
                 'url': 'https://github.com/test/testx', 'score': 9.0,
                 'source': 'TechCrunch', 'source_count': 1, 'sources': ['TechCrunch']},
                {'title': 'TestX benchmark results released', 'title_cn': 'TestX基准测试结果发布',
                 'url': 'https://arxiv.org/testx', 'score': 8.5,
                 'source': 'ArXiv', 'source_count': 1, 'sources': ['ArXiv']},
                {'title': 'TestX open source release', 'title_cn': 'TestX开源发布',
                 'url': 'https://github.com/test/testx/releases', 'score': 8.0,
                 'source': 'GitHub', 'source_count': 1, 'sources': ['GitHub']},
            ]
        }
    }

    # 写入fixture文件
    for day, data in [('2026-10-10', day1), ('2026-10-11', day2), ('2026-10-20', day3)]:
        with open(base / 'v4' / f'daily-{day}.json', 'w') as f:
            json.dump(data, f)

    # 直接传入数据，不通过 load_daily_data
    today_data = day3
    history = [('2026-10-10', day1), ('2026-10-11', day2)]

    # 计算新词
    candidates = compute_new_terms(today_data, history)

    # 验证词X被识别为 [new]
    testx_terms = [c for c in candidates if c['term'] == 'testx']
    assert len(testx_terms) == 1, f"Expected testx to be detected, got: {[c['term'] for c in candidates]}"
    assert testx_terms[0]['status'] == 'new', f"Expected 'new' status, got: {testx_terms[0]['status']}"
    # today_count=5: 3条标题中的"testx" + 2条URL中的repo名（testx出现2次）
    assert testx_terms[0]['today_count'] == 5, f"Expected count=5, got: {testx_terms[0]['today_count']}"
    assert testx_terms[0]['strong'] is True  # repo + score>=8

    # 验证平稳词Y不被选中
    # （构造一个过去3天都出现的词Y，但今天没有暴增）
    day2_with_y = {
        'date': '2026-10-11',
        'by_category': {
            'AI Model': [
                {'title': 'StableY feature update', 'title_cn': 'StableY功能更新',
                 'url': 'https://example.com/y1', 'score': 7.0,
                 'source': 'Example', 'source_count': 1, 'sources': ['Example']},
            ]
        }
    }
    day3_with_y = {
        'date': '2026-10-20',
        'by_category': {
            'AI Model': [
                {'title': 'StableY continues development', 'title_cn': 'StableY持续发展',
                 'url': 'https://example.com/y2', 'score': 7.0,
                 'source': 'Example', 'source_count': 1, 'sources': ['Example']},
            ]
        }
    }

    with open(base / 'v4' / 'daily-2026-10-11.json', 'w') as f:
        json.dump(day2_with_y, f)
    with open(base / 'v4' / 'daily-2026-10-20.json', 'w') as f:
        json.dump(day3_with_y, f)

    history = [('2026-10-10', load_daily_data('2026-10-10')),
               ('2026-10-11', load_daily_data('2026-10-11'))]
    today_data = load_daily_data('2026-10-20')
    candidates = compute_new_terms(today_data, history)

    stabley_terms = [c for c in candidates if 'stabley' in c['term'].lower()]
    assert len(stabley_terms) == 0, f"StableY should NOT be selected (平稳词), got: {stabley_terms}"

    print("✓ test_new_term_detection passed")


def test_rising_detection():
    """测试升温词判定：过去每天出现1次，今天暴增至6次"""
    history = []
    for i in range(1, 6):
        history.append((f'2026-10-{15+i:02d}', {
            'date': f'2026-10-{15+i:02d}',
            'by_category': {'AI': [{'title': 'ZZZ day', 'title_cn': '', 'url': '', 'score': 7.0, 'source': 'Ex', 'source_count': 1, 'sources': ['Ex']}]}})
        )
    today_data = {'date': '2026-10-21', 'by_category': {
        'AI': [
            {'title': 'ZZZ major', 'title_cn': '', 'url': '', 'score': 9.0, 'source': 'TC', 'source_count': 1, 'sources': ['TC']},
            {'title': 'ZZZ benchmark', 'title_cn': '', 'url': '', 'score': 8.5, 'source': 'ArXiv', 'source_count': 1, 'sources': ['ArXiv']},
            {'title': 'ZZZ guide', 'title_cn': '', 'url': '', 'score': 8.0, 'source': 'Medium', 'source_count': 1, 'sources': ['Medium']},
            {'title': 'ZZZ update', 'title_cn': '', 'url': '', 'score': 7.5, 'source': 'Blog', 'source_count': 1, 'sources': ['Blog']},
            {'title': 'ZZZ release', 'title_cn': '', 'url': '', 'score': 7.0, 'source': 'News', 'source_count': 1, 'sources': ['News']},
            {'title': 'ZZZ announcement', 'title_cn': '', 'url': '', 'score': 6.5, 'source': 'PR', 'source_count': 1, 'sources': ['PR']},
        ]
    }}

    candidates = compute_new_terms(today_data, history)
    zzz = [c for c in candidates if c['term'] == 'zzz']

    assert len(zzz) == 1, f"Expected zzz, got: {[c['term'] for c in candidates]}"
    assert zzz[0]['status'] == 'rising', f"Expected 'rising', got: {zzz[0]['status']}"
    assert zzz[0]['today_count'] == 6
    print("✓ test_rising_detection passed")


if __name__ == '__main__':
    test_extract_latin_phrases()
    print("✓ test_extract_latin_phrases passed")

    test_extract_zh_bracketed()
    print("✓ test_extract_zh_bracketed passed")

    test_extract_github_repo()
    print("✓ test_extract_github_repo passed")

    test_new_term_detection()
    test_rising_detection()

    print("\n=== ALL TESTS PASSED ===")
