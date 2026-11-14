// functions/mcp.js — 豆子实验室「每日情报」只读 MCP（Pages Functions 版）
// ============================================================================
// 批准：2026-11-14，老大先点 Worker 版，后改定 Pages Functions 版（跟站走）。
// 路由：POST /mcp（JSON-RPC 2.0，Streamable HTTP，无状态）；GET /mcp 返回信息页。
// 形态：独立只读 Function，只读本站公开 JSON，不碰管线，不新增采集、不调 LLM、
//       不需要 key、不写任何数据。部署跟站走：现有 GitHub Action
//       （wrangler pages deploy dist/）运行时，仓库根目录的 functions/ 会
//       随项目一起上传（Cloudflare 官方文档：命令在哪里运行，
//       那里的 functions 文件夹就随项目一起上传）。
//
// 三个工具：
//   daily_today   今天的日报：按 AI 评分取今日最值得看的条目
//   daily_search  按关键词搜全站日报（标题 + 摘要）
//   daily_signal  回答第一个问题：今天哪几条值得先动手或先避开，为什么？
//
// 数据源（公开 JSON，实测字段，2026-11-14）：
//   /search-index/YYYY-MM.json  月索引 {month, count, items:[{t 标题, d 日期,
//     i 条目 id, s 展示分（有 AI 评分时就是 ai_score，否则是旧分）, a 摘要,
//     p 来源}]}
//     注意：s 只有在 a（摘要）非空的条目上才是真正的 ai_score（0–8）；
//     没有摘要的条目 s 是旧分（常年 10.0 扎堆，分不出高下），所以排名
//     只覆盖有摘要的条目——这一点三个工具都会在返回里写明，不藏着。
//   /more-today.json  今日 31 条之后的条目 {date, total, items:[{id, t, u, p,
//     tm, sc, srcs, s ai_score, sm 摘要, r 推荐理由, c 分类}]}，
//     仅用于给 daily_signal 补推荐理由（r），按 id 关联；拿不到也不报错。
//
// 成本与体积（实施前写明，数字来自 Cloudflare 官方文档）：
//   托管：Pages Functions 与 Workers 共用免费档 $0——每天 10 万次请求、
//     每次请求 10ms CPU、每次请求最多 50 个子请求；超了返回 Error 1027，
//     不产生账单。付费档 $5/月（含 1000 万次请求/月），只有免费档不够用时才需要。
//     本 Function 每次工具调用只发 1–2 个子请求（月索引约 1.7MB、
//     more-today 约 280KB，服务端拉取，走 10 分钟缓存），
//     CPU 大头是解析月索引（冷启动一次，热请求走内存缓存不重复解析）。
//   返回体积：每个工具每次最多返回 10 条（daily_today 默认 8 条），
//     每条约 200–400 字，整个响应约 2–8KB；绝不把整包 JSON 吐给客户端
//     （此前 agent 须整包下载 latest.json 约 400KB 或 v2 约 3.5MB 自筛）。
//
// 本地测试：node test-mcp-pages.mjs（直接调本文件的 onRequest，打真实线上数据）。
// Worker 版（同逻辑、独立部署）见 ../mcp-worker.js，仅作备选。

const SITE = 'https://daily.dianda.dpdns.org';
const PROTOCOL_VERSION = '2025-03-26';
const SERVER_NAME = 'daily-mcp';
const SERVER_VERSION = '0.1.0';
const CACHE_TTL_MS = 10 * 60 * 1000; // 月索引 / more-today 的内存缓存：10 分钟
const FETCH_TIMEOUT_MS = 10_000;

