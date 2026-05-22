#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""情报中心 gen.py v4 - 侧边栏主次 + 汉化 + header"""
import json, os
from datetime import datetime
from collections import Counter

p = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(p, "intelligence_data.json"), "r", encoding="utf-8") as f:
    raw = json.load(f)
items = raw["items"]
ts = raw["last_update"]
ust = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")

N = {
    "gzh": "公众号", "weibo": "微博", "douyin": "抖音",
    "hackernews": "HackerNews", "github": "GitHub",
    "producthunt": "ProductHunt", "36kr": "36Kr",
    "wallstreetcn": "华尔街见闻", "v2ex": "V2EX",
    "tencent": "腾讯新闻", "ithome": "IT之家",
    "toutiao": "今日头条", "bilibili": "B站",
    "chuangye": "创业邦", "sspai": "少数派",
    "news_aggregator": "综合新闻", "unknown": "其他",
}

# 优先级排序：最能帮赚钱的来源排前面（不是按数据量）
PRI = [
    "gzh", "36kr", "v2ex", "weibo",
    "wallstreetcn", "sspai", "ithome", "chuangye",
    "producthunt", "github", "hackernews",
    "bilibili", "toutiao", "tencent",
    "news_aggregator", "douyin", "unknown"
]

def gs(i):
    """Get source key, fix items with empty original_source"""
    u = i.get("url", "")
    if "github.com" in u:
        return "github"
    if "sspai.com" in u:
        return "sspai"
    o = i.get("original_source", "")
    if o in N:
        return o
    st = i.get("source_type", "unknown")
    if st in N:
        return st
    return "unknown"

def gv(i):
    h = i.get("hot_value", 0)
    s = i.get("score", 0)
    f = i.get("frequency", 1)
    return (h or s or 0) * f

def fv(v):
    if v >= 10000:
        return "%.1fW" % (v / 10000)
    if v >= 1000:
        return "%.1fk" % (v / 1000)
    return str(int(v)) if v else "0"

# 视频来源
VS = ("douyin", "weibo", "bilibili")
video = sorted([i for i in items if gs(i) in VS], key=gv, reverse=True)
cards = sorted([i for i in items if gs(i) not in VS], key=gv, reverse=True)

# 颜色
C = {}
pairs = [
    ("gzh", "#FF6B6B", "#FFF0F0"), ("weibo", "#FF9500", "#FFF5E6"),
    ("douyin", "#00F2EA", "#E6FFFD"), ("hackernews", "#FF6600", "#FFF5E6"),
    ("github", "#4ECDC4", "#E8F8F5"), ("producthunt", "#FF6B35", "#FFF0ED"),
    ("36kr", "#2B8CFF", "#EBF5FF"), ("wallstreetcn", "#5856D6", "#EEEEFF"),
    ("v2ex", "#584528", "#FDF6EC"), ("tencent", "#E43961", "#FFEEF2"),
    ("ithome", "#0090D8", "#E6F6FF"), ("toutiao", "#E60023", "#FFE6E6"),
    ("bilibili", "#FB7299", "#FFF0F5"), ("chuangye", "#F5A623", "#FFF8E6"),
    ("sspai", "#4CAF50", "#E8F5E9"), ("news_aggregator", "#607D8B", "#ECEFF1"),
    ("unknown", "#95A5A6", "#F5F5F5"),
]
for k, c, b in pairs:
    C[k] = (c, b)

