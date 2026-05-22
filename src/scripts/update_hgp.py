#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新 items 表的 description 字段，从 hgp_translations.json 读取翻译"""

import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "db" / "intel.db"
JSON_PATH = Path(__file__).parent / "hgp_translations.json"


def main():
    # 读取翻译JSON
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        translations = json.load(f)

    print(f"读取到 {len(translations)} 条翻译记录")

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updated = 0
    errors = 0

    for id_str, description in translations.items():
        item_id = int(id_str)
        try:
            cursor.execute(
                "UPDATE items SET description = ? WHERE id = ?",
                (description, item_id)
            )
            if cursor.rowcount > 0:
                updated += 1
            else:
                print(f"  [警告] id={item_id} 未找到或description已相同，跳过")
        except Exception as e:
            print(f"  [错误] id={item_id}: {e}")
            errors += 1

    conn.commit()

    # 验证
    cursor.execute("SELECT COUNT(*) FROM items WHERE description IS NOT NULL AND description != ''")
    total_with_desc = cursor.fetchone()[0]

    print(f"\n更新完成：成功更新 {updated} 条")
    if errors > 0:
        print(f"错误：{errors} 条")
    print(f"当前有 description 的记录总数：{total_with_desc} 条")

    conn.close()


if __name__ == "__main__":
    main()