// 服务端说明（initialize 下发；学 Gary 的 radar/mcp.py：先结论后细节，
// 只用工具数据，数字照原样，附链接，查不到就直说）。
const INSTRUCTIONS = [
  '你是豆子实验室「每日情报」的只读助手。回答先给结论，再给细节。',
  '只用工具返回的数据回答问题。数字（评分、条数、日期）照原样引用，不换算、不四舍五入、不编造。',
  '每条结论都附工具给的站内链接（/day/日期/#entry-条目 id），不要自己拼原文链接。',
  '工具没给的信息直接说查不到，不要编：包括没有 AI 摘要的条目没有评分、没有“先避开”榜单（数据里没有这项信号）。',
  '如果工具返回“没找到”，如实转告，不要用别的条目凑数。',
  '回答用中文 Markdown。',
].join('\n');

// ---------------------------------------------------------------------------
// 数据层：内存缓存（同 isolate 内复用；冷启动才重新拉取 + 解析）
// ---------------------------------------------------------------------------
const cache = {
  indexMonth: '',
  indexAt: 0,
  index: null, // { month, count, items }
  moreAt: 0,
  moreById: null, // Map<id, { r, sm }>
};

async function fetchJson(url) {
  const res = await fetch(url, {
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    // 让 Cloudflare 边缘缓存这份公开 JSON 10 分钟；Node 下会被忽略。
    cf: { cacheTtl: 600 },
  });
  if (res.status === 404) {
    const err = new Error(`not found: ${url}`);
    err.code = 404;
    throw err;
  }
  if (!res.ok) throw new Error(`fetch failed: ${url} -> HTTP ${res.status}`);
  // 站点对不存在的 .json 路径会回 200 + 404 HTML 页（实测 2020-01），
  // 不能只看状态码：内容是 HTML 或解析失败都按“没有这份数据”处理。
  const ctype = res.headers.get('content-type') || '';
  if (ctype.includes('text/html')) {
    const err = new Error(`not found (HTML fallback): ${url}`);
    err.code = 404;
    throw err;
  }
  try {
    return await res.json();
  } catch {
    const err = new Error(`not JSON: ${url}`);
    err.code = 404;
    throw err;
  }
}

async function loadIndex(month) {
  const now = Date.now();
  if (cache.index && cache.indexMonth === month && now - cache.indexAt < CACHE_TTL_MS) {
    return cache.index;
  }
  const data = await fetchJson(`${SITE}/search-index/${month}.json`);
  if (!data || !Array.isArray(data.items)) {
    const err = new Error(`bad index shape: ${month}`);
    err.code = 404;
    throw err;
  }
  cache.index = data;
  cache.indexMonth = month;
  cache.indexAt = now;
  return data;
}

// more-today.json 只用于补推荐理由；拿不到、格式不对都不影响主流程。
async function loadReasons() {
  const now = Date.now();
  if (cache.moreById && now - cache.moreAt < CACHE_TTL_MS) return cache.moreById;
  const byId = new Map();
  try {
    const data = await fetchJson(`${SITE}/more-today.json`);
    if (data && Array.isArray(data.items)) {
      for (const it of data.items) {
        if (it && typeof it.id === 'number') byId.set(it.id, { r: it.r || '', sm: it.sm || '' });
      }
    }
  } catch {
    // 忽略：没有推荐理由也能回答，摘要还在。
  }
  cache.moreById = byId;
  cache.moreAt = now;
  return byId;
}

function currentMonth() {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, '0')}`;
}

function anchor(date, id) {
  return `${SITE}/day/${date}/#entry-${id}`;
}

function short(text, max = 120) {
  const t = String(text || '').replace(/\s+/g, ' ').trim();
  return t.length > max ? t.slice(0, max) + '…' : t;
}

// 今日已评分条目：取索引里最新一天、有摘要的条目，按展示分倒序。
function rankedToday(index) {
  let latest = '';
  for (const it of index.items) {
    if (typeof it.d === 'string' && it.d > latest) latest = it.d;
  }
  const today = index.items.filter((it) => it.d === latest);
  const scored = today.filter((it) => it.a && String(it.a).trim() !== '');
  scored.sort((a, b) => (b.s || 0) - (a.s || 0) || (a.i || 0) - (b.i || 0));
  return { date: latest, total: today.length, scored: scored.length, items: scored };
}

