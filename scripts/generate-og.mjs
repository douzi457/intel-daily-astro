// OG 分享卡生成器（prebuild 钩子）：每次构建时生成 1200×630 PNG，写入 public/og/（构建产物，不进仓库）。
// 图片永远不经过推送通道，构建时现算。实现：手写 SVG + @resvg/resvg-js 渲染，
// 字体为全量 Noto Sans SC OTF（构建时从 jsdelivr 下载，约 17MB）。
// 不用 satori：实测 satori 对中文的宽度估算错误（右端文字被切出画布、换行错乱），全量字体也一样。
// 失败时写占位图，绝不让构建失败：resvg 纯色占位 → 手写 PNG。
import fs from 'fs';
import os from 'node:os';
import path from 'path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA_ROOT = path.join(ROOT, 'src/data/rewrite/zh');
const OUT_DIR = path.join(ROOT, 'public/og');
const W = 1200;
const H = 630;
const MAX_DAYS = 60;
const FONT_700_URL =
  'https://cdn.jsdelivr.net/gh/notofonts/noto-cjk@main/Sans/SubsetOTF/SC/NotoSansSC-Bold.otf';
const FONT_400_URL =
  'https://cdn.jsdelivr.net/gh/notofonts/noto-cjk@main/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf';
const GARBAGE = /数据不足|未提供具体内容|无法生成|歸藏未提供/;

const C = {
  bg: '#0A0A0A',
  text: '#F5F5F5',
  muted: '#A1A1AA',
  faint: '#71717A',
  accent: '#EA580C',
};

function displayScore(it) {
  const a = it.ai_score;
  return typeof a === 'number' && !Number.isNaN(a) ? a : it.score || 0;
}
function cleanTitle(it) {
  return String(it.ai_title || it.title || '').trim();
}
function fmtDate(d) {
  return `${d.slice(0, 4)}年${parseInt(d.slice(5, 7), 10)}月${parseInt(d.slice(8, 10), 10)}日`;
}
function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function loadDays() {
  const days = [];
  if (!fs.existsSync(DATA_ROOT)) return days;
  for (const f of fs.readdirSync(DATA_ROOT).sort().reverse()) {
    if (!/^\d{4}-\d{2}-\d{2}\.json$/.test(f)) continue;
    try {
      const raw = JSON.parse(fs.readFileSync(path.join(DATA_ROOT, f), 'utf-8'));
      days.push({ date: f.replace('.json', ''), items: raw.items || [], total: (raw.items || []).length });
    } catch {}
  }
  return days;
}

function topItems(day, n) {
  return [...day.items]
    .map((it, idx) => ({ t: cleanTitle(it), s: displayScore(it) }))
    .filter((x) => x.t && !GARBAGE.test(x.t))
    .sort((a, b) => b.s - a.s)
    .slice(0, n);
}

// 宽度估算（只用于 JS 侧断行与 pill 宽度，宁可高估不可低估）：中文 1em，ASCII 约 0.55em
function estWidth(s, fontSize) {
  let w = 0;
  for (const ch of s) {
    w += ch.codePointAt(0) < 128 ? fontSize * 0.55 : fontSize;
  }
  return w;
}

// 贪心断行：最多 maxLines 行，超出的在末行截断加 …
function wrapText(s, fontSize, maxWidth, maxLines) {
  const lines = [''];
  for (const ch of s) {
    if (estWidth(lines[lines.length - 1] + ch, fontSize) > maxWidth) {
      if (lines.length === maxLines) break;
      lines.push('');
    }
    lines[lines.length - 1] += ch;
  }
  const consumed = lines.join('').length;
  if (consumed < s.length) {
    let last = lines[lines.length - 1];
    while (last && estWidth(last + '…', fontSize) > maxWidth) last = last.slice(0, -1);
    lines[lines.length - 1] = last + '…';
  }
  return lines.filter(Boolean);
}

