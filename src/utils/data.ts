import fs from 'fs';
import path from 'path';

// 语言配置
export type Locale = 'zh' | 'en';

// 平台元数据
export const PLATFORMS: Record<string, { label: string; color: string; tab: string; icon: string }> = {
  weibo:        { label: '微博',     color: '#FF9500', tab: '热搜',  icon: '🔥' },
  douyin:       { label: '抖音',     color: '#00F2EA', tab: '热搜',  icon: '🎵' },
  wallstreetcn: { label: '华尔街见闻', color: '#3395FF', tab: '财经', icon: '📈' },
  '36kr':       { label: '36Kr',    color: '#4A90E2', tab: '财经',  icon: '📊' },
  toutiao:      { label: '今日头条', color: '#E63946', tab: '财经',  icon: '📰' },
  tencent:      { label: '腾讯新闻', color: '#1DB100', tab: '财经',  icon: '🌐' },
  ithome:       { label: 'IT之家',  color: '#0090D8', tab: '开发',  icon: '💻' },
  github:       { label: 'GitHub',  color: '#6CCB5F', tab: '开发',  icon: '🐙' },
  hackernews:   { label: 'HN',       color: '#FF6600', tab: '开发',  icon: '⚡' },
  producthunt:  { label: 'ProductHunt', color: '#DA5430', tab: '开发', icon: '🚀' },
  v2ex:         { label: 'V2EX',    color: '#4CAF50', tab: '开发',  icon: '💬' },
  gzh:          { label: '公众号',  color: '#2ECC71', tab: '公众号', icon: '📮' },
  bilibili:     { label: 'B站',     color: '#FB7299', tab: '热搜',  icon: '📺' },
  zhihu:        { label: '知乎',     color: '#0066FF', tab: '热搜',  icon: '💡' },
  baidu:        { label: '百度热搜', color: '#2932E1', tab: '热搜',  icon: '🔍' },
  tieba:        { label: '百度贴吧', color: '#4B90E0', tab: '热搜',  icon: '📋' },
  cailianshe:   { label: '财联社',   color: '#C71A1A', tab: '财经',  icon: '📡' },
  pengpai:      { label: '澎湃新闻', color: '#E60012', tab: '财经',  icon: '📱' },
  guancha:      { label: '观察者网', color: '#2B5797', tab: '财经',  icon: '👁️' },
  '163':        { label: '网易新闻', color: '#DE1A1A', tab: '财经',  icon: '📰' },
  chuangye:     { label: '创业邦',   color: '#FF6B35', tab: '财经',  icon: '🚀' },
};

// 英文标签映射 (用于英文版展示)
export const PLATFORMS_EN: Record<string, string> = {
  weibo: 'Weibo', douyin: 'TikTok China', wallstreetcn: 'WallStreetCN', '36kr': '36Kr',
  toutiao: 'TouTiao', tencent: 'Tencent News', ithome: 'IT Home', github: 'GitHub',
  hackernews: 'HackerNews', producthunt: 'ProductHunt', v2ex: 'V2EX', gzh: 'WeChat OA',
  bilibili: 'Bilibili', zhihu: 'Zhihu', baidu: 'Baidu Hot', tieba: 'Baidu Tieba',
  cailianshe: 'Cailianshe', pengpai: 'The Paper', guancha: 'Guancha', '163': 'NetEase News',
  chuangye: 'Cyzone',
};

export const TABS = ['热搜', '财经', '开发', '公众号'];
export const TABS_EN = ['Trending', 'Finance', 'Dev', 'Society'];

export const TAB_COLORS: Record<string, string> = {
  '热搜': '#FF9500', '财经': '#3395FF', '开发': '#6CCB5F', '公众号': '#2ECC71',
  'Trending': '#FF9500', 'Finance': '#3395FF', 'Dev': '#6CCB5F', 'Society': '#2ECC71',
};

export const TAB_ICONS: Record<string, string> = {
  '热搜': '🔥', '财经': '📈', '开发': '💻', '公众号': '📮',
  'Trending': '🔥', 'Finance': '📈', 'Dev': '💻', 'Society': '📮',
};

// ── AI 话题分类元数据 ──
export const CATEGORIES: Record<string, { label: string; labelEn: string; icon: string; color: string }> = {
  'AI模型':   { label: 'AI模型', labelEn: 'AI Models', icon: '🤖', color: '#A78BFA' },
  '开源项目': { label: '开源项目', labelEn: 'Open Source', icon: '🐙', color: '#6CCB5F' },
  '融资并购': { label: '融资并购', labelEn: 'Funding', icon: '💰', color: '#F59E0B' },
  '政策监管': { label: '政策监管', labelEn: 'Policy', icon: '⚖️', color: '#EF4444' },
  '商业动态': { label: '商业动态', labelEn: 'Business', icon: '📊', color: '#3395FF' },
  '技术突破': { label: '技术突破', labelEn: 'Tech Breakthrough', icon: '🔬', color: '#10B981' },
  '安全隐私': { label: '安全隐私', labelEn: 'Security', icon: '🔒', color: '#F97316' },
  '其他':     { label: '其他资讯', labelEn: 'Other', icon: '📌', color: '#94A3B8' },
};

export const CATEGORY_ORDER = ['AI模型', '开源项目', '融资并购', '政策监管', '商业动态', '技术突破', '安全隐私', '其他'];

// 数据存放路径
const DATA_ROOT = path.join(process.cwd(), 'src/data/rewrite');

export function getDayData(dateStr: string, locale: Locale = 'zh') {
  const jsonPath = path.join(DATA_ROOT, locale, `${dateStr}.json`);
  if (fs.existsSync(jsonPath)) {
    return JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
  }
  return { date: dateStr, items: [] };
}

export function getAllDates(locale: Locale = 'zh'): string[] {
  const localeDir = path.join(DATA_ROOT, locale);
  if (!fs.existsSync(localeDir)) return [];
  return fs.readdirSync(localeDir)
    .filter(f => f.endsWith('.json'))
    .map(f => f.replace('.json', ''))
    .sort()
    .reverse();
}