function toItem(it, reasons) {
  const reason = reasons ? reasons.get(it.i) : null;
  return {
    id: it.i,
    title: it.t || '',
    score: typeof it.s === 'number' ? it.s : null,
    platform: it.p || '',
    date: it.d || '',
    summary: it.a || '',
    reason: (reason && reason.r) || '',
    url: anchor(it.d, it.i),
  };
}

function clampLimit(v, def, min, max) {
  if (v === undefined || v === null) return def;
  const n = Number(v);
  if (!Number.isFinite(n)) throw new Error('limit 必须是数字');
  return Math.min(max, Math.max(min, Math.floor(n)));
}

// ---------------------------------------------------------------------------
// 三个工具
// ---------------------------------------------------------------------------
const TOOLS = [
  {
    name: 'daily_today',
    description:
      '今天的日报：按 AI 评分取今日最值得看的条目。只覆盖有 AI 摘要的条目（今天其余条目没有 AI 评分，不参与排名）。',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'integer', description: '返回条数，默认 8，最多 20', default: 8 },
      },
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  },
  {
    name: 'daily_search',
    description: '按关键词搜全站日报（标题 + 摘要）。有摘要的条目排在前面。',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: '关键词，如“黄仁勋”“DeepSeek”“机器人”' },
        limit: { type: 'integer', description: '返回条数，默认 10，最多 20', default: 10 },
        month: { type: 'string', description: '月份 YYYY-MM，默认当月', default: undefined },
      },
      required: ['query'],
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  },
  {
    name: 'daily_signal',
    description:
      '回答第一个问题：今天哪几条值得先动手或先避开，为什么？返回 AI 评分最高的几条及推荐理由；数据里没有“先避开”榜单，不编造。',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'integer', description: '返回条数，默认 5，最多 10', default: 5 },
      },
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  },
];

async function toolToday(args) {
  const limit = clampLimit(args.limit, 8, 1, 20);
  const index = await loadIndex(currentMonth());
  const { date, total, scored, items } = rankedToday(index);
  const reasons = await loadReasons();
  const top = items.slice(0, limit).map((it) => toItem(it, reasons));
  const lines = [
    `## ${date} · 今日情报（共 ${total} 条，其中 ${scored} 条有 AI 摘要与评分）`,
    '排名只覆盖有 AI 摘要的条目；分数为数据原样，未换算。',
    '',
  ];
  if (top.length === 0) {
    lines.push('今天还没有带 AI 摘要的条目，无法按评分排名。');
  } else {
    top.forEach((it, n) => {
      lines.push(`${n + 1}. **${it.score}** [${it.title}](${it.url}) · ${it.platform}`);
      if (it.summary) lines.push(`   ${short(it.summary)}`);
    });
  }
  return { text: lines.join('\n'), data: { date, total, scored, items: top } };
}

async function toolSearch(args) {
  const query = String(args.query || '').trim();
  if (!query) throw new Error('query 不能为空');
  const limit = clampLimit(args.limit, 10, 1, 20);
  let month = typeof args.month === 'string' && args.month.trim() ? args.month.trim() : currentMonth();
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) throw new Error('month 须为真实月份 YYYY-MM，如 2026-11');
  let index;
  try {
    index = await loadIndex(month);
  } catch (err) {
    if (err && err.code === 404) {
      return { text: `${month} 还没有日报索引，没找到含“${query}”的条目。`, data: { month, query, total: 0, items: [] } };
    }
    throw err;
  }
  const q = query.toLowerCase();
  const hits = index.items.filter((it) => {
    const hay = `${it.t || ''} ${it.a || ''}`.toLowerCase();
    return hay.includes(q);
  });
  // 有摘要的在前（摘要意味着有 AI 评分，排得准）；同组内按分、按日期倒序。
  hits.sort((a, b) => {
    const ah = a.a ? 1 : 0;
    const bh = b.a ? 1 : 0;
    if (ah !== bh) return bh - ah;
    return (b.s || 0) - (a.s || 0) || String(b.d || '').localeCompare(String(a.d || ''));
  });
  const reasons = await loadReasons();
  const top = hits.slice(0, limit).map((it) => toItem(it, reasons));
  const lines = [`## 搜索“${query}”（${month}，${hits.length} 条匹配）`, ''];
  if (top.length === 0) {
    lines.push(`在 ${month} 没找到含“${query}”的条目。换个词或换个月份再试。`);
  } else {
    top.forEach((it, n) => {
      lines.push(`${n + 1}. **${it.score}** [${it.title}](${it.url}) · ${it.platform} · ${it.date}`);
      if (it.summary) lines.push(`   ${short(it.summary)}`);
    });
  }
  return { text: lines.join('\n'), data: { month, query, total: hits.length, items: top } };
}

