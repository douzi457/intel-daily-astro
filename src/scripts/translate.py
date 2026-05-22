"""
翻译模块 - translate.py
利用 MiniMax API 将国外平台内容翻译为中文
"""
import os, sys, json, time, re

# MiniMax API Key（需要设置环境变量 MINIMAX_API_KEY）
API_KEY = os.environ.get('MINIMAX_API_KEY', '')
API_URL = 'https://api.minimax.chat/v1/text/chatcompletion_v2'

# 需要翻译的来源
TRANSLATABLE_SOURCES = {'reddit', 'hackernews', 'github', 'producthunt'}


def translate_text(text, max_chars=500, retry=2):
    """将英文文本翻译为中文（MiniMax API）"""
    if not text or not text.strip():
        return text
    if not API_KEY:
        return None  # 无 Key，不翻译

    text = text.strip()[:max_chars]
    prompt = (
        f"Translate the following text to Chinese. "
        f"Keep the tone natural and concise. Only output the translation, no explanations.\n\n"
        f"Text: {text}"
    )

    for attempt in range(retry):
        try:
            import urllib.request
            req = urllib.request.Request(
                API_URL,
                data=json.dumps({
                    'model': 'MiniMax-Text-01',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 300,
                    'temperature': 0.3,
                }).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {API_KEY}',
                    'Content-Type': 'application/json',
                },
                method='POST'
            )
            r = urllib.request.urlopen(req, timeout=30)
            resp = json.load(r)
            return resp['choices'][0]['message']['content'].strip()
        except Exception as e:
            if attempt < retry - 1:
                time.sleep(2)
    return None


def _is_foreign(original_source, source_type):
    """判断是否为国外平台（支持 reddit/xxx 格式）"""
    if not original_source:
        return source_type in TRANSLATABLE_SOURCES
    os = original_source.lower()
    for src in TRANSLATABLE_SOURCES:
        if os == src or os.startswith(src + '/'):
            return True
    return False


def batch_translate(items, label='title', batch_size=10):
    """
    批量翻译 items 中的指定字段
    items: [{id, title, desc, ...}, ...]
    label: 要翻译的字段名，默认翻译 title
    返回: {id: translated_text, ...}
    """
    if not API_KEY:
        return {}

    # 过滤出需要翻译且有内容的条目
    to_translate = [
        (it['id'], it.get(label, ''))
        for it in items
        if _is_foreign(it.get('original_source',''), it.get('source_type',''))
        and it.get(label, '').strip()
        and len(it.get(label, '')) > 5  # 太短的跳过
    ]

    if not to_translate:
        return {}

    print(f"  [翻译] 需翻译 {len(to_translate)} 条 {label}...")
    results = {}

    # 分批处理，每批10条
    for i in range(0, len(to_translate), batch_size):
        batch = to_translate[i:i+batch_size]
        # 合并为一个 prompt
        lines = []
        for idx, (item_id, text) in enumerate(batch):
            lines.append(f"[{idx}] {text}")
        combined_prompt = (
            "Translate each item to Chinese. Keep tone natural.\n"
            "Output format: one line per item, start with [index]: \n\n"
            + "\n".join(lines)
        )

        try:
            import urllib.request
            req = urllib.request.Request(
                API_URL,
                data=json.dumps({
                    'model': 'MiniMax-Text-01',
                    'messages': [{'role': 'user', 'content': combined_prompt}],
                    'max_tokens': 800,
                    'temperature': 0.3,
                }).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {API_KEY}',
                    'Content-Type': 'application/json',
                },
                method='POST'
            )
            r = urllib.request.urlopen(req, timeout=60)
            resp = json.load(r)
            translations = resp['choices'][0]['message']['content'].strip().split('\n')

            for idx, line in enumerate(translations):
                if idx < len(batch):
                    item_id = batch[idx][0]
                    # 去掉 [index]: 前缀
                    clean = re.sub(r'^\[\d+\]\s*', '', line).strip()
                    results[item_id] = clean

            print(f"    批次 {i//batch_size + 1}: 翻译了 {len(translations)} 条")
            time.sleep(1)  # 避免限流

        except Exception as e:
            print(f"    批次 {i//batch_size + 1} 失败: {e}")

    return results


def patch_items_with_translations(items):
    """
    给 items 列表中的国外平台内容翻译 title 和 desc
    在原字段上增加 zh_title 和 zh_desc
    """
    if not API_KEY:
        print("  [翻译] 未设置 MINIMAX_API_KEY，跳过翻译")
        return items

    # 先翻译 title
    title_map = batch_translate(items, label='title')
    # 再翻译 desc
    desc_map = batch_translate(items, label='desc')

    for it in items:
        it_id = it.get('id')
        if it_id in title_map:
            it['zh_title'] = title_map[it_id]
        if it_id in desc_map:
            it['zh_desc'] = desc_map[it_id]

    return items


if __name__ == '__main__':
    # 简单测试
    test = [
        {'id': 1, 'original_source': 'reddit', 'title': 'OpenAI releases GPT-5 with revolutionary reasoning capabilities', 'desc': 'The new model shows unprecedented performance on mathematical benchmarks.'},
        {'id': 2, 'original_source': 'github', 'title': 'microsoft/TypeScript', 'desc': 'TypeScript is a superset of JavaScript.'},
        {'id': 3, 'original_source': '36kr', 'title': '某公司发布新产品', 'desc': '这是一个中文描述'},
    ]
    patched = patch_items_with_translations(test)
    for it in patched:
        print(f"  {it['original_source']}: {it.get('zh_title', it['title'])}")
