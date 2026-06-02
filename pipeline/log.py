# log.py — 日志模块
import json
from datetime import datetime
from .config import LOG_DIR


def log(msg):
    """终端输出日志（带时间戳）。"""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def write_pipeline_log(date_key, status, details=None):
    """写入结构化流水线运行日志到 JSON 文件。"""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_entry = {
            "date": date_key,
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "details": details or {},
        }
        log_file = LOG_DIR / f"{date_key}.json"
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
            runs = existing.get("runs", [])
        else:
            runs = []
        runs.append(log_entry)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump({"date": date_key, "runs": runs}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