# GitHub 项目中文描述
GH_ZH = {
    "ollama": "本地 LLM 运行平台，Ollama/Mistral 等模型一键部署，开源免费",
    "open-webui": "Ollama 的 Web 界面，支持多用户、知识库检索",
    "anything-llm": "私有 AI 知识库，支持多格式文档、多 LLM 后端接入",
    "fastgpt": "可视化 AI 知识库问答，工作流编排引擎",
    "maxkb": "开源知识库问答系统，RAG 模式，部署简单",
    "n8n": "开源工作流自动化，连接 API / 数据库 / AI 服务",
    "difrank": "本地文档 AI 问答，多格式支持，RAG 检索",
    "dify": "开源 LLM 应用平台，拖拽式 AI 工作流构建",
    "one-api": "统一 AI API 网关，支持密钥管理与调用统计",
    "tabby": "自托管 AI 代码补全，Tab 键友好兼容",
    "continue": "IDE 内 AI 编程助手，RAG 检索上下文",
    "claude-code": "Anthropic 官方 CLI 编程工具，可生成 / 测试 / 调试代码",
    "bolt": "AI 网页应用开发框架，描述即可生成完整项目",
    "cursor": "AI 代码编辑器，支持 TAB 智能补全",
    "Windsurf": "Codeium AI IDE，支持工作流编排",
    "Codeium": "免费 AI 代码补全，Copilot 替代品",
    "go-cqhttp": "QQ 机器人框架，支持多协议接入",
    "Supabase": "开源 Firebase 替代，数据库 + 认证 + API",
    "gpt-sovits": "AI 声音克隆工具，5秒音频即可克隆音色",
    "rvc": "语音转换模型，实时变声器",
    "open-webui": "Ollama Web UI，支持多用户和知识库",
    "gpt4": "OpenAI GPT-4 模型接口",
    "o1": "OpenAI o1 推理模型",
    "o3": "OpenAI o3 推理模型",
    "gemini": "Google Gemini 多模态模型",
    "claude": "Anthropic Claude 模型",
    "localai": "本地 AI 模型推理，支持 OpenAI 兼容 API",
}

def zh(item):
    """获取中文描述（GitHub 项目）"""
    t = item.get("title", "")
    d = item.get("desc", "")
    combined = (t + " " + d).lower()
    for k, v in GH_ZH.items():
        if k.lower() in combined:
            return v
    return d.strip() if d else ""

def mcard(item):
    s = gs(item)
    n = N.get(s, s)
    co, bg = C.get(s, ("#999", "#F5F5F5"))
    t = item.get("title", "No title")
    d = zh(item)
    u = item.get("url", "")
    val = gv(item)
    if d and len(d) > 120:
        d = d[:120].rsplit(" ", 1)[0] + "..."
    a = '<a href="%s" target="_blank">%s</a>' % (u, t) if u else t
    dtHtml = '<div class="mdesc">%s</div>' % d if d else ""
    tt = item.get("time", "")
    vtHtml = '<span class="mtime">%s</span>' % tt.split("T")[1][:5] if "T" in tt else ""
    return '<div class="mcard" data-src="%s"><div class="mhead"><span class="mbdg" style="background:%s;color:%s">%s</span>%s</div><div class="mtitle">%s</div>%s<div class="mfoot"><span class="mheat">%s</span></div></div>' % (s, bg, co, n, vtHtml, a, dtHtml, fv(val))

def vrow(item):
    s = gs(item)
    n = N.get(s, s)
    co, bg = C.get(s, ("#999", "#F5F5F5"))
    t = item.get("title", "No title")
    u = item.get("url", "")
    val = gv(item)
    tt = item.get("time", "")
    a = '<a href="%s" target="_blank">%s</a>' % (u, t) if u else t
    vt = '<span class="vtime">%s</span>' % tt.split("T")[1][:5] if "T" in tt else ""
    return '<li class="vrow" data-src="%s"><span class="vsrc" style="background:%s;color:%s">%s</span><span class="vtitle">%s</span><span class="vheat">%s</span>%s</li>' % (s, bg, co, n, a, fv(val), vt)

vhtml = "".join(vrow(i) for i in video)
chtml = "".join(mcard(i) for i in cards)

# 来源计数，按优先级排序
src_cnt = Counter(gs(i) for i in items)
ordered = sorted(src_cnt.keys(), key=lambda k: PRI.index(k) if k in PRI else 999)
# 主要来源（价值最高）加红色 ! 标记
TOP_KEYS = {"gzh", "36kr", "v2ex", "weibo", "wallstreetcn"}
shtml = ""
for k in ordered:
    v = src_cnt[k]
    n = N.get(k, k)
    co, bg = C.get(k, ("#999", "#F5F5F5"))
    top_mark = ' <span class="topmark">!</span>' if k in TOP_KEYS else ""
    shtml += '<div class="sitem" data-f="%s"><span class="sdot" style="background:%s"></span><span class="slabel">%s%s</span><span class="scnt">%s</span></div>' % (k, co, n, top_mark, v)

