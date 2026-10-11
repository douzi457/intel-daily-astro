// ── Daily Officer V2 Types ──

/** 来源信息 */
export interface SourceInfo {
  id: string;
  name: string;
  home_url: string | null;
  tier: 'official' | 'primary-media' | 'specialist-media' | 'community' | 'aggregator' | 'unknown';
  language: 'zh' | 'en' | 'other';
  access_mode: 'rss' | 'api' | 'public-page' | 'existing-collector' | 'unknown';
}

/** 实体 */
export interface Entity {
  name: string;
  type: 'company' | 'product' | 'person' | 'technology' | 'other';
}

/** 建议动作 */
export interface SuggestedAction {
  type: 'try' | 'write' | 'watch' | 'decide' | 'ignore';
  text: string;
}

/** 评分详情 */
export interface ScoreDetail {
  total: number;
  relevance: number;      // 0-30
  impact: number;         // 0-20
  novelty: number;        // 0-20
  source_authority: number; // 0-15
  actionability: number;  // 0-15
  penalties: number;      // 0-100
  reason: string;
}

/** 标准条目 Item (V2) */
export interface V2Item {
  id: string;
  title: string;
  title_original: string;
  url: string;
  canonical_url: string;
  source: SourceInfo;
  category: string;
  tags: string[];
  entities: Entity[];
  published_at: string | null;
  published_at_confidence: 'exact' | 'estimated' | 'unknown';
  first_seen_at: string;
  last_seen_at: string;
  language: 'zh' | 'en' | 'other';
  raw_summary: string;
  clean_summary: string;
  evidence_points: string[];
  why_it_matters: string;
  suggested_action: SuggestedAction;
  confidence: number;
  uncertainty: string | null;
  score: ScoreDetail;
}

/** 事件 Event */
export interface V2Event {
  event_id: string;
  headline: string;
  clean_summary: string;
  primary_item_id: string;
  supporting_item_ids: string[];
  source_count: number;
  mention_count: number;
  first_seen_at: string;
  last_seen_at: string;
  status: 'new' | 'developing' | 'continuing';
  tags: string[];
  entities: Entity[];
  why_it_matters: string;
  suggested_action: SuggestedAction;
  confidence: number;
  uncertainty: string | null;
  score: ScoreDetail;
}

/** 质量指标 */
export interface QualityMetrics {
  raw_items: number;
  normalized_items: number;
  unique_events: number;
  exact_duplicate_rate: number;
  core_event_duplicate_count: number;
  dead_link_rate: number;
  empty_summary_rate: number;
  noise_summary_rate: number;
  stale_source_count: number;
  top_score_tie_rate: number;
}

/** QA 质量报告 */
export interface QualityReport {
  total: number;
  grade: 'pass' | 'pilot' | 'fail';
  components: {
    coverage: number;
    relevance: number;
    event_dedup: number;
    score_discrimination: number;
    summary_cleanliness: number;
    actionability: number;
    freshness: number;
    link_health: number;
  };
  metrics: QualityMetrics;
  gates: Array<{
    id: string;
    passed: boolean;
    detail: string;
  }>;
  warnings: string[];
}

/** 来源健康 */
export interface SourceHealth {
  name: string;
  category: string;
  count: number;
  last_updated: string | null;
  status: 'normal' | 'delayed' | 'failed' | 'no-data';
  issues: string[];
}

/** 已过滤概览 */
export interface IgnoredSummary {
  reason: string;
  count: number;
  examples: Array<{ title: string; url: string; source: string; }>;
}

/** V2 顶层数据 */
export interface V2DailyData {
  schema_version: 2;
  date: string;
  generated_at: string;
  timezone: string;
  profile_id: string;
  
  stats: {
    raw_items: number;
    normalized_items: number;
    unique_events: number;
    core_signals: number;
    watchlist: number;
    ignored: number;
  };
  
  executive_summary: string[];
  core_signals: V2Event[];
  watchlist: V2Event[];
  actions: SuggestedAction[];
  ignored_summary: IgnoredSummary[];
  source_health: SourceHealth[];
  quality: QualityReport;
  
  items: V2Item[];
  events: V2Event[];
}

/** 画像配置 */
export interface ProfileConfig {
  id: string;
  name: string;
  description: string;
  include_keywords: string[];
  exclude_keywords: string[];
  entities_watch: Entity[];
  category_weights: Record<string, number>;
  source_boost: string[];
  source_block: string[];
  languages: ('zh' | 'en' | 'other')[];
  core_limit: number;
  watch_limit: number;
  action_limit: number;
  reading_minutes: number;
  confidence_threshold: number;
}
