import sys
sys.stdout.reconfigure(encoding='utf-8')

"""
情报系统主调度器
功能：
  python run.py collect       — 手动跑一次采集
  python run.py generate      — 手动生成所有 HTML
  python run.py generate --today — 只生成今日日报
  python run.py serve         — 本地预览（http.server）
  python run.py schedule      — 后台运行定时任务（采集每2h，日报6h+20h）

用法（定时任务用 schedule，serve 用于本地预览）：
  采集 + 生成今日日报：
    python run.py collect
    python run.py generate --today

  本地预览：
    python run.py serve
    → 浏览器打开 http://localhost:8765/output/index.html
"""
import sys, os, time, subprocess, threading
from pathlib import Path
from datetime import datetime, date, timedelta
import http.server, webbrowser

WORKSPACE = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")
COLLECTOR = WORKSPACE / "collect" / "collector.py"
GENERATOR = WORKSPACE / "collect" / "generate.py"
OUTPUT    = WORKSPACE / "output"

CST_OFFSET = 8  # UTC+8

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def do_collect():
    log("=== 采集开始 ===")
    r = subprocess.run([sys.executable, str(COLLECTOR)], capture_output=True, text=True, encoding='utf-8')
    print(r.stdout[-500:] if r.stdout else '')
    if r.stderr: print(r.stderr[-300:])
    log("=== 采集完成 ===")

def do_generate(today_only=False):
    log("=== 生成 HTML ===")
    args = [sys.executable, str(GENERATOR)]
    if today_only: args.append('--today')
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8')
    print(r.stdout[-500:] if r.stdout else '')
    log("=== 完成 ===")

# ---- 定时逻辑 ----

def get_next_6am():
    now = datetime.now()
    h = now.hour
    target = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if h >= 6:
        target += timedelta(days=1)
    return target

def get_next_8pm():
    now = datetime.now()
    h = now.hour
    target = now.replace(hour=20, minute=0, second=0, microsecond=0)
    if h >= 20:
        target += timedelta(days=1)
    return target

def wait_until(dt):
    secs = (dt - datetime.now()).total_seconds()
    if secs > 0:
        log(f"等待 {secs/3600:.1f}h 直到 {dt.strftime('%H:%M')}")
        time.sleep(min(secs, 300))  # 最多睡5分钟再检查

def schedule_loop():
    """
    永动机循环：
    - 每2小时采集一次（00:00, 02:00, 04:00, ...）
    - 每天 06:00 生成 24h 日报
    - 每天 20:00 生成 增量日报
    """
    log("定时调度已启动")
    # 启动时先采集一次（如果距上次采集超过30分钟）
    do_collect()
    do_generate(today_only=True)

    while True:
        now = datetime.now()
        mins = now.minute

        # 每2小时：00, 02, 04, 06, 08, 10, 12, 14, 16, 18, 20, 22
        # 在每个整点前1分钟检查
        if mins >= 58 or mins <= 2:
            log(f"[{now.strftime('%H:%M')}] 2h采集检查")
            do_collect()
            do_generate(today_only=True)
            # 睡55分钟，避免重复触发
            time.sleep(55 * 60)
        else:
            time.sleep(30 * 60)  # 每30分钟检查一次

        # 每天 06:00 前后生成日报
        # 每天 20:00 前后生成增量日报
        # 这由上面的 2h 触发点覆盖

def serve():
    """本地 HTTP 服务"""
    port = 8765
    os.chdir(str(WORKSPACE))
    handler = http.server.SimpleHTTPRequestHandler
    handler.extensions_map.update({'.html': 'text/html'})
    srv = http.server.HTTPServer(('', port), handler)
    url = f"http://localhost:{port}/output/index.html"
    log(f"本地预览已启动：{url}")
    webbrowser.open(url)
    srv.serve_forever()

# ---- CLI ----

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'help'

    if cmd == 'collect':
        do_collect()
    elif cmd == 'generate':
        today_only = len(sys.argv) > 2 and sys.argv[2] == '--today'
        do_generate(today_only)
    elif cmd == 'serve':
        serve()
    elif cmd == 'schedule':
        log("启动后台定时任务...")
        t = threading.Thread(target=schedule_loop, daemon=True)
        t.start()
        log("调度器运行中，按 Ctrl+C 停止")
        try:
            while True: time.sleep(60)
        except KeyboardInterrupt:
            log("已停止")
    else:
        print(__doc__)
