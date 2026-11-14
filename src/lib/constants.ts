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
  // v4.2：补齐 rewrite 数据里出现、此前未列入的平台——否则日报页“查看今日全部 N 条”
  // 只渲染 SECTION_ORDER 里的平台，BBC / 纽约时报 / arXiv / 各家官方博客等约 640 条/天直接丢了，
  // 全站搜索链到日报页锚点时也找不到条目。
  'aihot', 'theverge', 'techcrunch', 'techmeme', 'arstechnica', 'arstechnicaai',
  'wired', 'thedecoder', 'bbc', 'nytimes', 'guardian', 'cbc', 'npr', 'euronews', 'sputnik',
  'nature', 'sciencedaily', 'infoq', 'ifanr', 'juejin', 'qbitai',
  'hackernoon', 'devto', 'lobsters', 'slashdot', 'simonwillison', 'latentspace',
  'arxivcs.ai', 'arxivcs.cl', 'arxivcs.lg',
  'openainews', 'anthropicnews', 'deepmindblog', 'googleresearchblog', 'microsoftresearch',
  'bairblog', 'nvidiablog', 'awsmlblog', 'cohereblog', 'mistralai', 'huggingfaceblog',
  'githubblog', 'perplexityblog', 'vllmblog', 'mitteltechreview',
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
  aihot:           { name: 'AIHOT',        icon: '🔥' },
  theverge:        { name: 'The Verge',   icon: '📰' },
  techcrunch:      { name: 'TechCrunch',  icon: '🚀' },
  techmeme:        { name: 'Techmeme',    icon: '📰' },
  arstechnica:     { name: 'Ars Technica', icon: '📰' },
  arstechnicaai:   { name: 'Ars Technica AI', icon: '🤖' },
  wired:           { name: 'Wired',       icon: '📡' },
  thedecoder:      { name: 'The Decoder', icon: '🤖' },
  bbc:             { name: 'BBC',         icon: '🌍' },
  nytimes:         { name: '纽约时报',     icon: '📰' },
  guardian:        { name: '卫报',         icon: '📰' },
  cbc:             { name: 'CBC',         icon: '🌍' },
  npr:             { name: 'NPR',         icon: '📻' },
  euronews:        { name: '欧洲新闻',     icon: '🌍' },
  sputnik:         { name: '卫星通讯社',   icon: '🛰️' },
  nature:          { name: 'Nature',      icon: '🔬' },
  sciencedaily:    { name: 'ScienceDaily', icon: '🔬' },
  infoq:           { name: 'InfoQ',       icon: '💻' },
  ifanr:           { name: '爱范儿',       icon: '📱' },
  juejin:          { name: '掘金',         icon: '⛏️' },
  qbitai:          { name: '量子位',       icon: '⚛️' },
  hackernoon:      { name: 'HackerNoon',  icon: '💻' },
  devto:           { name: 'DEV 社区',     icon: '💻' },
  lobsters:        { name: 'Lobsters',    icon: '🦞' },
  slashdot:        { name: 'Slashdot',    icon: '💻' },
  simonwillison:   { name: "Simon's Blog", icon: '✍️' },
  latentspace:     { name: 'Latent Space', icon: '🎙️' },
  'arxivcs.ai':    { name: 'arXiv AI',    icon: '📄' },
  'arxivcs.cl':    { name: 'arXiv 计算语言学', icon: '📄' },
  'arxivcs.lg':    { name: 'arXiv 机器学习', icon: '📄' },
  openainews:      { name: 'OpenAI 官方',  icon: '🤖' },
  anthropicnews:   { name: 'Anthropic 官方', icon: '🤖' },
  deepmindblog:    { name: 'DeepMind 博客', icon: '🧠' },
  googleresearchblog: { name: 'Google Research 博客', icon: '🔬' },
  microsoftresearch: { name: '微软研究院',  icon: '🔬' },
  bairblog:        { name: 'BAIR 博客',    icon: '🎓' },
  nvidiablog:      { name: 'NVIDIA 博客',  icon: '💚' },
  awsmlblog:       { name: 'AWS 机器学习博客', icon: '☁️' },
  cohereblog:      { name: 'Cohere 博客',  icon: '💬' },
  mistralai:       { name: 'Mistral AI',  icon: '🌬️' },
  huggingfaceblog: { name: 'Hugging Face 博客', icon: '🤗' },
  githubblog:      { name: 'GitHub 博客',  icon: '🐙' },
  perplexityblog:  { name: 'Perplexity 博客', icon: '🔍' },
  vllmblog:        { name: 'vLLM 博客',   icon: '⚡' },
  mitteltechreview: { name: 'MIT 科技评论', icon: '🎓' },
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
  aihot:           { name: 'AIHOT',        icon: '🔥' },
  theverge:        { name: 'The Verge',   icon: '📰' },
  techcrunch:      { name: 'TechCrunch',  icon: '🚀' },
  techmeme:        { name: 'Techmeme',    icon: '📰' },
  arstechnica:     { name: 'Ars Technica', icon: '📰' },
  arstechnicaai:   { name: 'Ars Technica AI', icon: '🤖' },
  wired:           { name: 'Wired',       icon: '📡' },
  thedecoder:      { name: 'The Decoder', icon: '🤖' },
  bbc:             { name: 'BBC',         icon: '🌍' },
  nytimes:         { name: 'NY Times',    icon: '📰' },
  guardian:        { name: 'The Guardian', icon: '📰' },
  cbc:             { name: 'CBC',         icon: '🌍' },
  npr:             { name: 'NPR',         icon: '📻' },
  euronews:        { name: 'Euronews',    icon: '🌍' },
  sputnik:         { name: 'Sputnik',     icon: '🛰️' },
  nature:          { name: 'Nature',      icon: '🔬' },
  sciencedaily:    { name: 'ScienceDaily', icon: '🔬' },
  infoq:           { name: 'InfoQ',       icon: '💻' },
  ifanr:           { name: 'iFanr',       icon: '📱' },
  juejin:          { name: 'Juejin',      icon: '⛏️' },
  qbitai:          { name: 'QbitAI',      icon: '⚛️' },
  hackernoon:      { name: 'HackerNoon',  icon: '💻' },
  devto:           { name: 'DEV Community', icon: '💻' },
  lobsters:        { name: 'Lobsters',    icon: '🦞' },
  slashdot:        { name: 'Slashdot',    icon: '💻' },
  simonwillison:   { name: "Simon's Blog", icon: '✍️' },
  latentspace:     { name: 'Latent Space', icon: '🎙️' },
  'arxivcs.ai':    { name: 'arXiv AI',    icon: '📄' },
  'arxivcs.cl':    { name: 'arXiv CL',    icon: '📄' },
  'arxivcs.lg':    { name: 'arXiv ML',    icon: '📄' },
  openainews:      { name: 'OpenAI News', icon: '🤖' },
  anthropicnews:   { name: 'Anthropic News', icon: '🤖' },
  deepmindblog:    { name: 'DeepMind Blog', icon: '🧠' },
  googleresearchblog: { name: 'Google Research Blog', icon: '🔬' },
  microsoftresearch: { name: 'Microsoft Research', icon: '🔬' },
  bairblog:        { name: 'BAIR Blog',   icon: '🎓' },
  nvidiablog:      { name: 'NVIDIA Blog', icon: '💚' },
  awsmlblog:       { name: 'AWS ML Blog', icon: '☁️' },
  cohereblog:      { name: 'Cohere Blog', icon: '💬' },
  mistralai:       { name: 'Mistral AI',  icon: '🌬️' },
  huggingfaceblog: { name: 'Hugging Face Blog', icon: '🤗' },
  githubblog:      { name: 'GitHub Blog', icon: '🐙' },
  perplexityblog:  { name: 'Perplexity Blog', icon: '🔍' },
  vllmblog:        { name: 'vLLM Blog',   icon: '⚡' },
  mitteltechreview: { name: 'MIT Tech Review', icon: '🎓' },
};

/** 获取指定语言的导航标签 */
export function getNavTabs(activeSections: string[], locale: 'zh' | 'en' = 'zh', includeFeatured: boolean = true): NavTab[] {
  const cats = locale === 'zh' ? SECTION_CATEGORIES_ZH : SECTION_CATEGORIES_EN;
  const tabs: NavTab[] = [];

  // 精选tab（可选）
  if (includeFeatured) {
    tabs.push({ id: 'featured', label: locale === 'zh' ? '精选' : 'Featured', icon: '⭐' });
  }

  // 实际有数据的分类
  for (const s of activeSections) {
    tabs.push({
      id: `section-${s}`,
      label: cats[s]?.name || s,
      icon: cats[s]?.icon || '📌',
    });
  }
  return tabs;
}

/** 获取平台元数据（带默认值） */
export function getPlatformMeta(platform: string, locale: 'zh' | 'en' = 'zh'): PlatformMeta {
  const map = locale === 'zh' ? PLATFORM_META_ZH : PLATFORM_META_EN;
  return map[platform] || { label: platform, icon: '📌', color: '#94A3B8' };
}

/** 网站基础信息 */
export const SITE = {
  url: 'https://daily.dianda.dpdns.org',
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
