<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>情报中心 v6</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#fff;
  --header:#1a1a1a;
  --row:#f7f8fa;
  --row2:#fff;
  --border:#e8e8e8;
  --text:#111;
  --sub:#888;
  --hover:#f0f4ff;
  --accent:#0a56a8;
  --hot:#d44;
  --f:'PingFang SC','Microsoft YaHei',system-ui,sans-serif
}
html,body{background:var(--bg);color:var(--text);font-family:var(--f)}
body::-webkit-scrollbar{width:5px}
body::-webkit-scrollbar-thumb{background:#ccc;border-radius:3px}

/* === HEADER === */
.ticker-wrap{
  background:var(--header);
  color:#fff;
  padding:0 20px;
  display:flex;
  align-items:center;
  gap:0;
  height:42px;
  overflow:hidden;
}
.ticker-brand{
  font-size:14px;
  font-weight:900;
  letter-spacing:1px;
  white-space:nowrap;
  padding-right:16px;
  border-right:1px solid #444;
  margin-right:16px;
  color:#4ECDC4;
  flex-shrink:0;
}
.ticker-updated{font-size:11px;color:#888;white-space:nowrap;flex-shrink:0}
.ticker-scroll{flex:1;overflow:hidden;white-space:nowrap}
.ticker-scroll span{font-size:12px;color:#ccc;padding:0 20px}

/* === SEARCH === */
.search-row{
  background:#fafafa;
  border-bottom:1px solid var(--border);
  padding:7px 20px;
  display:flex;
  gap:10px;
  align-items:center;
}
.search-row input{
  flex:1;
  max-width:400px;
  padding:6px 12px;
  border:1px solid #ddd;
  border-radius:6px;
  font-size:13px;
  outline:none;
  background:#fff;
  color:var(--text);
}
.search-row input:focus{border-color:var(--accent)}
.search-row .hint{font-size:12px;color:var(--sub);white-space:nowrap}
.src-filters{display:flex;gap:6px;flex-wrap:wrap}
.sf{
  padding:3px 10px;
  border-radius:20px;
  font-size:11px;
  cursor:pointer;
  border:1px solid #ddd;
  background:#fff;
  color:var(--sub);
  transition:.12s;
  white-space:nowrap;
}
.sf:hover{border-color:var(--accent);color:var(--accent)}
.sf.on{background:var(--accent);color:#fff;border-color:var(--accent)}

/* === MAIN === */
.main{padding:0 20px}

/* === SEC HEAD === */
.sec{padding:10px 0 6px;display:flex;align-items:center;gap:10px;border-bottom:2px solid var(--border);margin-bottom:0}
.sec h3{font-size:12px;font-weight:900;color:var(--sub);letter-spacing:1px;text-transform:uppercase}
.sec .sc{background:#f0f0f0;color:#888;font-size:11px;padding:1px 7px;border-radius:10px}
.sec .ln{flex:1;height:1px;background:#eee}

/* === NEWS ROW === */
.news-list{display:flex;flex-direction:column}
.news-row{
  display:flex;
  align-items:center;
  gap:0;
  padding:6px 0;
  border-bottom:1px solid #f0f0f0;
  cursor:pointer;
  transition:.1s;
}
.news-row:hover{background:var(--hover)}
.news-row:hover .nw{color:var(--accent)}
.news-row.hidden{display:none}

.ns{
  width:80px;
  padding:2px 8px;
  border-radius:3px;
  font-size:10px;
  font-weight:700;
  text-align:center;
  flex-shrink:0;
  margin-right:10px;
}
.nw{
  flex:1;
  font-size:14px;
  font-weight:500;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
  padding-right:10px;
  color:var(--text);
}
.nw a{color:inherit;text-decoration:none}
.nh{
  width:52px;
  text-align:right;
  font-size:12px;
  color:var(--hot);
  font-weight:700;
  flex-shrink:0;
  margin-left:8px;
}
.nt{
  width:42px;
  text-align:right;
  font-size:11px;
  color:var(--sub);
  flex-shrink:0;
}

/* === VIDEO ROW (slightly different) === */
.video-row .ns{color:#00c853}
.news-row.video-row .nw{color:#333}

/* === FOOTER === */
footer{
  text-align:center;
  padding:16px;
  color:var(--sub);
  font-size:11px;
  border-top:1px solid var(--border);
  margin-top:10px;
}

/* === EMPTY === */
.empty{padding:30px;text-align:center;color:var(--sub);font-size:13px}
</style>
</head>
<body>

<div class="ticker-wrap">
  <div class="ticker-brand">情报中心</div>
  <div class="ticker-updated" id="updated"></div>
  <div class="ticker-scroll" id="ticker"></div>
</div>

<div class="search-row">
  <input id="q" placeholder="搜索标题..." autocomplete="off">
  <span class="hint" id="totalHint"></span>
  <div class="src-filters" id="filters"></div>
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
function fv(v) {
  if (v >= 10000) return (v/10000).toFixed(1) + 'W';
  if (v >= 1000) return (v/1000).toFixed(1) + 'k';
  return String(v || 0);
}
function gt(item) {
  var t = item.time || '';
  return t.indexOf('T') > -1 ? t.split('T')[1].slice(0,5) : '';
}

var VS = {'douyin':1,'weibo':1,'bilibili':1};

var srcCnt = {};
DATA.forEach(function(i){ var s=gs(i); srcCnt[s]=(srcCnt[s]||0)+1; });

var topSrcs = PRI.filter(function(k){ return srcCnt[k]; }).slice(0,8);
var filtHtml = '<div class="sf on" data-f="all">全部</div>';
topSrcs.forEach(function(k){
  filtHtml += '<div class="sf" data-f="'+k+'">'+N[k]+'</div>';
});
document.getElementById('filters').innerHTML = filtHtml;

var latest = DATA.reduce(function(a,b){ return (a.time||'') > (b.time||'') ? a : b; }, DATA[0]);
if (latest && latest.time) {
  var d = new Date(latest.time.replace('Z',''));
  document.getElementById('updated').textContent = '更新于 ' + d.toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
  // ticker
  var top3 = DATA.slice().sort(function(a,b){ return gv(b)-gv(a); }).slice(0,3);
  document.getElementById('ticker').innerHTML = '<span>最热：</span>' + top3.map(function(i){
    return '<span>'+(i.title||'').slice(0,40)+'</span>';
  }).join('<span> · </span>');
}
document.getElementById('totalHint').textContent = '共 ' + DATA.length + ' 条';

// sorted by priority then heat
function scoreOf(i) {
  var pi = PRI.indexOf(gs(i));
  if (pi < 0) pi = 999;
  return pi * 10000000 + gv(i);
}
var sorted = DATA.slice().sort(function(a,b){ return scoreOf(a) - scoreOf(b); });

var curF = 'all', q = '';

document.querySelectorAll('.sf').forEach(function(el){
  el.onclick = function() {
    document.querySelectorAll('.sf').forEach(function(s){ s.classList.remove('on'); });
    el.classList.add('on');
    curF = el.dataset.f;
    render();
  };
});
document.getElementById('q').oninput = function(e){
  q = e.target.value.toLowerCase();
  render();
};

function passes(i) {
  var okS = curF === 'all' || gs(i) === curF;
  var okQ = !q || (i.title||'').toLowerCase().indexOf(q) > -1 || (i.desc||'').toLowerCase().indexOf(q) > -1;
  return okS && okQ;
}

function render() {
  var visible = sorted.filter(passes);
  var vid = visible.filter(function(i){ return VS[gs(i)]; });
  var news = visible.filter(function(i){ return !VS[gs(i)]; });
  document.getElementById('totalHint').textContent = '显示 ' + visible.length + ' / ' + DATA.length;

  var html = '';

  if (news.length) {
    html += '<div class="sec"><h3>内容</h3><span class="sc">'+news.length+'</span><div class="ln"></div></div>';
    html += '<div class="news-list">';
    news.forEach(function(i){
      var s = gs(i); var co = C[s]?C[s][0]:'#999'; var bg = C[s]?C[s][1]:'#f5f5f5';
      var t = i.title||'No title';
      var u = i.url||'';
      var ta = u ? '<a href="'+u+'" target="_blank">'+t+'</a>' : t;
      html += '<div class="news-row" data-src="'+s+'"><span class="ns" style="color:'+co+';background:'+bg+'">'+N[s]+'</span><span class="nw">'+ta+'</span><span class="nh">'+fv(gv(i))+'</span><span class="nt">'+gt(i)+'</span></div>';
    });
    html += '</div>';
  }

  if (vid.length) {
    html += '<div class="sec" style="margin-top:8px"><h3>视频</h3><span class="sc">'+vid.length+'</span><div class="ln"></div></div>';
    html += '<div class="news-list">';
    vid.forEach(function(i){
      var s = gs(i); var co = C[s]?C[s][0]:'#999'; var bg = C[s]?C[s][1]:'#f5f5f5';
      var t = i.title||'No title';
      var u = i.url||'';
      var ta = u ? '<a href="'+u+'" target="_blank">'+t+'</a>' : t;
      html += '<div class="news-row video-row" data-src="'+s+'"><span class="ns" style="color:'+co+';background:'+bg+'">'+N[s]+'</span><span class="nw">'+ta+'</span><span class="nh">'+fv(gv(i))+'</span><span class="nt">'+gt(i)+'</span></div>';
    });
    html += '</div>';
  }

  if (!visible.length) html = '<div class="empty">无匹配结果</div>';

  document.getElementById('main').innerHTML = html;
}

document.getElementById('footer').innerHTML = '情报中心 v6 · ' + DATA.length + ' 条 · NewsNow风格';
render();
</script>
</body>
</html>