function cardSVG({ dateLabel, headline, score, total, lines, bottomRight }) {
  const hl = wrapText(headline, 46, 1072, 2);
  const afterHeadline = hl.length === 2 ? 267 : 205;
  const p = [];
  p.push(`<rect width="1200" height="630" fill="${C.bg}"/>`);
  p.push(
    `<text x="64" y="92" font-family="Noto Sans SC" font-size="30" font-weight="700" fill="${C.accent}">豆子实验室 · 每日情报</text>`,
  );
  p.push(
    `<text x="1136" y="90" font-family="Noto Sans SC" font-size="26" fill="${C.muted}" text-anchor="end">${esc(dateLabel)}</text>`,
  );
  p.push(`<rect x="64" y="128" width="120" height="4" rx="2" fill="${C.accent}"/>`);
  hl.forEach((ln, i) => {
    p.push(
      `<text x="64" y="${205 + i * 62}" font-family="Noto Sans SC" font-size="46" font-weight="700" fill="${C.text}">${esc(ln)}</text>`,
    );
  });
  let secY;
  if (score != null) {
    const label = `AI 评分 ${score.toFixed(1)}`;
    const pillW = Math.round(estWidth(label, 24) + 36);
    const pillTop = afterHeadline + 38;
    p.push(`<rect x="64" y="${pillTop}" width="${pillW}" height="44" rx="22" fill="${C.accent}"/>`);
    p.push(
      `<text x="${64 + pillW / 2}" y="${pillTop + 30}" font-family="Noto Sans SC" font-size="24" font-weight="700" fill="#FFFFFF" text-anchor="middle">${esc(label)}</text>`,
    );
    p.push(
      `<text x="${64 + pillW + 16}" y="${pillTop + 30}" font-family="Noto Sans SC" font-size="24" fill="${C.faint}">今日 ${total} 条</text>`,
    );
    secY = pillTop + 80;
  } else {
    secY = afterHeadline + 74;
  }
  lines.forEach((t, i) => {
    const y = secY + i * 44;
    p.push(`<rect x="64" y="${y - 9}" width="12" height="12" fill="${C.accent}"/>`);
    p.push(
      `<text x="90" y="${y}" font-family="Noto Sans SC" font-size="25" fill="${C.muted}">${esc(t)}</text>`,
    );
  });
  p.push(
    `<text x="64" y="582" font-family="Noto Sans SC" font-size="24" fill="${C.faint}">daily.dianda.dpdns.org</text>`,
  );
  p.push(
    `<text x="1136" y="582" font-family="Noto Sans SC" font-size="24" fill="${C.faint}" text-anchor="end">${esc(bottomRight)}</text>`,
  );
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">${p.join('')}</svg>`;
}

function dayCard(day) {
  const top = topItems(day, 3);
  if (!top.length) {
    return cardSVG({
      dateLabel: fmtDate(day.date),
      headline: '今日情报正在整理',
      score: null,
      total: day.total,
      lines: ['每天 4 次更新 · AI 评分精选 · 全程可溯源'],
      bottomRight: '精选 · 可溯源',
    });
  }
  return cardSVG({
    dateLabel: fmtDate(day.date),
    headline: top[0].t,
    score: top[0].s,
    total: day.total,
    lines: top.slice(1, 3).map((x) => wrapText(x.t, 25, 1046, 1)[0] || ''),
    bottomRight: '精选 · 可溯源',
  });
}

function defaultCard() {
  return cardSVG({
    dateLabel: 'AI/科技情报站',
    headline: '把 AI 讲成人话',
    score: null,
    total: 0,
    lines: ['每天 4 次更新 · AI 评分精选 · 全程可溯源', '开源 / 大模型 / 数码 / 科技热点'],
    bottomRight: '每天更新',
  });
}