async function toolSignal(args) {
  const limit = clampLimit(args.limit, 5, 1, 10);
  const index = await loadIndex(currentMonth());
  const { date, total, scored, items } = rankedToday(index);
  const reasons = await loadReasons();
  const top = items.slice(0, limit).map((it) => toItem(it, reasons));
  const lines = [
    `## 今天值得先动手（${date}，AI 评分前 ${top.length} 条）`,
    '按 AI 评分排序；推荐理由是管线给的原话，没有的以摘要为准，不编造。',
    '',
  ];
  if (top.length === 0) {
    lines.push('今天还没有带 AI 摘要的条目，无法排出先后。');
  } else {
    top.forEach((it, n) => {
      lines.push(`${n + 1}. **${it.score}** [${it.title}](${it.url}) · ${it.platform}`);
      if (it.reason) lines.push(`   为什么：${short(it.reason, 160)}`);
      else if (it.summary) lines.push(`   摘要：${short(it.summary)}`);
    });
  }
  lines.push(
    '',
    `说明：今天共 ${total} 条，其中 ${scored} 条有 AI 评分，排名只覆盖这 ${scored} 条；“先避开”没有单独榜单——数据里没有这项信号。`,
  );
  return { text: lines.join('\n'), data: { date, total, scored, items: top } };
}

async function callTool(name, args) {
  const a = args && typeof args === 'object' && !Array.isArray(args) ? args : {};
  switch (name) {
    case 'daily_today':
      return toolToday(a);
    case 'daily_search':
      return toolSearch(a);
    case 'daily_signal':
      return toolSignal(a);
    default:
      throw new Error(`未知工具：${name}，可用工具：daily_today / daily_search / daily_signal`);
  }
}

// ---------------------------------------------------------------------------
// JSON-RPC 2.0（Streamable HTTP，无状态；通知只回 202）
// ---------------------------------------------------------------------------
function rpcResult(id, result) {
  return { jsonrpc: '2.0', id, result };
}
function rpcError(id, code, message) {
  return { jsonrpc: '2.0', id, error: { code, message } };
}

function handleInitialize(id, params) {
  const asked = params && typeof params.protocolVersion === 'string' ? params.protocolVersion : '';
  const known = ['2025-03-26', '2025-06-18', '2024-11-05'];
  return rpcResult(id, {
    protocolVersion: known.includes(asked) ? asked : PROTOCOL_VERSION,
    capabilities: { tools: {} },
    serverInfo: { name: SERVER_NAME, version: SERVER_VERSION },
    instructions: INSTRUCTIONS,
  });
}

