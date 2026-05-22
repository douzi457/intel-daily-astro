#!/usr/bin/env python3
"""生成情报中心 v3.0 — 侧边栏 + 仪表盘布局"""
import json, os, re
from datetime import datetime

# ── 加载数据 ──────────────────────────────────────────────
data_file = os.path.join(os.path.dirname(__file__), 'intelligence_data.json')
with open(data_file, 'r', encoding='utf-8') as f:
    raw = json.load(f)

items = raw['items']
last_update = raw['last_update']
update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
update_str = update_dt.strftime('%Y-%m-%d %H:%M')

# ── 来源配置 ──────────────────────────────────────────────
SOURCE_NAMES = {
    'gzh':'公众号','weibo':'微博','douyin':'抖音',
    'hackernews':'HackerNews','github':'GitHub',
    'producthunt':'Product Hunt','36kr':'36Kr',
    'wallstreetcn':'华尔街见闻','v2ex':'V2EX',
    'tencent':'腾讯新闻','ithome':'IT之家',
    'toutiao':'今日头条','bilibili':'B站',
    'chuangye':'创业邦','sspai':'少数派',
    'news_aggregator':'科技新闻','unknown':'其他',
}
SOURCE_EMOJI = {
    'gzh':'📖','weibo':'','douyin':'',
    'hackernews':'🔥','github':'⚙️',
    'producthunt':'🌟','36kr':'📰',
    'wallstreetcn':'💹','v2ex':'💬',
    'tencent':'','ithome':'🖥️',
    'toutiao':'📡','bilibili':'',
    'chuangye':'🚀','sspai':'⚡',
    'news_aggregator':'📡','unknown':'❓',
}
SOURCE_COLORS = {
    'gzh':   ('#FF6B6B','#FFF0F0'),
    'weibo': ('#FF9500','#FFF5E6'),
    'douyin':('#00F2EA','#E6FFFD'),
    'hackernews':('#FF6600','#FFF5E6'),
    'github':    ('#4ECDC4','#E8F8F5'),
    'producthunt':('#FF6B35','#FFF0ED'),
    '36kr':      ('#2B8CFF','#EBF5FF'),
    'wallstreetcn':('#5856D6','#EEEEFF'),
    'v2ex':      ('#584528','#FDF6EC'),
    'tencent':   ('#E43961','#FFEEF2'),
    'ithome':    ('#0090D8','#E6F6FF'),
    'toutiao':   ('#E60023','#FFE6E6'),
    'bilibili':  ('#FB7299','#FFF0F5'),
    'chuangye':  ('#F5A623','#FFF8E6'),
    'sspai':     ('#4CAF50','#E8F5E9'),
    'news_aggregator':('#4ECDC4','#E8F8F5'),
    'unknown':   ('#95A5A6','#F5F5F5'),
}

# GitHub 项目简介中译
GITHUB_DESC_ZH = {
    'ollama': '运行开源大模型的本地工具，Llama/Mistral/Gemma等模型一键部署',
    'open-webui': '网页端UI，调用本地Ollama或OpenAI API，支持多用户和知识库',
    'anything-llm': '私有AI知识库，支持多文档格式，多LLM后端',
    'fastgpt': '可视化AI知识库问答系统，支持工作流编排',
    'maxkb': '开源知识库问答系统，基于RAG，支持快速部署',
    'n8n': '开源工作流自动化，连接API/数据库/AI服务',
    'difrank': '本地文档问答工具，支持多格式，RAG检索增强',
    'pulsar经纪商': '消息队列平台',
    'kafka': '分布式流处理平台',
    'dify': '开源LLM应用开发平台，拖拽式AI工作流，支持RAG',
    'one-api': '聚合多种AI API的统一接口，支持Key管理和用量统计',
    'tabby': '开源AI代码补全服务器，自托管，兼容VSCode/TAB',
    'continue': 'IDE中集成AI代码助手，支持多种LLM和RAG上下文',
    'go-cqhttp': 'QQ机器人框架，支持多种协议',
    ' LagerCron': '定时任务管理系统',
    'DocAsk': '上传文档，AI回答关于文档的问题',
    'claude-code': 'Anthropic官方CLI工具，用AI写代码、跑测试、改bug',
    'bolt': 'AI网页应用开发框架，描述需求自动生成完整项目',
    'bolt.new': 'StackBlitz上的AI开发环境，即开即用',
    'reliable-man': 'Humanloop创始人新项目',
    'A': '一个简洁的AI项目',
    'cursor': 'AI代码编辑器，基于VSCode，Tab智能补全',
    ' Windsurf': 'Codeium推出的AI IDE，支持工作流',
    'Github': 'GitHub官方App，代码审查和项目管理',
    'vscode': '微软开源代码编辑器',
    'Codeium': '免费AI代码补全，替代Copilot',
    'Continue': '开源AI代码助手，兼容多种LLM',
    ' Supermaven': 'AI代码补全，速度极快，支持上下文',
    'figma': 'UI设计工具，实时协作',
    'Notion': '笔记和知识库平台',
    'Linear': '软件项目管理系统',
    'Vercel': '前端部署平台',
    'Supabase': '开源Firebase替代，后端即服务',
    'Railway': '云端应用部署平台',
    'Render': '云端应用托管服务',
    'Fly.io': '边缘计算平台',
    'Cloudflare': 'CDN和网络服务商',
    'Tailscale': 'WireGuard组网工具，内网穿透',
    'Ngrok': '内网穿透工具，快速暴露本地服务',
    'P tunnel': '内网穿透工具',
}

