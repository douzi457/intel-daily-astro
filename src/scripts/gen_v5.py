<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>情报中心 v5</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0a0c10;
  --top:#0f1117;
  --bar:#14171f;
  --card:#13161d;
  --border:#1e2330;
  --text:#dde3ed;
  --sub:#6b7590;
  --accent:#4ECDC4;
  --hot:#FF9500;
  --green:#4CAF50;
  --f:system-ui,sans-serif
}
html,body{height:100%;overflow:hidden;background:var(--bg);color:var(--text);font-family:var(--f)}

#app{display:flex;flex-direction:column;height:100vh}

/* === TOP BAR === */
.topbar{
  background:var(--top);
  border-bottom:1px solid var(--border);
  padding:0 20px;
  display:flex;
  align-items:center;
  gap:20px;
  height:52px;
  flex-shrink:0;
}
.brand{font-size:15px;font-weight:900;color:var(--accent);white-space:nowrap}
.brand span{display:block;font-size:10px;color:var(--sub);font-weight:400}
.stats{display:flex;gap:10px}
.stat-item{
  background:var(--bar);
  border:1px solid var(--border);
  border-radius:8px;
  padding:4px 12px;
  display:flex;
  align-items:center;
  gap:7px;
  cursor:pointer;
  transition:.15s;
  font-size:12px;
  white-space:nowrap;
}
.stat-item:hover{border-color:var(--accent)}
.stat-item.active{border-color:var(--accent);background:#1a2424}
.stat-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.stat-val{font-weight:700;font-size:13px}
.stat-src{color:var(--sub);font-size:11px}
.grow{flex:1}

/* === SEARCH BAR === */
.searchbar{
  background:var(--top);
  border-bottom:1px solid var(--border);
  padding:8px 20px;
  display:flex;
  gap:10px;
  align-items:center;
  flex-shrink:0;
}
.searchbar input{
  flex:1;
  max-width:360px;
  padding:7px 13px;
  background:var(--bar);
  border:1px solid var(--border);
  border-radius:8px;
  color:var(--text);
  font-size:13px;
  outline:none;
}
.searchbar input:focus{border-color:var(--accent)}
.searchbar .hint{font-size:11px;color:var(--sub);white-space:nowrap}

/* === TABS === */
.tabs{
  background:var(--top);
  border-bottom:1px solid var(--border);
  padding:0 20px;
  display:flex;
  gap:4px;
  flex-shrink:0;
}
.tab{
  padding:8px 14px;
  font-size:12px;
  color:var(--sub);
  cursor:pointer;
  border-bottom:2px solid transparent;
  transition:.15s;
  white-space:nowrap;
  display:flex;
  align-items:center;
  gap:6px;
}
.tab:hover{color:var(--text)}
.tab.active{color:var(--accent);border-color:var(--accent)}
.tab .tbadge{
  background:var(--border);
  color:var(--sub);
  font-size:10px;
  padding:1px 5px;
  border-radius:6px;
}
.tab.active .tbadge{background:#1a2424;color:var(--accent)}

/* === MAIN === */
.main{
  flex:1;
  overflow-y:auto;
  padding:12px 20px 20px;
}

/* === SECTION HEADER === */
.sec-hdr{
  display:flex;
  align-items:center;
  gap:10px;
  margin-bottom:8px;
  position:sticky;
  top:0;
  background:var(--bg);
  padding:6px 0;
  z-index:5;
}
.sec-hdr h3{font-size:12px;font-weight:700;color:var(--sub);letter-spacing:1px}
.sec-line{flex:1;height:1px;background:var(--border)}

/* === FEED LIST === */
.feed-list{display:flex;flex-direction:column;gap:2px}

.feed-item{
  display:flex;
  align-items:center;
  gap:10px;
  padding:9px 12px;
  background:var(--card);
  border:1px solid var(--border);
  border-radius:9px;
  transition:.15s;
  cursor:pointer;
  min-width:0;
}
.feed-item:hover{border-color:var(--accent);background:#181c24}
.feed-item.hidden{display:none}

.src-badge{
  padding:2px 8px;
  border-radius:20px;
  font-size:10px;
  font-weight:700;
  white-space:nowrap;
  min-width:68px;
  text-align:center;
  flex-shrink:0;
}

.title-wrap{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.item-title{
  font-size:13px;
  font-weight:600;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
  line-height:1.4;
}
.item-title a{color:var(--text);text-decoration:none}
.feed-item:hover .item-title a{color:var(--accent)}
.item-desc{
  font-size:12px;
  color:var(--sub);
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}

.item-right{display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex-shrink:0}
.item-hot{font-size:12px;font-weight:700;color:var(--hot)}
.item-time{font-size:10px;color:var(--sub)}

/* === VIDEO ROW === */
.video-item{
  display:flex;
  align-items:center;
  gap:10px;
  padding:8px 12px;
  background:var(--card);
  border:1px solid var(--border);
  border-radius:9px;
  transition:.15s;
  cursor:pointer;
  min-width:0;
}
.video-item:hover{border-color:var(--accent)}
.video-item.hidden{display:none}

/* === FOOTER === */
footer{
  text-align:center;
  padding:10px;
  color:var(--sub);
  font-size:10px;
  border-top:1px solid var(--border);
  flex-shrink:0;
}

/* === EMPTY STATE === */
.empty{
  text-align:center;
  padding:40px;
  color:var(--sub);
  font-size:13px;
}
</style>
</head>
<body>
<div id="app">

  <!-- TOP BAR -->
  <div class="topbar">
    <div class="brand">情报中心<span>v5.0</span></div>
    <div class="stats" id="topStats"></div>
    <div class="grow"></div>
    <div style="font-size:11px;color:var(--sub);white-space:nowrap" id="updateTime"></div>
  </div>

  <!-- SEARCH BAR -->
  <div class="searchbar">
    <input id="q" type="text" placeholder="搜索标题、描述..." autocomplete="off">
    <span class="hint" id="totalHint"></span>
  </div>

  <!-- TABS -->
  <div class="tabs" id="tabs"></div>

  <!-- MAIN -->
  <div class="main" id="main"></div>

  <!-- FOOTER -->
  <footer id="footer"></footer>
</div>

<script>
var DATA = __DATA__;
var N = __N__;
var C = __C__;
var PRI = __PRI__;
var PRI_NAMES = __PRI_NAMES__;

var curSrc = 'all';
var q = '';

function gs(item) {
  var u = item.url || '';
  if (u.indexOf('github.com') > -1) return 'github';
  if (u.indexOf('sspai.com') > -1) return 'sspai';
  var o = item.original_source || '';
  if (N[o]) return o;
  var st = item.source_type || 'unknown';
  return N[st] ? st : 'unknown';
}

function gv(item) {
  var h = item.hot_value || 0;
  var s = item.score || 0;
  var f = item.frequency || 1;
  return (h || s || 0) * f;
}

function fv(v) {
  if (v >= 10000) return (v/10000).toFixed(1) + 'W';
  if (v >= 1000) return (v/1000).toFixed(1) + 'k';
  return String(v || 0);
}

function getTime(item) {
  var t = item.time || '';
  if (t.indexOf('T') > -1) return t.split('T')[1].slice(0,5);
  return t;
}

// GH descriptions
var GH_ZH = __GH_ZH__;

function zh(item) {
  var combined = ((item.title||'') + ' ' + (item.desc||'')).toLowerCase();
  for (var k in GH_ZH) {
    if (combined.indexOf(k.toLowerCase()) > -1) return GH_ZH[k];
  }
  return (item.desc||'').trim();
}

// Build source counts
var srcCnt = {};
DATA.forEach(function(i){ var s=gs(i); srcCnt[s]=(srcCnt[s]||0)+1; });

// Top stats (top 5 sources by importance)
var top5 = PRI.filter(function(k){ return srcCnt[k]; }).slice(0,5);
var statsHtml = top5.map(function(k){
  var co = C[k] ? C[k][0] : '#999';
  return '<div class="stat-item" data-f="'+k+'"><span class="stat-dot" style="background:'+co+'"></span><span class="stat-val">'+srcCnt[k]+'</span><span class="stat-src">'+N[k]+'</span></div>';
}).join('');
document.getElementById('topStats').innerHTML = statsHtml;

// Update time
var latest = DATA.reduce(function(a,b){
  var ta = a.time||'', tb = b.time||'';
  return ta > tb ? ta : tb;
}, '');
if (latest && latest.indexOf('T') > -1) {
  var d = new Date(latest.replace('Z',''));
  document.getElementById('updateTime').textContent = '更新: ' + d.toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
}
document.getElementById('totalHint').textContent = '共 ' + DATA.length + ' 条';

// Tabs
var tabSrcs = ['all'].concat(top5);
var tabsHtml = tabSrcs.map(function(k){
  var cnt = k==='all' ? DATA.length : (srcCnt[k]||0);
  var label = k==='all' ? '全部' : N[k];
  return '<div class="tab'+(k==='all'?' active':'')+'" data-f="'+k+'"><span>'+label+'</span><span class="tbadge">'+cnt+'</span></div>';
}).join('');
document.getElementById('tabs').innerHTML = tabsHtml;

// Tab click
document.querySelectorAll('.tab').forEach(function(t){
  t.onclick = function() {
    document.querySelectorAll('.tab').forEach(function(x){ x.classList.remove('active'); });
    t.classList.add('active');
    curSrc = t.dataset.f;
    applyFilter();
  };
});

// Top stats click
document.querySelectorAll('.stat-item').forEach(function(s){
  s.onclick = function() {
    document.querySelectorAll('.stat-item').forEach(function(x){ x.classList.remove('active'); });
    document.querySelectorAll('.tab').forEach(function(x){ x.classList.remove('active'); });
    s.classList.add('active');
    curSrc = s.dataset.f;
    applyFilter();
  };
});

// Search
document.getElementById('q').oninput = function(e){
  q = e.target.value.toLowerCase();
  applyFilter();
};

function passes(i) {
  var s = gs(i);
  var okSrc = (curSrc === 'all') || (s === curSrc);
  var okQ = !q || (i.title||'').toLowerCase().indexOf(q) > -1 || (i.desc||'').toLowerCase().indexOf(q) > -1;
  return okSrc && okQ;
}

// Sort: high priority sources first within same score band
function scoreOf(i) {
  var priIdx = PRI.indexOf(gs(i));
  if (priIdx < 0) priIdx = 999;
  return -(priIdx * 1000000 + gv(i));
}

var sorted = DATA.slice().sort(function(a,b){ return scoreOf(a) - scoreOf(b); });

// Render
function render() {
  var visible = sorted.filter(passes);
  var vidCnt = visible.filter(function(i){ var s=gs(i); return s==='douyin'||s==='weibo'||s==='bilibili'; }).length;
  var cardCnt = visible.length - vidCnt;

  var html = '';

  if (vidCnt > 0) {
    html += '<div class="sec-hdr"><h3>视频媒体</h3><span style="font-size:11px;color:var(--sub)">'+vidCnt+'条</span><div class="sec-line"></div></div>';
    html += '<div class="feed-list">';
    visible.filter(function(i){ var s=gs(i); return s==='douyin'||s==='weibo'||s==='bilibili'; }).forEach(function(i){
      var s = gs(i);
      var n = N[s] || s;
      var co = C[s] ? C[s][0] : '#999';
      var bg = C[s] ? C[s][1] : '#F5F5F5';
      var t = i.title || 'No title';
      var u = i.url || '';
      var titleA = u ? '<a href="'+u+'" target="_blank">'+t+'</a>' : t;
      var tt = getTime(i);
      var timeStr = tt ? '<span class="item-time">'+tt+'</span>' : '';
      html += '<div class="video-item" data-src="'+s+'"><span class="src-badge" style="background:'+bg+';color:'+co+'">'+n+'</span><span class="item-title">'+titleA+'</span><div class="item-right"><span class="item-hot">'+fv(gv(i))+'</span>'+timeStr+'</div></div>';
    });
    html += '</div>';
  }

  if (cardCnt > 0) {
    html += '<div class="sec-hdr" style="margin-top:16px"><h3>全部内容</h3><span style="font-size:11px;color:var(--sub)">'+cardCnt+'条</span><div class="sec-line"></div></div>';
    html += '<div class="feed-list">';
    visible.filter(function(i){ var s=gs(i); return !(['douyin','weibo','bilibili'].indexOf(s)>-1); }).forEach(function(i){
      var s = gs(i);
      var n = N[s] || s;
      var co = C[s] ? C[s][0] : '#999';
      var bg = C[s] ? C[s][1] : '#F5F5F5';
      var t = i.title || 'No title';
      var u = i.url || '';
      var titleA = u ? '<a href="'+u+'" target="_blank">'+t+'</a>' : t;
      var d = zh(i);
      var descHtml = d ? '<div class="item-desc">'+d+'</div>' : '';
      var tt = getTime(i);
      var timeStr = tt ? '<span class="item-time">'+tt+'</span>' : '';
      html += '<div class="feed-item" data-src="'+s+'"><span class="src-badge" style="background:'+bg+';color:'+co+'">'+n+'</span><div class="title-wrap"><span class="item-title">'+titleA+'</span>'+descHtml+'</div><div class="item-right"><span class="item-hot">'+fv(gv(i))+'</span>'+timeStr+'</div></div>';
    });
    html += '</div>';
  }

  if (visible.length === 0) {
    html = '<div class="empty">没有找到匹配的内容</div>';
  }

  document.getElementById('main').innerHTML = html;
}

function applyFilter() {
  render();
  document.getElementById('totalHint').textContent = '共 ' + sorted.filter(passes).length + ' 条';
}

render();
</script>
</body>
</html>
