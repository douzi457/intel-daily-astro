// 首页“加载更多”数据源（构建时生成）：当日时间线第 31 条往后的全部条目
// 排序与首页一致：按 score 倒序；字段只给客户端渲染条目必需的。
import { getDayData, getAllDates } from '../utils/data.ts';

export async function GET() {
  const dates = getAllDates('zh');
  const today = dates[0] || '';
  const items = getDayData(today, 'zh').items;
  const sorted = [...items].sort((a, b) => (b.score || 0) - (a.score || 0));
  const rest = sorted.slice(30).map((it: any) => ({
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
  return new Response(JSON.stringify({ date: today, total: sorted.length, items: rest }), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
}
