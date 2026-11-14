// 全站搜索索引清单（构建时生成）：有哪些月份分片、各多少条
import fs from 'fs';
import path from 'path';

export async function GET() {
  const dir = path.join(process.cwd(), 'src/data/rewrite/zh');
  const months: Record<string, number> = {};
  if (fs.existsSync(dir)) {
    for (const f of fs.readdirSync(dir).sort()) {
      const m = f.match(/^(\d{4}-\d{2})-\d{2}\.json$/);
      if (!m) continue;
      let n = 0;
      try {
        n = (JSON.parse(fs.readFileSync(path.join(dir, f), 'utf-8')).items || []).length;
      } catch {}
      months[m[1]] = (months[m[1]] || 0) + n;
    }
  }
  const list = Object.entries(months)
    .sort()
    .reverse()
    .map(([month, count]) => ({ month, count }));
  return new Response(
    JSON.stringify({ months: list, total: list.reduce((a, b) => a + b.count, 0) }),
    { headers: { 'Content-Type': 'application/json; charset=utf-8' } },
  );
}
