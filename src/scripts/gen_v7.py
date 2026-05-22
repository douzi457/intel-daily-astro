<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>情报中心 v7</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#fff;
  --bar:#f4f4f4;
  --row:#fff;
  --border:#eee;
  --text:#111;
  --sub:#888;
  --accent:#0a56a8;
  --hot:#d44;
  --f:'PingFang SC','Microsoft YaHei',system-ui,sans-serif
}
body{background:var(--bg);color:var(--text);font-family:var(--f);font-size:14px}
body::-webkit-scrollbar{width:4px}
body::-webkit-scrollbar-thumb{background:#ccc}

/* HEADER */
header{
  background:#1a1a1a;
  color:#fff;
  padding:10px 20px;
  display:flex;
  align-items:center;
  gap:20px;
  position:sticky;
  top:0;
  z-index:100;
}
header .brand{
  font-size:15px;
  font-weight:900;
  color:#4ECDC4;
  letter-spacing:1px;
  flex-shrink:0;
}
header .updated{font-size:11px;color:#888;flex-shrink:0}
header .ticker{
  flex:1;
  overflow:hidden;
  white-space:nowrap;
  font-size:12px;
  color:#aaa;
}
header .ticker span{padding:0 18px}
header .ticker span:first-child{padding-left:0}

/* FILTER BAR */
.filter{
  background:var(--bar);
  border-bottom:1px solid var(--border);
  padding:6px 20px;
  display:flex;
  gap:6px;
  flex-wrap:wrap;
  align-items:center;
}
.fbtn{
  padding:3px 11px;
  border-radius:20px;
  border:1px solid #ddd;
  background:#fff;
  font-size:12px;
  cursor:pointer;
  transition:.12s;
  color:#555;
}
.fbtn:hover{border-color:var(--accent);color:var(--accent)}
.fbtn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.fbtn .cnt{margin-left:4px;opacity:.7}

/* SEARCH */
.srow{
  padding:8px 20px;
  border-bottom:1px solid var(--border);
  display:flex;
  gap:10px;
  align-items:center;
  background:#fafafa;
}
.srow input{
  flex:1;
  max-width:380px;
  padding:6px 12px;
  border:1px solid #ddd;
  border-radius:6px;
  font-size:13px;
  outline:none;
  background:#fff;
  color:var(--text);
}
.srow input:focus{border-color:var(--accent)}
.srow .hint{font-size:12px;color:var(--sub)}

/* MAIN */
.main{padding:0 20px}

/* SEC LABEL */
.sec-label{
  display:flex;
  align-items:center;
  gap:8px;
  padding:8px 0 4px;
  font-size:11px;
  color:var(--sub);
  letter-spacing:1px;
}
.sec-label .ln{flex:1;height:1px;background:#eee}

/* ROW */
.news-list{display:flex;flex-direction:column}
.row{
  display:flex;
  align-items:center;
  gap:0;
  padding:7px 0;
  border-bottom:1px solid #f5f5f5;
  cursor:pointer;
  transition:.1s;
}
.row:hover{background:#f8fbff}
.row:hover .title{color:var(--accent)}
.row.hidden{display:none}
.plat{
  width:72px;
  font-size:10px;
  font-weight:700;
  text-align:center;
  flex-shrink:0;
  padding:2px 0;
}
.title{
  flex:1;
  font-size:14px;
  font-weight:400;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
  padding:0 12px;
  color:var(--text);
}
.title a{color:inherit;text-decoration:none}
.time{
  width:42px;
  text-align:right;
  font-size:11px;
  color:var(--sub);
  flex-shrink:0;
}

/* FOOTER */
footer{
  text-align:center;
  padding:14px;
  color:var(--sub);
  font-size:11px;
  border-top:1px solid var(--border);
}
</style>
</head>
<body>

<header>
  <div class="brand">情报中心</div>
  <div class="updated" id="updated"></div>
  <div class="ticker" id="ticker"></div>
</header>

<div class="filter" id="filters"></div>

<div class="srow">
  <input id="q" placeholder="搜索标题..." autocomplete="off">
  <span class="hint" id="hint"></span>
</div>

<div class="main" id="main"></div>

<footer id="footer"></footer>

<script>
var DATA = __DATA__;
var N = __N__;
var C = __C__;
var PRI = __PRI__;

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
  return (item.hot_value || item.score || 0) * (item.frequency || 1);
}
function gt(item) {
  var t = item.time || '';
  return t.indexOf('T') > -1 ? t.split('T')[1].slice(0,5) : '';
}
function scoreOf(i) {
  var pi = PRI.indexOf(gs(i));
  if (pi < 0) pi = 999;
  return pi * 10000000 + gv(i);
}

var srcCnt = {};
DATA.forEach(function(i){ var s=gs(i); srcCnt[s]=(srcCnt[s]||0)+1; });

// top sources for filters
var topSrcs = PRI.filter(function(k){ return srcCnt[k]; }).slice(0,9);
var filtHtml = '<div class="fbtn active" data-f="all">全部<span class="cnt">'+DATA.length+'</span></div>';
topSrcs.forEach(function(k){
  filtHtml += '<div class="fbtn" data-f="'+k+'">'+N[k]+'<span class="cnt">'+srcCnt[k]+'</span></div>';
});
document.getElementById('filters').innerHTML = filtHtml;

// Updated time
var latest = DATA.reduce(function(a,b){ return (a.time||'') > (b.time||'') ? a : b; }, DATA[0]);
if (latest && latest.time) {
  var d = new Date(latest.time.replace('Z',''));
  document.getElementById('updated').textContent = '更新于 ' + d.toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
}

// Ticker: top 5 hot
var top5 = DATA.slice().sort(function(a,b){ return gv(b)-gv(a); }).slice(0,5);
document.getElementById('ticker').innerHTML = '<span>最热：</span>' + top5.map(function(i){
  return '<span>'+N[gs(i)]+' · '+(i.title||'').slice(0,28)+'</span>';
}).join('<span> · </span>');

document.getElementById('hint').textContent = '共 ' + DATA.length + ' 条';

var sorted = DATA.slice().sort(function(a,b){ return scoreOf(a) - scoreOf(b); });

var curF = 'all', qv = '';

document.querySelectorAll('.fbtn').forEach(function(el){
  el.onclick = function() {
    document.querySelectorAll('.fbtn').forEach(function(s){ s.classList.remove('active'); });
    el.classList.add('active');
    curF = el.dataset.f;
    render();
  };
});
document.getElementById('q').oninput = function(e){ qv = e.target.value.toLowerCase(); render(); };

function passes(i) {
  return (curF === 'all' || gs(i) === curF) && (!qv || (i.title||'').toLowerCase().indexOf(qv) > -1);
}

function render() {
  var vis = sorted.filter(passes);
  document.getElementById('hint').textContent = '显示 ' + vis.length + ' / ' + DATA.length;

  if (!vis.length) {
    document.getElementById('main').innerHTML = '<div style="padding:30px;text-align:center;color:#888">无匹配结果</div>';
    return;
  }

  document.getElementById('main').innerHTML = '<div class="news-list">' +
    vis.map(function(i){
      var s = gs(i);
      var co = C[s] ? C[s][0] : '#888';
      var t = i.title || 'No title';
      var u = i.url || '';
      var ta = u ? '<a href="'+u+'" target="_blank">'+t+'</a>' : t;
      return '<div class="row" data-src="'+s+'"><span class="plat" style="color:'+co+'">'+N[s]+'</span><span class="title">'+ta+'</span><span class="time">'+gt(i)+'</span></div>';
    }).join('') + '</div>';
}

document.getElementById('footer').textContent = '情报中心 v7 · NewsNow · ' + DATA.length + ' 条';
render();
</script>
</body>
</html>