async function handleRpc(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    return { status: 400, json: rpcError(null, -32600, '请求须为单个 JSON-RPC 2.0 对象，不接受批量') };
  }
  if (body.jsonrpc !== '2.0' || typeof body.method !== 'string') {
    return { status: 400, json: rpcError(body.id ?? null, -32600, '无效的 JSON-RPC 2.0 请求') };
  }
  const isNotification = body.id === undefined || body.id === null;
  if (isNotification) return { status: 202, json: null }; // 通知不回包
  const { id, method, params } = body;
  try {
    switch (method) {
      case 'initialize':
        return { status: 200, json: handleInitialize(id, params) };
      case 'ping':
        return { status: 200, json: rpcResult(id, {}) };
      case 'tools/list':
        return { status: 200, json: rpcResult(id, { tools: TOOLS }) };
      case 'tools/call': {
        const name = params && params.name;
        if (typeof name !== 'string' || !name) {
          return { status: 200, json: rpcError(id, -32602, 'tools/call 须给 name（工具名）') };
        }
        try {
          const { text, data } = await callTool(name, params.arguments);
          return {
            status: 200,
            json: rpcResult(id, {
              content: [{ type: 'text', text }],
              structuredContent: data,
            }),
          };
        } catch (err) {
          // 工具级错误：照 Gary 的做法，ToolError 单独处理，不拖垮端点。
          return {
            status: 200,
            json: rpcResult(id, {
              content: [{ type: 'text', text: `工具执行失败：${err.message || '未知错误'}` }],
              isError: true,
            }),
          };
        }
      }
      default:
        return { status: 200, json: rpcError(id, -32601, `未知方法：${method}`) };
    }
  } catch (err) {
    return { status: 200, json: rpcError(id, -32603, `内部错误：${err.message || '未知错误'}`) };
  }
}

// ---------------------------------------------------------------------------
// HTTP 入口（Pages Functions：onRequest）
// ---------------------------------------------------------------------------
const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Accept, Mcp-Session-Id',
};

function jsonResponse(status, obj) {
  const headers = { 'Content-Type': 'application/json', ...CORS };
  return new Response(obj === null ? null : JSON.stringify(obj), { status, headers });
}

function infoPage() {
  const rows = TOOLS.map(
    (t) => `<li><code>${t.name}</code> — ${t.description}</li>`,
  ).join('\n');
  const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>daily-mcp · 豆子实验室每日情报 MCP</title></head><body style="font-family:system-ui;max-width:640px;margin:40px auto;padding:0 16px;line-height:1.7">
<h1>daily-mcp</h1>
<p>豆子实验室「每日情报」的只读 MCP 端点（Streamable HTTP，无状态，免注册，不用 key）。</p>
<p>MCP 地址：<code>POST /mcp</code>（JSON-RPC 2.0）。在 Claude Code / Codex / Cursor 里填这个地址即可。</p>
<h2>三个工具</h2><ul>${rows}</ul>
<p>数据只读站上公开的 JSON（月索引 + more-today），不碰仓库与管线；每次工具调用最多返回 10 条，约 2–8KB。</p>
<p>站内：<a href="${SITE}/">每日情报</a></p>
</body></html>`;
  return new Response(html, { status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8', ...CORS } });
}

export async function onRequest({ request }) {
  const url = new URL(request.url);
  try {
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS });
    }
    if (url.pathname !== '/mcp') {
      return jsonResponse(404, { jsonrpc: '2.0', id: null, error: { code: -32601, message: `没有这条路：${url.pathname}，MCP 在 POST /mcp` } });
    }
    // GET /mcp：人打开看得到说明页（MCP 客户端只用 POST，不受影响）。
    if (request.method === 'GET') return infoPage();
    if (request.method !== 'POST') {
      return jsonResponse(405, { jsonrpc: '2.0', id: null, error: { code: -32601, message: `不支持 ${request.method}` } });
    }
    let body;
    try {
      body = await request.json();
    } catch {
      return jsonResponse(400, rpcError(null, -32700, '请求体不是合法 JSON'));
    }
    const out = await handleRpc(body);
    return jsonResponse(out.status, out.json);
  } catch (err) {
    return jsonResponse(500, rpcError(null, -32603, `内部错误：${err.message || '未知错误'}`));
  }
}
