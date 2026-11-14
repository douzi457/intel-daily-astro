// 全站搜索索引 · 按月分片（构建时生成）
// 源：src/data/rewrite/zh/*.json（首页时间线与日报页渲染的同一份数据）
// 字段只留搜索与展示必需的：t 标题、d 日期、i 条目 id、s 展示分、a 摘要片段（≤80 字）、p 来源
// 展示分口径与首页一致：ai_score 是数字就用它，否则回落到 score。
import fs from 'fs';
import path from 'path';

export async function getStaticPaths() {
  const dir = path.join(process.cwd(), 'src/data/rewrite/zh');
  const months = new Set<string>();
  if (fs.existsSync(dir)) {
    for (const f of fs.readdirSync(dir)) {
      const m = f.match(/^(\d{4}-\d{2})-\d{2}\.json$/);
      if (m) months.add(m[1]);
    }
  }
  return [...months].sort().map((month) => ({ params: { month } }));
}

function displayScore(it: any): number {
  const a = it.ai_score;
  return typeof a === 'number' && !isNaN(a) ? a : it.score || 0;
}

export async function GET({ params }: { params: { month: string } }) {
  const { month } = params;
  const dir = path.join(process.cwd(), 'src/data/rewrite/zh');
  const items: Array<{ t: string; d: string; i: number; s: number; a: string; p: string }> = [];
  if (fs.existsSync(dir)) {
    const files = fs
      .readdirSync(dir)
      .filter((f) => f.startsWith(month) && f.endsWith('.json'))
      .sort();
    for (const f of files) {
      const date = f.replace('.json', '');
      let raw: any = {};
      try {
        raw = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf-8'));
      } catch {
        continue;
      }
      (raw.items || []).forEach((it: any, idx: number) => {
        const title = String(it.ai_title || it.title || '').trim();
        if (!title) return;
        items.push({
          t: title,
          d: date,
          i: it.id || idx + 1,
          s: displayScore(it),
          a: String(it.ai_summary || '').slice(0, 80),
          p: it.platform_label || it.platform || it.source || '',
        });
      });
    }
  }
  return new Response(JSON.stringify({ month, count: items.length, items }), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
}