async function fetchFont(url, name) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'og-fonts-'));
  const file = path.join(dir, name);
  let lastErr;
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(60000) });
      if (!res.ok) throw new Error(`font ${res.status}: ${url}`);
      fs.writeFileSync(file, Buffer.from(await res.arrayBuffer()));
      return file;
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr;
}

// 最底层兜底：手写纯色 PNG（黑底 + 顶部橙条），零依赖
function crc32(buf) {
  let table = crc32.table;
  if (!table) {
    table = crc32.table = new Int32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      table[n] = c;
    }
  }
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = table[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, 'ascii'), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body));
  return Buffer.concat([len, body, crc]);
}
function solidPNG() {
  const raw = Buffer.alloc((W * 4 + 1) * H);
  for (let y = 0; y < H; y++) {
    raw[y * (W * 4 + 1)] = 0;
    for (let x = 0; x < W; x++) {
      const o = y * (W * 4 + 1) + 1 + x * 4;
      if (y < 8) {
        raw[o] = 0xea;
        raw[o + 1] = 0x58;
        raw[o + 2] = 0x0c;
      } else {
        raw[o] = 0x0a;
        raw[o + 1] = 0x0a;
        raw[o + 2] = 0x0a;
      }
      raw[o + 3] = 0xff;
    }
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(W, 0);
  ihdr.writeUInt32BE(H, 4);
  ihdr[8] = 8;
  ihdr[9] = 6;
  const sig = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  return Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}

function placeholderSVG() {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><rect width="${W}" height="${H}" fill="${C.bg}"/><rect width="${W}" height="8" fill="${C.accent}"/></svg>`;
}

function writeSet(png) {
  const days = loadDays().slice(0, MAX_DAYS);
  fs.writeFileSync(path.join(OUT_DIR, 'default.png'), png);
  for (const d of days) fs.writeFileSync(path.join(OUT_DIR, `${d.date}.png`), png);
  if (days.length) fs.copyFileSync(path.join(OUT_DIR, `${days[0].date}.png`), path.join(OUT_DIR, 'today.png'));
  else fs.writeFileSync(path.join(OUT_DIR, 'today.png'), png);
  return days.length;
}

const days = loadDays();
fs.mkdirSync(OUT_DIR, { recursive: true });
try {
  const [f700, f400] = await Promise.all([
    fetchFont(FONT_700_URL, 'NotoSansSC-Bold.otf'),
    fetchFont(FONT_400_URL, 'NotoSansSC-Regular.otf'),
  ]);
  const { Resvg } = await import('@resvg/resvg-js');
  const opts = {
    font: { fontFiles: [f700, f400], loadSystemFonts: false, defaultFontFamily: 'Noto Sans SC' },
    fitTo: { mode: 'width', value: W },
  };
  const render = (svg) => new Resvg(svg, opts).render().asPng();
  fs.writeFileSync(path.join(OUT_DIR, 'default.png'), render(defaultCard()));
  let n = 0;
  for (const day of days.slice(0, MAX_DAYS)) {
    fs.writeFileSync(path.join(OUT_DIR, `${day.date}.png`), render(dayCard(day)));
    n++;
  }
  if (days.length) fs.copyFileSync(path.join(OUT_DIR, `${days[0].date}.png`), path.join(OUT_DIR, 'today.png'));
  else fs.copyFileSync(path.join(OUT_DIR, 'default.png'), path.join(OUT_DIR, 'today.png'));
  console.log(`[og] rendered ${n} day cards + today + default`);
} catch (e) {
  console.warn('[og] full render failed, writing placeholders:', e.message);
  try {
    const { Resvg } = await import('@resvg/resvg-js');
    const png = new Resvg(placeholderSVG(), { fitTo: { mode: 'width', value: W } }).render().asPng();
    const n = writeSet(png);
    console.log(`[og] wrote ${n} placeholder cards (resvg, no text)`);
  } catch (e2) {
    const n = writeSet(solidPNG());
    console.log(`[og] wrote ${n} placeholder cards (solid PNG, no deps)`);
  }
}
