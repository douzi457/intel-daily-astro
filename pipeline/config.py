# config.py — 全局配置和常量
import os
from pathlib import Path

# ── 路径 ──
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
OUT_BASE = PROJECT_ROOT / "src" / "data" / "rewrite"
LOG_DIR = OUT_BASE / "logs"

# ── API Keys ──
API_KEY = os.environ.get("ZHIPU_API_KEY")
BAIDU_APP_ID = os.environ.get("BAIDU_TRANSLATE_APP_ID", "")
BAIDU_SECRET_KEY = os.environ.get("BAIDU_TRANSLATE_SECRET_KEY", "")
DAILY_TRANSLATE_LIMIT = 30000

# ── HTTP ──
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ── 平台元数据 ──
PLATFORM_META = {
    "36kr":         {"label": "36Kr",       "color": "#4A90E2", "icon": "📊"},
    "wallstreetcn": {"label": "华尔街见闻", "color": "#3395FF", "icon": "📈"},
    "ithome":       {"label": "IT之家",     "color": "#0090D8", "icon": "💻"},
    "github":       {"label": "GitHub",     "color": "#6CCB5F", "icon": "🐙"},
    "hackernews":   {"label": "HackerNews", "color": "#FF6600", "icon": "⚡"},
    "toutiao":      {"label": "今日头条",   "color": "#E63946", "icon": "📰"},
    "weibo":        {"label": "微博热搜",   "color": "#FF9500", "icon": "🔥"},
    "douyin":       {"label": "抖音热搜",   "color": "#00F2EA", "icon": "🎵"},
    "v2ex":         {"label": "V2EX",       "color": "#4CAF50", "icon": "💬"},
    "producthunt":  {"label": "ProductHunt","color": "#DA5430", "icon": "🚀"},
    "bilibili":     {"label": "B站",        "color": "#FB7299", "icon": "📺"},
    "zhihu":        {"label": "知乎",       "color": "#0066FF", "icon": "💡"},
    "baidu":        {"label": "百度热搜",   "color": "#2932E1", "icon": "🔍"},
    "tieba":        {"label": "百度贴吧",   "color": "#4B90E0", "icon": "📋"},
    "cailianshe":   {"label": "财联社",     "color": "#C71A1A", "icon": "📡"},
    "pengpai":      {"label": "澎湃新闻",   "color": "#E60012", "icon": "📱"},
    "guancha":      {"label": "观察者网",   "color": "#2B5797", "icon": "👁️"},
    "163":          {"label": "网易新闻",   "color": "#DE1A1A", "icon": "📰"},
    "chuangye":     {"label": "创业邦",     "color": "#FF6B35", "icon": "🚀"},
    "juejin":       {"label": "掘金",       "color": "#0078F0", "icon": "💎"},
    "sspai":        {"label": "少数派",     "color": "#D33A2C", "icon": "📱"},
    "solidot":      {"label": "Solidot",    "color": "#555555", "icon": "🔗"},
    "coolapk":      {"label": "酷安",       "color": "#56B4E9", "icon": "📲"},
    "freebuf":      {"label": "FreeBuf",    "color": "#333333", "icon": "🛡️"},
    "hupu":         {"label": "虎扑",       "color": "#D32F2F", "icon": "🏀"},
    "tencent":      {"label": "腾讯新闻",   "color": "#1E90FF", "icon": "📺"},
    "ifeng":        {"label": "凤凰网",     "color": "#FF6600", "icon": "📰"},
    "zaobao":       {"label": "联合早报",   "color": "#B22222", "icon": "📰"},
    "chongbuluo":   {"label": "虫部落",     "color": "#4A90E2", "icon": "🔍"},
    "xueqiu":       {"label": "雪球",       "color": "#FF6B35", "icon": "📊"},
    "news_aggregator": {"label": "新闻聚合", "color": "#94A3B8", "icon": "📡"},
}

# URL → 平台映射
URL_PLATFORM_MAP = [
    (r'ithome\.com', 'ithome'),
    (r'news\.ycombinator\.com', 'hackernews'),
    (r'hackernews', 'hackernews'),
    (r'github\.com', 'github'),
    (r'v2ex\.com', 'v2ex'),
    (r'36kr\.com', '36kr'),
    (r'wallstreetcn\.com', 'wallstreetcn'),
    (r'toutiao\.com', 'toutiao'),
    (r'weibo\.com', 'weibo'),
    (r'zhihu\.com', 'zhihu'),
    (r'baidu\.com/s', 'baidu'),
    (r'tieba\.baidu\.com', 'tieba'),
    (r'cls\.cn', 'cailianshe'),
    (r'thepaper\.cn', 'pengpai'),
    (r'guancha\.cn', 'guancha'),
    (r'163\.com', '163'),
    (r'cyzone\.cn', 'chuangye'),
    (r'juejin\.cn', 'juejin'),
    (r'sspai\.com', 'sspai'),
    (r'solidot\.org', 'solidot'),
    (r'coolapk\.com', 'coolapk'),
    (r'freebuf\.com', 'freebuf'),
    (r'hupu\.com', 'hupu'),
    (r'news\.qq\.com', 'tencent'),
    (r'ifeng\.com', 'ifeng'),
    (r'zaobao\.com', 'zaobao'),
    (r'chongbuluo\.com', 'chongbuluo'),
    (r'xueqiu\.com', 'xueqiu'),
    (r'producthunt\.com', 'producthunt'),
    (r'bilibili\.com', 'bilibili'),
    (r'douyin\.com', 'douyin'),
    (r'zaochenbao\.com', 'news_aggregator'),
]

# 补充直接 RSS 源
SUPPLEMENTARY_RSS = [
    ("ruanyifeng",  "阮一峰",  "http://feeds.feedburner.com/ruanyifeng", "📡"),
    ("sspai",       "少数派",  "https://sspai.com/feed",                  "📱"),
    ("geekpark",    "GeekPark", "https://www.geekpark.net/rss",            "🚀"),
]

# 采集限制
PER_SOURCE_LIMIT = 15
MAX_TOTAL = 300

# ── 来源权重（用于评分加权和内容筛选）──
# 高分来源：开发者核心信息源，天然具有更高信息密度
# 低分来源：娱乐化严重，需要额外筛选
PLATFORM_WEIGHTS = {
    "github": 2,
    "hackernews": 2,
    "producthunt": 1,
    "v2ex": 1,
    "ithome": 1,
    "36kr": 1,
    "wallstreetcn": 1,
    "solidot": 1,
    "juejin": 1,
    "sspai": 1,
    "freebuf": 1,
    "xueqiu": 1,
    # 默认 0（toutiao, tencent, ifeng 等）
    # 低信噪比来源
    "weibo": -2,
    "douyin": -2,
    "baidu": -2,
    "tieba": -2,
    "bilibili": -1,
    "zhihu": -1,
    "hupu": -2,
    "coolapk": -1,
}

# 低信噪比平台 — 需要额外筛选才展示（仅限真正以娱乐八卦为主的平台）
NOISY_PLATFORMS = {"weibo", "douyin", "baidu", "tieba", "hupu"}
NOISE_SCORE_THRESHOLD = 4  # 低于此评分的条目丢弃（降低阈值避免误杀）
MAX_NOISE_REMOVAL_RATIO = 0.30  # 最多删除总量 30%，保证内容充裕