def zh_desc(text, fallback=''):
    """将英文关键词翻译为中文，找不到则返回原文"""
    if not text:
        return fallback
    t = text.strip()
    for kw, val in GITHUB_DESC_ZH.items():
        if kw.lower() in t.lower():
            return val
    return t

def get_source(item):
    os_ = item.get('original_source', '')
    if os_ in SOURCE_NAMES:
        return os_
    return item.get('source_type', 'unknown')

def get_score(item):
    hot = item.get('hot_value', 0)
    score = item.get('score', 0)
    heat = item.get('heat', '')
    freq = item.get('frequency', 1)
    val = hot or score or 0
    if hot and hot > 1000000:
        val = hot / 10000
    return val * freq

def fmt_val(v):
    if v >= 10000:
        return f'{v/10000:.1f}万'
    if v >= 1000:
        return f'{v/1000:.1f}k'
    if isinstance(v, float) and v < 100:
        return f'{v:.1f}'
    return str(int(v)) if v else '0'

def build_item(item, is_list=False):
    """生成单条情报的HTML片段"""
    src = get_source(item)
    name = SOURCE_NAMES.get(src, src)
    emoji = SOURCE_EMOJI.get(src, '📌')
    color, bg = SOURCE_COLORS.get(src, ('#999','#F5F5F5'))
    title = item.get('title', '无标题')
    desc = item.get('desc', '')
    url = item.get('url', '')
    val = get_score(item)

    # GitHub项目简介汉化
    if src == 'github' and desc:
        desc = zh_desc(desc, desc)

    if desc and len(desc) > 120:
        desc = desc[:120].rsplit('，',1)[0] + '…'

    t = item.get('time','')
    if 'T' in t:
        t = t.split('T')[1][:5]

    title_html = f'<a href="{url}" target="_blank">{title}</a>' if url else title

    if is_list:
        # 紧凑列表行（微博/抖音风格）
        return f'''<li class="vrow" data-src="{src}">
  <span class="vsrc" style="background:{bg};color:{color}">{emoji}</span>
  <span class="vtitle">{title_html}</span>
  <span class="vheat">🔥 {fmt_val(val)}</span>
  {f'<span class="vtime">{t}</span>' if t else ''}
</li>'''
    else:
        # 卡片（大来源：公众号/科技新闻）
        return f'''<div class="mcard" data-src="{src}">
  <div class="mhead">
    <span class="mbdg" style="background:{bg};color:{color}">{emoji}{name}</span>
    {f'<span class="mtime">{t}</span>' if t else ''}
  </div>
  <div class="mtitle">{title_html}</div>
  {f'<div class="mdesc">{desc}</div>' if desc else ''}
  <div class="mfoot"><span class="mheat">🔥 {fmt_val(val)}</span></div>
</div>'''

# ── 分类 ───────────────────────────────────────────────────
video_items = [i for i in items if get_source(i) in ('douyin','weibo','bilibili')]
card_items  = [i for i in items if get_source(i) not in ('douyin','weibo','bilibili')]

# 热度排序
video_items.sort(key=get_score, reverse=True)
card_items.sort(key=get_score, reverse=True)

video_html = '\n'.join(build_item(i, is_list=True) for i in video_items)
card_html  = '\n'.join(build_item(i, is_list=False) for i in card_items)

