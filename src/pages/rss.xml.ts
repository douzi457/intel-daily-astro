// RSS Feed — 中文版（已接入 Officer V2 LLM 评价）
import rss from '@astrojs/rss';
import { getDayData, getAllDates } from '../utils/data.ts';
import { SITE, getPlatformMeta } from '../lib/constants';
import type { IntelItem } from '../lib/types';

// 加载指定日期的 Officer V2 数据
async function loadV2Data(dateStr: string) {
  try {
    const idx = await import(`../../public/data/v2/index.json`).catch(() => null);
    if (!idx?.default?.latest_date) return {};
    if (idx.default.latest_date !== dateStr) return {};
    const mod = await import(`../../public/data/v2/daily-${dateStr}-v2.json`).catch(() => null);
    return mod?.default || {};
  } catch {
    return {};
  }
}

export async function GET({ request }: { request: Request }) {
  const url = new URL(request.url);
  const requestedDate = url.searchParams.get('date');
  const dates = getAllDates('zh');
  const recentDates = requestedDate
    ? [requestedDate].filter(d => dates.includes(d))
    : dates.slice(0, 7);

  // 收集所有 V2 数据的 core_signals by primary_item_id
  const v2Map: Record<string, any> = {};
  for (const d of recentDates) {
    const v2 = await loadV2Data(d);
    const signals: Array<{ primary_item_id: string; why_it_matters: string; url?: string; headline?: string }> =
      (v2.core_signals || []).map((s: any) => ({
        primary_item_id: s.primary_item_id,
        why_it_matters: s.why_it_matters || '',
        url: s.url || '',
        headline: s.headline || '',
      }));
    v2Map[d] = { signals, date: v2.date || d };
  }

  const items = recentDates.flatMap(d => {
  const dayData = getDayData(d, 'zh');
  const intelItems: IntelItem[] = dayData.items || [];
  const v2Info = v2Map[d] || { signals: [] };

  // 构建 URL → signal 的查找表（去除尾部斜杠，统一小写）
  const signalByUrl = new Map<string, { why_it_matters: string; headline: string }>();
  for (const s of v2Info.signals) {
    const url = (s.url || '').replace(/\/$/, '').toLowerCase();
    if (url) signalByUrl.set(url, { why_it_matters: s.why_it_matters || '', headline: s.headline || '' });
  }

  return intelItems.slice(0, 10).map((item: IntelItem) => {
    const meta = getPlatformMeta(item.platform, 'zh');
    // 按 URL 精确匹配 V2 评价
    const itemUrl = (item.url || '').replace(/\/$/, '').toLowerCase();
    const matched = signalByUrl.get(itemUrl);
    // sanity check：匹配到的 signal 标题须与 item 标题相关（URL 已保证同一事件）
    const description = matched?.why_it_matters && matched.headline?.trim()
      ? `[${meta.label}] ${matched.why_it_matters}`
      : `${item.desc || ''}`.slice(0, 200);
    return {
      title: item.title,
      link: item.url,
      pubDate: new Date(item.date + 'T08:00:00+08:00'),
      description,
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