# 顶部统计数据（按PRI取前4个有数据的源）
top_srcs = [(k, src_cnt[k]) for k in PRI if k in src_cnt][:4]
stats_html = "".join('<div class="stat"><div class="stat-n">%d</div><div class="stat-l">%s</div></div>' % (v, N.get(k, k)) for k, v in top_srcs)

JS = """
var cur='all',q='';
function apply(){
  var mc=0,vc=0;
  document.querySelectorAll('#mgrid .mcard').forEach(function(el){
    var ok=(cur==='all'||el.dataset.src===cur)&&(!q||el.textContent.toLowerCase().indexOf(q)>-1);
    el.style.display=ok?'':'none';
    if(ok)mc++;
  });
  document.querySelectorAll('#vlist .vrow').forEach(function(el){
    var ok=(cur==='all'||el.dataset.src===cur)&&(!q||el.textContent.toLowerCase().indexOf(q)>-1);
    el.style.display=ok?'':'none';
    if(ok)vc++;
  });
  document.getElementById('mtotal').textContent=mc;
  document.getElementById('vtotal').textContent=vc;
}
document.querySelectorAll('.sitem').forEach(function(it){
  it.onclick=function(){
    document.querySelectorAll('.sitem').forEach(function(s){s.classList.remove('on')});
    it.classList.add('on');
    cur=it.dataset.f;
    apply();
  };
});
document.getElementById('q').oninput=function(e){q=e.target.value.toLowerCase();apply();};
"""

vsec = ('<section><div class="sec-hd"><h2>视频媒体</h2><span class="cnt-p" id="vtotal">%d</span></div><div class="vlist" id="vlist">%s</div></section>' % (len(video), vhtml)) if video else ''
csec = ('<section><div class="sec-hd"><h2>全部内容</h2><span class="cnt-p" id="mtotal">%d</span></div><div class="mgrid" id="mgrid">%s</div></section>' % (len(cards), chtml)) if cards else ''

