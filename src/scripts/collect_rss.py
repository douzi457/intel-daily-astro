# collect_rss.py — 兼容包装器，实际逻辑已迁移至 pipeline/ 模块
# 用法: python src/scripts/collect_rss.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from pipeline.main import collect_all

if __name__ == "__main__":
    collect_all()