# ── 侧边栏统计 ──────────────────────────────────────────────
from collections import Counter
src_cnt = Counter(get_source(i) for i in items)
sidebar_items = []
for src, cnt in src_cnt.most_common():
    name = SOURCE_NAMES.get(src, src)
    emoji = SOURCE_EMOJI.get(src, '📌')
    color, bg = SOURCE_COLORS.get(src, ('#999','#F5F5F5'))
    sidebar_items.append(
        f'<div class="sitem" data-f="{src}">'
        f'<span class="sdot" style="background:{color}"></span>'
        f'<span class="slabel">{emoji}{name}</span>'
        f'<span class="scnt">{cnt}</span>'
        f'</div>'
    )
sidebar_html = '\n'.join(sidebar_items)

# ── JS ─────────────────────────────────────────────────────
FILTER_JS = '''
const sitems = document.querySelectorAll('.sitem');
const mgrid  = document.getElementById('mgrid');
const vlist  = document.getElementById('vlist');
const mtotal = document.getElementById('mtotal');
const vtotal = document.getElementById('vtotal');
const qinput = document.getElementById('q');
let cur = 'all', q = '';

function apply(){
  let mc=0, vc=0;
  // 卡片区
  mgrid.querySelectorAll('.mcard').forEach(el=>{
    const ok = (cur==='all'||el.dataset.src===cur) && (!q||el.textContent.toLowerCase().includes(q));
    el.style.display=ok?'':'none';
    if(ok) mc++;
  });
  // 视频区
  vlist.querySelectorAll('.vrow').forEach(el=>{
    const ok = (cur==='all'||el.dataset.src===cur) && (!q||el.textContent.toLowerCase().includes(q));
    el.style.display=ok?'':'none';
    if(ok) vc++;
  });
  mtotal.textContent=mc; vtotal.textContent=vc;
}
sitems.forEach(it=>{
  it.onclick=()=>{
    sitems.forEach(s=>s.classList.remove('on'));
    it.classList.add('on');
    cur=it.dataset.f;
    apply();
  };
});
qinput.oninput=e=>{ q=e.target.value.toLowerCase(); apply(); };
'''

# ── 完整HTML ─────────────────────────────────────────────────
html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>情报中心 v3.0</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --bg:#0d0f14;--sidebar:#13161e;--sur:#181c26;
  --sur2:#1e2330;--bd:#2a3044;--tx:#dde3ed;
  --tx2:#7e8aa4;--acc:#4ECDC4;--hot:#FF9500;
  --f:system-ui,-apple-system,'Segoe UI',sans-serif;
}}
html,body{{height:100%;overflow:hidden}}
body{{background:var(--bg);color:var(--tx);font-family:var(--f)}}

/* ── 整体三栏 ── */
.layout{{display:flex;height:100vh}}
/* ── 侧边栏 ── */
aside{{width:200px;min-width:200px;background:var(--sidebar);
  border-right:1px solid var(--bd);display:flex;flex-direction:column;overflow-y:auto}}
.logo{{padding:18px 18px 14px;font-size:16px;font-weight:800;color:var(--acc);
  border-bottom:1px solid var(--bd);flex-shrink:0}}
.logo span{{display:block;font-size:11px;color:var(--tx2);font-weight:400;margin-top:2px}}
.ssrc{{padding:10px 14px 6px;font-size:10px;color:var(--tx2);text-transform:uppercase;letter-spacing:1px}}
.sitems{{padding:0 10px 10px;flex:1}}
.sitem{{display:flex;align-items:center;gap:8px;padding:7px 8px;
  border-radius:8px;cursor:pointer;transition:.15s;font-size:13px}}
.sitem:hover{{background:var(--sur2)}}
.sitem.on{{background:var(--sur2);box-shadow:inset 2px 0 0 var(--acc)}}
.sdot{{width:7px;height:7px;border-radius:50%;flex-shrink:0}}
.slabel{{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.scnt{{background:var(--bd);color:var(--tx2);font-size:11px;padding:1px 6px;border-radius:10px}}

/* ── 主内容 ── */
main{{flex:1;overflow-y:auto;padding:18px 22px;display:flex;flex-direction:column;gap:22px}}

/* 搜索 */
.sbar{{display:flex;gap:10px;align-items:center;flex-shrink:0}}
.sbar input{{flex:1;max-width:400px;padding:9px 14px;background:var(--sur);
  border:1px solid var(--bd);border-radius:10px;color:var(--tx);
  font-size:14px;outline:none}}
.sbar input:focus{{border-color:var(--acc)}}
.sbar .hint{{font-size:12px;color:var(--tx2)}}

/* 区块标题 */
.sec-hd{{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-shrink:0}}
.sec-hd h2{{font-size:14px;font-weight:700;color:var(--tx)}}
.cnt-pill{{background:var(--sur2);color:var(--tx2);font-size:12px;padding:2px 9px;border-radius:10px}}

/* 卡片网格（公众号/科技） */
.mgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px}}
.mcard{{background:var(--sur);border:1px solid var(--bd);border-radius:12px;
  padding:13px;display:flex;flex-direction:column;gap:7px;transition:.2s}}
