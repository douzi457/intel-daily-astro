import fs from 'fs';
import path from 'path';
import type { DayData, IntelItem, Locale } from '../lib/types';

export type { Locale } from '../lib/types';

// Re-export platform metadata for backward compatibility (used by stats pages)
import { PLATFORM_META_ZH as PLATFORMS, PLATFORM_META_EN as PLATFORMS_EN } from '../lib/constants';
export { PLATFORMS, PLATFORMS_EN };

// 数据存放路径
const DATA_ROOT = path.join(process.cwd(), 'src/data/rewrite');

/** 获取指定日期的日报数据 */
export function getDayData(dateStr: string, locale: Locale = 'zh'): DayData {
  const jsonPath = path.join(DATA_ROOT, locale, `${dateStr}.json`);
  if (fs.existsSync(jsonPath)) {
    const raw = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
    return {
      date: raw.date || dateStr,
      items: (raw.items || []).map((item: any, idx: number) => ({
        id: item.id || idx + 1,
        url: item.url || '',
        platform: item.platform || 'news_aggregator',
        platform_label: item.platform_label || item.platform || '',
        platform_color: item.platform_color || '#94A3B8',
        platform_icon: item.platform_icon || '📌',
        hot: item.hot || 0,
        date: item.date || dateStr,
        score: item.score || 0,
        category: item.category || '其他',
        title: item.title || '',
        desc: item.desc || '',
        merged_sources: item.merged_sources || undefined,
        cross_sources: item.cross_sources || 0,
      })),
    };
  }
  return { date: dateStr, items: [] };
}

/** 获取所有已有数据的日期列表（降序） */
export function getAllDates(locale: Locale = 'zh'): string[] {
  const localeDir = path.join(DATA_ROOT, locale);
  if (!fs.existsSync(localeDir)) return [];
  return fs.readdirSync(localeDir)
    .filter(f => f.endsWith('.json'))
    .map(f => f.replace('.json', ''))
    .sort()
    .reverse();
}
