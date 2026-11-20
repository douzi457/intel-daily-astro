// 首页“加载更多”数据源（构建时生成）：当日时间线第 31 条往后的全部条目
// 排序与首页一致：按 score 倒序；字段只给客户端渲染条目必需的。
// v5：与首页同一口径——先排除今日精选 5 个事件（v4 topic 去重），再取第 31 条往后，
// 否则加载更多会把精选事件重复拼回列表里。
import { getDayData, getAllDates } from '../utils/data.ts';

export async function GET() {
  const dates = getAllDates('zh');
  const today = dates[0] || '';
  const items = getDayData(today, 'zh').items;
  const sorted = [...items].sort((a, b) => (b.score || 0) - (a.score || 0));

  // 复刻首页精选 5 的取法：v4 有摘要条目按展示分排，同一 topic 只留最高分
  const featuredUrls = new Set<string>();
  try {
    const v4Index = await import('../data/v4/index.json');
    const latestDate = (v4Index as any).default?.latest_date;
    if (latestDate) {
      const mod = await import(`../data/v4/daily-${latestDate}.json`);
      const v4: any = mod.default;
      const pool: any[] = [];
      if (v4?.by_category) {
        for (const cat of Object.values(v4.by_category)) {
          for (const it of (cat as any[])) {
            if (it.ai_summary && String(it.ai_summary).trim()) pool.push(it);
          }
        }
      }
      const ds = (it: any) => (typeof it.ai_score === 'number' && !isNaN(it.ai_score) ? it.ai_score : it.score || 0);
      pool.sort((a, b) => ds(b) - ds(a) || ((b.score || 0) - (a.score || 0)));
      const seen = new Set<string>();
      for (const it of pool) {
        const tp = String(it.topic || '').trim();
        if (tp && seen.has(tp)) continue;
        if (tp) seen.add(tp);
        featuredUrls.add(it.url);
        if (featuredUrls.size >= 5) break;
      }
    }
  } catch {}

  const rest = sorted.filter((it: any) => !featuredUrls.has(it.url));
  const page = rest.slice(30).map((it: any) => ({
    id: it.id,
    t: it.ai_title || it.title || '',
    u: it.url || '',
    p: it.platform_label || it.platform || it.source || '',
    tm: it.published_at || '',
    sc: it.source_count || 0,
    srcs: it.sources || [],
    s: typeof it.ai_score === 'number' && !isNaN(it.ai_score) ? it.ai_score : it.score || 0,
    sm: it.ai_summary || it.desc || it.title || '',
    r: it.ai_reason || '',
    c: it.category || '其他',
  }));
  return new Response(JSON.stringify({ date: today, total: rest.length, items: page }), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
}