.mcard:hover{{border-color:var(--acc);box-shadow:0 4px 16px rgba(78,205,196,.08)}}
.mhead{{display:flex;justify-content:space-between;align-items:center}}
.mbdg{{padding:3px 9px;border-radius:20px;font-size:11px;font-weight:700}}
.mtime{{font-size:11px;color:var(--tx2)}}
.mtitle{{font-size:14px;font-weight:600;line-height:1.5}}
.mtitle a{{color:var(--tx);text-decoration:none}}
.mtitle a:hover{{color:var(--acc)}}
.mdesc{{font-size:13px;color:var(--tx2);line-height:1.65}}
.mfoot{{margin-top:auto}}
.mheat{{font-size:12px;color:var(--hot)}}

/* 视频竖排列表（微博/抖音/ B站） */
.vlist-wrap{{background:var(--sur);border:1px solid var(--bd);border-radius:12px;overflow:hidden}}
.vrow{{display:flex;align-items:center;gap:10px;padding:10px 14px;
  border-bottom:1px solid var(--bd);transition:.15s}}
.vrow:last-child{{border-bottom:none}}
.vrow:hover{{background:var(--sur2)}}
.vsrc{{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:13px;flex-shrink:0}}
.vtitle{{flex:1;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.vtitle a{{color:var(--tx);text-decoration:none}}
.vtitle a:hover{{color:var(--acc)}}
.vheat{{font-size:12px;color:var(--hot);min-width:55px;text-align:right}}
.vtime{{font-size:11px;color:var(--tx2);min-width:38px}}

footer{{text-align:center;padding:20px;color:var(--tx2);font-size:11px;border-top:1px solid var(--bd);
  margin-top:auto;flex-shrink:0}}

@media(max-width:768px){{
  .layout{{flex-direction:column;height:auto;overflow:auto}}
  aside{{width:100%;min-width:unset;border-right:none;border-bottom:1px solid var(--bd);max-height:220px}}
  .mgrid{{grid-template-columns:1fr}}
}}
</style>
</head>
<body>
<div class="layout">

<!-- 侧边栏 -->
<aside>
  <div class="logo">🧠 情报中心<span>v3.0 · {len(items)}条</span></div>
  <div class="ssrc">数据来源</div>
  <div class="sitems">
    <div class="sitem on" data-f="all">
      <span class="sdot" style="background:#4ECDC4"></span>
      <span class="slabel">📌 全部</span>
      <span class="scnt">{len(items)}</span>
    </div>
    {sidebar_html}
  </div>
</aside>

<!-- 主内容 -->
<main>
  <div class="sbar">
    <input id="q" type="text" placeholder=" 搜索标题、描述…" autocomplete="off">
    <span class="hint">📅 {update_str}</span>
  </div>

  <!-- 竖排视频区 -->
  {f'''<section>
  <div class="sec-hd">
    <h2> 抖音 ·  微博 ·  B站</h2>
    <span class="cnt-pill" id="vtotal">{len(video_items)}</span>
  </div>
  <div class="vlist-wrap" id="vlist">{video_html}
  </div>
  </section>''' if video_items else ''}

  <!-- 卡片区 -->
  {f'''<section>
  <div class="sec-hd">
    <h2>📝 公众号 · 💻 科技 · ⚙️ 开源</h2>
    <span class="cnt-pill" id="mtotal">{len(card_items)}</span>
  </div>
  <div class="mgrid" id="mgrid">{card_html}
  </div>
  </section>''' if card_items else ''}

  <footer>情报中心 v3.0</footer>
</main>
</div>
<script>{FILTER_JS}</script>
</body>
</html>'''

out = os.path.join(os.path.dirname(__file__), '情报中心.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'✅ 生成: {out}')
print(f'   视频竖排: {len(video_items)} 条')
print(f'   卡片区:   {len(card_items)} 条')
