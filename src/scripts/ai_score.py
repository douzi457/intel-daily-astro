"""
AI 评分 + 摘要模块 - ai_score.py
先实现规则评分（无 API 依赖），后续可切换到 AI 评分
"""
import os, sys, time, re

# ============== 规则评分系统 ==============
"""
规则评分逻辑：
- 来源权重 × 内容长度权重 × 关键词加成 = 最终分
- 0-10 分，8分以上是好内容
"""
import re

# 来源权重配置（哪些来源的内容本身就质量高）
SOURCE_WEIGHT = {
    'gzh': 10,           # 公众号 - 最高权重
    '36kr': 8,           # 36Kr - 商业科技
    'wallstreetcn': 9,   # 华尔街见闻 - 金融
    'v2ex': 7,           # V2EX - 程序员社区
    'sspai': 8,          # 少数派 - 数字生活
    'ithome': 7,         # IT之家 - 科技
    'chuangye': 7,       # 创业邦 - 创业
    'reddit': 7,          # Reddit - 海外社区
    'hackernews': 9,      # HN - 科技前沿
    'github': 8,          # GitHub - 开发
    'producthunt': 8,    # PH - 产品
    'tencent': 6,        # 腾讯新闻 - 综合
    'toutiao': 5,        # 今日头条 - 内容参差
    'weibo': 4,          # 微博 - 娱乐八卦
    'bilibili': 5,       # B站 - 视频社区
    'douyin': 3,         # 抖音 - 视频平台
    'news_': 5,          # 其他聚合
}

# 关键词加分（这些关键词出现=高质量内容）
HIGH_VALUE_KEYWORDS = [
    '免费', '开源', 'GPT', 'Claude', 'AI', 'LLM', 'Copilot',
    'API', 'GitHub', '新功能', '发布', '更新', '版本',
    '赚钱', '副业', '收入', '变现', '流量主',
    '教程', '指南', '攻略', '白嫖', '羊毛',
    '限免', '折扣', '送', '福利',
]

# 关键词扣分（这些关键词=低质量/标题党）
LOW_VALUE_KEYWORDS = [
    '震惊', '必看', '绝了', '笑死', '太牛', '破防',
    '绝了绝了', '太恐怖', '全网', '刷屏', '内幕',
]


def score_by_rule(title, desc, source, hot_value=0, comments=0):
    """
    规则评分，返回 0-10 分数和一句话摘要（如果有）
    """
    # 1. 来源基础分
    source_key = source.split('/')[0].lower() if source else ''
    base_score = SOURCE_WEIGHT.get(source_key, 5)

    # 2. 内容丰富度加成
    content = (title + ' ' + (desc or '')).lower()
    length_bonus = 0
    if len(desc or '') > 100:
        length_bonus = 1
    if len(desc or '') > 300:
        length_bonus = 2

    # 3. 关键词加成
    keyword_bonus = 0
    for kw in HIGH_VALUE_KEYWORDS:
        if kw.lower() in content:
            keyword_bonus += 1

    keyword_penalty = 0
    for kw in LOW_VALUE_KEYWORDS:
        if kw.lower() in content:
            keyword_penalty += 2

    # 4. 热度加成（评论数/star/点赞）
    hot_bonus = 0
    if hot_value and hot_value > 1000:
        hot_bonus = 1
    if hot_value and hot_value > 5000:
        hot_bonus = 2
    if comments and comments > 50:
        hot_bonus = 1
    if comments and comments > 200:
        hot_bonus = 2

    # 5. 计算最终分
    score = base_score + length_bonus + keyword_bonus + hot_bonus - keyword_penalty
    score = max(0, min(10, score))  # 限制在 0-10

    # 6. 生成一句话摘要（从标题+描述中提取）
    summary = generate_summary(title, desc)

    return score, summary


def generate_summary(title, desc):
    """
    从标题和描述生成一句话摘要
    策略：标题本身就够简洁了，直接用标题的关键词
    """
    if not desc or len(desc.strip()) < 10:
        # 没有描述，从标题提取关键词
        words = re.findall(r'[\w]{2,}', title)
        # 过滤停用词
        stopwords = {'一个', '这个', '那个', '什么', '怎么', '如何', '为什么', '可以', '不是', '就是', '但是', '而且', '所以', '因为', '如果', '虽然', '自己', '已经', '现在', '开始', '之后', '之前', '以后', '以前', '时候', '里面', '外面', '上面', '下面', '里面', '这些', '那些', '所有', '一些', '还有', '没有', '还有', '就是', '不能', '不会', '不要', '不用', '必须', '应该', '能够'}
        key_words = [w for w in words if w not in stopwords and len(w) > 2]
        if key_words:
            return ' '.join(key_words[:5])
        return title[:30]

    # 有描述，提取第一句或关键信息
    first_sent = desc.split('。')[0].split('\n')[0].strip()
    if len(first_sent) > 50:
        first_sent = first_sent[:50] + '...'
    if not first_sent:
        return title[:30]
    return first_sent


