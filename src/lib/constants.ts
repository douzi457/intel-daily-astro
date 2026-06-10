// ── Shared Constants ──
// 所有页面共享的平台元数据、排序、分类定义

import type { PlatformMeta, SectionCategory, NavTab } from './types';

/** 平台元数据（中文） */
export const PLATFORM_META_ZH: Record<string, PlatformMeta> = {
  weibo:           { label: '微博',       icon: '🔥', color: '#FF9500' },
  hackernews:      { label: 'HackerNews', icon: '⚡', color: '#FF6600' },
  github:          { label: 'GitHub',     icon: '🐙', color: '#6CCB5F' },
  producthunt:     { label: 'ProductHunt',icon: '🚀', color: '#DA5430' },
  v2ex:            { label: 'V2EX',       icon: '💬', color: '#4CAF50' },
  twitter:         { label: 'X/Twitter',   icon: '🐦', color: '#1DA1F2' },
  reddit:          { label: 'Reddit',     icon: '🤖', color: '#FF4500' },
  ithome:          { label: 'IT之家',     icon: '💻', color: '#0090D8' },
  '36kr':          { label: '36氪',       icon: '📊', color: '#4A90E2' },
  wallstreetcn:    { label: '华尔街见闻', icon: '📈', color: '#3395FF' },
  toutiao:         { label: '今日头条',   icon: '📰', color: '#E63946' },
  douyin:          { label: '抖音',       icon: '🎵', color: '#00F2EA' },
  news_aggregator: { label: '快讯聚合',   icon: '📌', color: '#94A3B8' },
  bilibili:        { label: 'B站',        icon: '📺', color: '#FB7299' },
  zhihu:           { label: '知乎',       icon: '💡', color: '#0066FF' },
  baidu:           { label: '百度热搜',   icon: '🔍', color: '#2932E1' },
  tieba:           { label: '百度贴吧',   icon: '📋', color: '#4B90E0' },
  cailianshe:      { label: '财联社',     icon: '📡', color: '#C71A1A' },
  pengpai:         { label: '澎湃新闻',   icon: '📱', color: '#E60012' },
  guancha:         { label: '观察者网',   icon: '👁️', color: '#2B5797' },
  '163':           { label: '网易新闻',   icon: '📰', color: '#DE1A1A' },
  chuangye:        { label: '创业邦',     icon: '🚀', color: '#FF6B35' },
};

/** 平台元数据（英文） */
export const PLATFORM_META_EN: Record<string, PlatformMeta> = {
  weibo:           { label: 'Weibo',        icon: '🔥', color: '#FF9500' },
  hackernews:      { label: 'HackerNews',   icon: '⚡', color: '#FF6600' },
  github:          { label: 'GitHub',       icon: '🐙', color: '#6CCB5F' },
  producthunt:     { label: 'ProductHunt',  icon: '🚀', color: '#DA5430' },
  v2ex:            { label: 'V2EX',         icon: '💬', color: '#4CAF50' },
  twitter:         { label: 'X/Twitter',     icon: '🐦', color: '#1DA1F2' },
  reddit:          { label: 'Reddit',       icon: '🤖', color: '#FF4500' },
  ithome:          { label: 'IT Home',      icon: '💻', color: '#0090D8' },
  '36kr':          { label: '36Kr',         icon: '📊', color: '#4A90E2' },
  wallstreetcn:    { label: 'WallStreetCN', icon: '📈', color: '#3395FF' },
  toutiao:         { label: 'TouTiao',      icon: '📰', color: '#E63946' },
  douyin:          { label: 'Douyin',       icon: '🎵', color: '#00F2EA' },
  news_aggregator: { label: 'News Feed',    icon: '📌', color: '#94A3B8' },
  bilibili:        { label: 'Bilibili',     icon: '📺', color: '#FB7299' },
  zhihu:           { label: 'Zhihu',        icon: '💡', color: '#0066FF' },
  baidu:           { label: 'Baidu Hot',    icon: '🔍', color: '#2932E1' },
  tieba:           { label: 'Baidu Tieba',  icon: '📋', color: '#4B90E0' },
  cailianshe:      { label: 'Cailianshe',   icon: '📡', color: '#C71A1A' },
  pengpai:         { label: 'The Paper',    icon: '📱', color: '#E60012' },
  guancha:         { label: 'Guancha',      icon: '👁️', color: '#2B5797' },
  '163':           { label: 'NetEase News', icon: '📰', color: '#DE1A1A' },
  chuangye:        { label: 'Cyzone',       icon: '🚀', color: '#FF6B35' },
};

/** 分区展示顺序（中英文共用） */
export const SECTION_ORDER = [
  'weibo', 'hackernews', 'github', 'producthunt', 'v2ex', 'twitter', 'reddit',
  'ithome', '36kr', 'wallstreetcn', 'toutiao', 'douyin',
  'news_aggregator', 'bilibili', 'zhihu', 'baidu', 'tieba',
  'cailianshe', 'pengpai', 'guancha', '163', 'chuangye',
];