CSS = """
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0d0f14;--sb:#13161e;--su:#181c26;--s2:#1e2330;--bd:#2a3044;--tx:#dde3ed;--tx2:#7e8aa4;--ac:#4ECDC4;--ht:#FF9500;--f:system-ui,sans-serif}
html,body{height:100%;overflow:hidden}
body{background:var(--bg);color:var(--tx);font-family:var(--f)}
.lay{display:flex;height:100vh}
aside{width:210px;min-width:210px;background:var(--sb);border-right:1px solid var(--bd);display:flex;flex-direction:column;overflow-y:auto}
.logo{padding:18px 16px 14px;border-bottom:1px solid var(--bd)}
.logo-title{font-size:16px;font-weight:900;color:var(--ac);letter-spacing:1px}
.logo-sub{font-size:10px;color:var(--tx2);margin-top:3px}
.logo-stats{display:flex;gap:8px;margin-top:10px}
.stat{background:var(--su);border:1px solid var(--bd);border-radius:8px;padding:7px 10px;flex:1;text-align:center}
.stat-n{font-size:17px;font-weight:800;color:var(--tx)}
.stat-l{font-size:9px;color:var(--tx2);margin-top:2px}
.ssrc{padding:12px 14px 4px;font-size:9px;color:var(--tx2);letter-spacing:1px}
.sitems{padding:0 10px 10px;flex:1}
.sitem{display:flex;align-items:center;gap:7px;padding:6px 8px;border-radius:7px;cursor:pointer;transition:.15s;font-size:13px}
.sitem:hover{background:var(--s2)}
.sitem.on{background:var(--s2);box-shadow:inset 2px 0 0 var(--ac)}
.sdot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.slabel{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.scnt{background:var(--bd);color:var(--tx2);font-size:11px;padding:1px 6px;border-radius:10px}
.topmark{font-size:9px;background:var(--ac);color:#000;border-radius:3px;padding:0 3px;margin-left:2px;font-weight:700}
main{flex:1;overflow-y:auto;padding:18px 22px;display:flex;flex-direction:column;gap:22px}
.sbar{display:flex;gap:10px;align-items:center;flex-shrink:0}
.sbar input{flex:1;max-width:400px;padding:9px 14px;background:var(--su);border:1px solid var(--bd);border-radius:10px;color:var(--tx);font-size:14px;outline:none}
.sbar input:focus{border-color:var(--ac)}
.sbar .hint{font-size:11px;color:var(--tx2)}
.sec-hd{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-shrink:0}
.sec-hd h2{font-size:14px;font-weight:700}
.cnt-p{background:var(--s2);color:var(--tx2);font-size:12px;padding:2px 9px;border-radius:10px}
.mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px}
.mcard{background:var(--su);border:1px solid var(--bd);border-radius:12px;padding:13px;display:flex;flex-direction:column;gap:7px;transition:.2s}
.mcard:hover{border-color:var(--ac);box-shadow:0 4px 16px rgba(78,205,196,.08)}
.mhead{display:flex;justify-content:space-between;align-items:center}
.mbdg{padding:3px 9px;border-radius:20px;font-size:11px;font-weight:700}
.mtime{font-size:11px;color:var(--tx2)}
.mtitle{font-size:14px;font-weight:600;line-height:1.5}
.mtitle a{color:var(--tx);text-decoration:none}
.mtitle a:hover{color:var(--ac)}
.mdesc{font-size:13px;color:var(--tx2);line-height:1.65}
.mfoot{margin-top:auto}
.mheat{font-size:12px;color:var(--ht)}
.vlist{background:var(--su);border:1px solid var(--bd);border-radius:12px;overflow:hidden}
.vrow{display:flex;align-items:center;gap:10px;padding:10px 14px;border-bottom:1px solid var(--bd);transition:.15s}
.vrow:last-child{border-bottom:none}
.vrow:hover{background:var(--s2)}
.vsrc{padding:3px 8px;border-radius:20px;font-size:11px;font-weight:700;min-width:80px;text-align:center}
.vtitle{flex:1;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.vtitle a{color:var(--tx);text-decoration:none}
.vtitle a:hover{color:var(--ac)}
.vheat{font-size:12px;color:var(--ht);min-width:55px;text-align:right}
.vtime{font-size:11px;color:var(--tx2);min-width:38px}
footer{text-align:center;padding:20px;color:var(--tx2);font-size:11px;border-top:1px solid var(--bd);margin-top:auto;flex-shrink:0}
@media(max-width:768px){.lay{flex-direction:column;height:auto;overflow:auto}aside{width:100%;min-width:unset;border-right:none;border-bottom:1px solid var(--bd);max-height:220px}.mgrid{grid-template-columns:1fr}}
</style>
"""

HTML = (
    '<!DOCTYPE html><html lang="zh"><head>'
    '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
    '<title>情报中心</title>' + CSS + '</head><body>'
    '<div class="lay">'
    '<aside>'
    '<div class="logo">'
    '<div class="logo-title">情报中心</div>'
    '<div class="logo-sub">采集源头 · ' + ust + '</div>'
    '<div class="logo-stats">' + stats_html + '</div>'
    '</div>'
    '<div class="ssrc">数据源</div>'
    '<div class="sitems">'
    '<div class="sitem on" data-f="all"><span class="sdot" style="background:#4ECDC4"></span><span class="slabel">全部</span><span class="scnt">' + str(len(items)) + '</span></div>'
    + shtml
    + '</div>'
    '</aside>'
    '<main>'
    '<div class="sbar">'
    '<input id="q" type="text" placeholder="搜索标题、描述..." autocomplete="off">'
    '<span class="hint">最远更新: ' + ust + '</span>'
    '</div>'
    + vsec + csec
    + '<footer>情报中心 v4</footer>'
    '</main>'
    '</div>'
    '<script>' + JS.strip() + '</script>'
    '</body></html>'
)

out = os.path.join(p, "intel.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print("Done:", out)
print("Video:", len(video), "Cards:", len(cards))
src_dist = dict(Counter(gs(i) for i in items))
print("Sources:", {N.get(k,k): v for k, v in src_dist.items()})
