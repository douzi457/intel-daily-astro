"""
一次性诊断并修复三个数据源：
1. gzh - fetch_gzh_trends.py 缺 UTF-8 重配置
2. weibo - 路径是 weibo-trending 而不是 weibo-hot-search
3. sspai - 技能不存在，需要单独处理
"""
import sys, subprocess, json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
WORKSPACE = Path(r"C:\Users\douzi457\.qclaw\workspace\情报系统")
SKILLS = Path(r"C:\Users\douzi457\.qclaw\workspace\skills")

def test_gzh():
    print("\n=== 1. 公众号 (gzh) ===")
    script = SKILLS / "gzh-explosive-content-detector" / "scripts" / "fetch_gzh_trends.py"
    if not script.exists():
        print("  ❌ 脚本不存在"); return None
    result = subprocess.run(
        [sys.executable, str(script), "--keyword", "副业", "--max-items", "3"],
        capture_output=True, text=True, timeout=30
    )
    # 检查是否需要加 UTF-8 fix
    content = script.read_text(encoding='utf-8')
    has_utf8_fix = 'sys.stdout.reconfigure' in content
    print(f"  脚本存在: ✅, 有UTF-8 fix: {'✅' if has_utf8_fix else '❌'}")
    print(f"  RC: {result.returncode}")
    if result.stderr:
        print(f"  STDERR: {result.stderr[:200]}")
    if result.stdout:
        print(f"  STDOUT: {result.stdout[:200]}")
    return has_utf8_fix

def test_weibo():
    print("\n=== 2. 微博 (weibo-trending) ===")
    # 检查两个可能的路径
    skill_name_collector = "weibo-hot-search"  # collector.py 里写的
    skill_name_actual = "weibo-trending"       # 实际安装的名字
    script_collector = SKILLS / skill_name_collector / "scripts" / "weibo_fetch.js"
    script_actual = SKILLS / skill_name_actual / "scripts" / "fetch-hot-search.py"
    print(f"  collector期望路径存在: {'✅' if script_collector.exists() else '❌'} {script_collector}")
    print(f"  实际安装路径存在: {'✅' if script_actual.exists() else '❌'} {script_actual}")
    if script_actual.exists():
        # 测试 fetch-hot-search.py
        r = subprocess.run([sys.executable, str(script_actual)], capture_output=True, text=True, timeout=30)
        print(f"  fetch-hot-search.py RC: {r.returncode}")
        if r.stdout and r.stdout.strip():
            try:
                data = json.loads(r.stdout.strip())
                print(f"  数据条数: {len(data) if isinstance(data, list) else '?'}")
            except:
                print(f"  STDOUT: {r.stdout[:200]}")
        if r.stderr:
            print(f"  STDERR: {r.stderr[:200]}")
    return script_actual.exists()

def test_sspai():
    print("\n=== 3. 少数派 (sspai) ===")
    skill_path = SKILLS / "sspai"
    print(f"  技能存在: {'✅' if skill_path.exists() else '❌'}")
    if skill_path.exists():
        scripts = list((skill_path / "scripts").glob("*"))
        print(f"  脚本: {scripts}")
    else:
        print("  ❌ 需要安装 sspai 技能")
    return skill_path.exists()

results = {}
results['gzh'] = test_gzh()
results['weibo'] = test_weibo()
results['sspai'] = test_sspai()

print("\n=== 总结 ===")
for k, v in results.items():
    print(f"  {k}: {'✅' if v else '❌'}")