/** 分区中文名 */
export const SECTION_CATEGORIES_ZH: Record<string, SectionCategory> = {
  weibo:           { name: '微博热搜',   icon: '🔥' },
  twitter:         { name: 'X/Twitter',   icon: '🐦' },
  reddit:          { name: 'Reddit',      icon: '🤖' },
  hackernews:      { name: '开发者社区', icon: '💻' },
  github:          { name: '开源项目',   icon: '🐙' },
  producthunt:     { name: '新品发布',   icon: '🚀' },
  v2ex:            { name: 'V2EX 热议',  icon: '💬' },
  ithome:          { name: '科技资讯',   icon: '💻' },
  '36kr':          { name: '商业科技',   icon: '📊' },
  wallstreetcn:    { name: '华尔街见闻', icon: '📈' },
  toutiao:         { name: '今日头条',   icon: '📰' },
  douyin:          { name: '抖音',       icon: '🎵' },
  news_aggregator: { name: '快讯聚合',   icon: '📌' },
  bilibili:        { name: 'B站',        icon: '📺' },
  zhihu:           { name: '知乎',       icon: '💡' },
  baidu:           { name: '百度热搜',   icon: '🔍' },
  tieba:           { name: '百度贴吧',   icon: '📋' },
  cailianshe:      { name: '财联社',     icon: '📡' },
  pengpai:         { name: '澎湃新闻',   icon: '📱' },
  guancha:         { name: '观察者网',   icon: '👁️' },
  '163':           { name: '网易新闻',   icon: '📰' },
  chuangye:        { name: '创业邦',     icon: '🚀' },
};

/** 分区英文名 */
export const SECTION_CATEGORIES_EN: Record<string, SectionCategory> = {
  weibo:           { name: 'Weibo Hot',     icon: '🔥' },
  twitter:         { name: 'X/Twitter',      icon: '🐦' },
  reddit:          { name: 'Reddit',         icon: '🤖' },
  hackernews:      { name: 'Dev Community', icon: '💻' },
  github:          { name: 'Open Source',   icon: '🐙' },
  producthunt:     { name: 'New Products',  icon: '🚀' },
  v2ex:            { name: 'V2EX',          icon: '💬' },
  ithome:          { name: 'Tech News',     icon: '💻' },
  '36kr':          { name: '36Kr',          icon: '📊' },
  wallstreetcn:    { name: 'WallStreetCN',  icon: '📈' },
  toutiao:         { name: 'TouTiao',       icon: '📰' },
  douyin:          { name: 'Douyin',        icon: '🎵' },
  news_aggregator: { name: 'News Feed',     icon: '📌' },
  bilibili:        { name: 'Bilibili',      icon: '📺' },
  zhihu:           { name: 'Zhihu',         icon: '💡' },
  baidu:           { name: 'Baidu Hot',     icon: '🔍' },
  tieba:           { name: 'Baidu Tieba',   icon: '📋' },
  cailianshe:      { name: 'Cailianshe',    icon: '📡' },
  pengpai:         { name: 'The Paper',     icon: '📱' },
  guancha:         { name: 'Guancha',       icon: '👁️' },
  '163':           { name: 'NetEase News',  icon: '📰' },
  chuangye:        { name: 'Cyzone',        icon: '🚀' },
};

/** 获取指定语言的导航标签 */
export function getNavTabs(activeSections: string[], locale: 'zh' | 'en' = 'zh'): NavTab[] {
  const cats = locale === 'zh' ? SECTION_CATEGORIES_ZH : SECTION_CATEGORIES_EN;
  return [
    { id: 'featured', label: locale === 'zh' ? '精选' : 'Featured', icon: '⭐' },
    ...activeSections.map(s => ({
      id: `section-${s}`,
      label: cats[s]?.name || s,
      icon: cats[s]?.icon || '📌',
    })),
  ];
}

/** 获取平台元数据（带默认值） */
export function getPlatformMeta(platform: string, locale: 'zh' | 'en' = 'zh'): PlatformMeta {
  const map = locale === 'zh' ? PLATFORM_META_ZH : PLATFORM_META_EN;
  return map[platform] || { label: platform, icon: '📌', color: '#94A3B8' };
}

/** 网站基础信息 */
export const SITE = {
  url: 'https://dianda.dpdns.org',
  name: '豆子实验室',
  nameEn: 'Douzi Lab',
  description: '每日自动采集全球科技资讯，AI 智能评分 · 双语播报 · 开发者情报枢纽',
  descriptionEn: 'Daily automated tech intelligence with AI scoring, bilingual coverage for developers.',
};

/** 星期标签 */
export const DOW_LABELS_ZH = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
export const DOW_LABELS_EN = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export function getDow(dateStr: string, locale: 'zh' | 'en' = 'zh'): string {
  const idx = new Date(dateStr + 'T00:00:00').getDay();
  const labels = locale === 'zh' ? DOW_LABELS_ZH : DOW_LABELS_EN;
  return labels[idx === 0 ? 6 : idx - 1];
}