# ============== AI 评分（需要 API key） ==============
"""
要启用 AI 评分，需要：
1. 获取 MiniMax API key（https://platform.minimax.chat/）
2. 设置环境变量: set MINIMAX_API_KEY=你的key
3. 调用时用 batch_score_ai() 而不是 score_by_rule()
"""

MINIMAX_API_KEY = os.environ.get('MINIMAX_API_KEY', '')


def call_minimax_api(prompt, max_tokens=200):
    """调用 MiniMax API"""
    if not MINIMAX_API_KEY:
        return None

    import urllib.request, json
    url = 'https://api.minimax.chat/v1/text/chatcompletion_v2'
    headers = {
        'Authorization': f'Bearer {MINIMAX_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': 'MiniMax-Text-01',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': max_tokens,
        'temperature': 0.3,
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'),
                                     headers=headers, method='POST')
        r = urllib.request.urlopen(req, timeout=60)
        resp = json.load(r)
        return resp['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'  MiniMax API 错误: {e}')
        return None


def batch_score_ai(items):
    """
    批量 AI 评分（需要 API key）
    items: [{title, desc, source, url, id}, ...]
    返回: {id: (score, summary), ...}
    """
    if not items or not MINIMAX_API_KEY:
        return {}

    # 构造 prompt
    items_text = '\n'.join([
        f"{i+1}. [{it['source']}] {it['title'][:60]} | {((it.get('desc') or '')[:60])}"
        for i, it in enumerate(items)
    ])

    prompt = f"""你是一个资讯筛选专家。请为以下新闻评分(0-10)并生成一句话摘要：

{items_text}

输出JSON格式（只用数字序号作key）：
{{"1": {{"score": 8, "summary": "..."}}, "2": {{"score": 5, "summary": "..."}}, ...}}

评分：10=全网刷屏，8=重大新闻，6=有意思，4=一般，2=低价值，0=垃圾。只输出JSON。
"""
    result = call_minimax_api(prompt, max_tokens=500)
    if not result:
        return {}

    try:
        import json as _json
        match = re.search(r'\{.*\}', result, re.DOTALL)
        if match:
            data = _json.loads(match.group())
            ret = {}
            for i, it in enumerate(items):
                key = str(i + 1)
                if key in data and isinstance(data[key], dict):
                    ret[it['id']] = (
                        int(data[key].get('score', 5)),
                        data[key].get('summary', '')[:50]
                    )
            return ret
    except Exception as e:
        print(f'  解析AI响应错误: {e}')

    return {}


# ============== 主函数 ==============
def score_all(date_key=None, use_ai=False):
    """
    给数据库中所有条目评分
    date_key: None=所有日期
    use_ai: True=用AI评分（需API key），False=规则评分
    """
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from db.db import get_conn

    conn = get_conn()

    # 统计已评分条数
    already_scored = conn.execute("SELECT COUNT(*) FROM items WHERE score > 0").fetchone()[0]
    print(f'已有评分: {already_scored}条')

    # 读取未评分条目
    if date_key:
        rows = conn.execute(
            "SELECT id, title, description, original_source, hot_value, comments FROM items WHERE date_key=? AND (score=0 OR score IS NULL)",
            (date_key,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, title, description, original_source, hot_value, comments FROM items WHERE score=0 OR score IS NULL"
        ).fetchall()

    total = len(rows)
    mode = 'AI' if use_ai else '规则'
    print(f'待评分: {total}条  ({mode}评分模式)')

    updated = 0
    for r in rows:
        title = r['title'] or ''
        desc = r['description'] or ''
        source = r['original_source'] or ''
        hot = r['hot_value'] or 0
        comments = r['comments'] or 0

        if use_ai:
            # TODO: 批量AI评分
            score, summary = None, None
        else:
            score, summary = score_by_rule(title, desc, source, hot, comments)

        if score is not None:
            conn.execute(
                "UPDATE items SET score=?, ai_summary=? WHERE id=?",
                (score, summary or '', r['id'])
            )
            updated += 1

        if updated % 50 == 0:
            print(f'  已处理 {updated}/{total} ...')

    conn.commit()
    print(f'=== 评分完成: 更新 {updated} 条 ===')
    return updated


if __name__ == '__main__':
    date_key = sys.argv[1] if len(sys.argv) > 1 else None
    use_ai = '--ai' in sys.argv
    score_all(date_key=date_key, use_ai=use_ai)
