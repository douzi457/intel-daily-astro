// ── Shared TypeScript Interfaces ──

/** 情报条目 */
export interface IntelItem {
  id: number;
  url: string;
  platform: string;
  platform_label: string;
  platform_color: string;
  platform_icon: string;
  hot: number;
  date: string;
  score: number;
  category: string;
  title: string;
  desc: string;
  merged_sources?: MergedSource[];
  cross_sources?: number;
}

/** 合并来源 */
export interface MergedSource {
  platform: string;
  label: string;
  color: string;
  icon: string;
  url: string;
}

/** 日报数据 */
export interface DayData {
  date: string;
  items: IntelItem[];
}

/** 平台元数据 */
export interface PlatformMeta {
  label: string;
  icon: string;
  color: string;
}

/** 分类元数据 */
export interface SectionCategory {
  name: string;
  icon: string;
}

/** 导航标签 */
export interface NavTab {
  id: string;
  label: string;
  icon: string;
}

/** 今日重点中的高亮条目 */
export interface FocusHighlight {
  rank: number;
  title: string;
  reason: string;
  insight?: string;
  summary?: string;
  source?: string;
  url?: string;
}

/** 今日重点数据 */
export interface FocusData {
  date: string;
  generated_at: string;
  summary?: string;
  trendAnalysis?: string;
  dailyPick?: string;
  highlights: FocusHighlight[];
  trends: string[];
}

/** 公众号文章 */
export interface GzhArticle {
  title: string;
  url: string;
  date?: string;
}

/** V4 推荐条目（来自 dashboard_v4 的每日精选） */
export interface V4RecommendItem {
  title: string;
  title_original: string;
  url: string;
  source: string;
  score: number;
  summary: string;
  heat: string;
}

/** V4 每日数据（来自 dashboard_v4 的 JSON 输出） */
export interface V4DailyData {
  date: string;
  generated_at: string;
  summary: string;
  total_items: number;
  total_sources: number;
  total_translated: number;
  recommendations: Record<string, V4RecommendItem[]>;
  by_category: Record<string, {
    title: string;
    url: string;
    source: string;
    score: number;
    heat: string;
  }[]>;
  sources: { name: string; category: string; count: number }[];
}

/** 广告轮播项 */
export interface AdPromo {
  src?: string;
  href: string;
  alt?: string;
  text?: string;
}
