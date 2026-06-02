// RSS Feed — 中文版
import rss from '@astrojs/rss';
import { getDayData, getAllDates } from '../utils/data.ts';
import { SITE, getPlatformMeta } from '../lib/constants';
import type { IntelItem } from '../lib/types';

export async function GET() {
  const dates = getAllDates('zh');
  const recentDates = dates.slice(0, 7);

  const items = recentDates.flatMap(d => {
    const dayData = getDayData(d, 'zh');
    const intelItems: IntelItem[] = dayData.items || [];
    return intelItems.slice(0, 10).map((item: IntelItem) => {
      const meta = getPlatformMeta(item.platform, 'zh');
      return {
        title: item.title,
        link: item.url,
        pubDate: new Date(item.date + 'T08:00:00+08:00'),
        description: item.desc || `[${meta.label}] AI 评分: ${item.score}`,
        categories: [item.platform, item.category],
      };
    });
  });

  return rss({
    title: `${SITE.name} · 每日情报 RSS`,
    description: SITE.description,
    site: SITE.url,
    items: items.slice(0, 100),
    customData: `<language>zh-CN</language>`,
  });
}
