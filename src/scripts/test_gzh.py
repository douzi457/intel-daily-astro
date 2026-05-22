import sys
sys.stdout.reconfigure(encoding='utf-8')
import subprocess
from pathlib import Path

skill_dir = Path(r"C:\Users\douzi457\.qclaw\workspace\skills\gzh-explosive-content-detector\scripts")
script = skill_dir / "fetch_gzh_trends.py"
print(f"Script exists: {script.exists()}")

result = subprocess.run(
    [sys.executable, str(script), "--keyword", "副业", "--max-items", "5"],
    capture_output=True, text=True, timeout=30
)
print("STDOUT:", result.stdout[:500] if result.stdout else "(empty)")
print("STDERR:", result.stderr[:500] if result.stderr else "(empty)")
print("RC:", result.returncode)
