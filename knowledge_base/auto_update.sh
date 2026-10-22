#!/bin/bash
# 知识库自动更新脚本
# 功能：定期爬取博客更新，更新知识库索引

KB_DIR="/root/intel-daily-astro/knowledge_base"
LOG_FILE="/root/intel-daily-astro/knowledge_base/update.log"
LOCK_FILE="/tmp/kb_update.lock"

# 检查是否已有进程运行
if [ -f "$LOCK_FILE" ]; then
    echo "$(date): 已有更新进程运行，退出" >> "$LOG_FILE"
    exit 1
fi

# 创建锁文件
touch "$LOCK_FILE"

echo "$(date): 开始知识库更新..." >> "$LOG_FILE"

# 更新甬哥博客（最近1个月）
echo "$(date): 爬取甬哥博客..." >> "$LOG_FILE"
curl -s -L --max-time 20 \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
    "https://ygkkk.blogspot.com/" | \
    grep -o 'https://ygkkk.blogspot.com/[0-9]*/[^"]*' | \
    head -10 > "${KB_DIR}/ygkkk_recent_urls.txt"

# 更新233Boy（最近3个月）
echo "$(date): 爬取233Boy..." >> "$LOG_FILE"
curl -s -L --max-time 20 \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
    "https://233boy.com/archives" | \
    grep -o 'https://233boy.com/[^"]*' | \
    sort -u | head -15 > "${KB_DIR}/233boy_recent_urls.txt"

# 更新科技老王（最近3个月）
echo "$(date): 爬取科技老王..." >> "$LOG_FILE"
curl -s -L --max-time 20 \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
    "https://kejilaowang.com/category/vps" | \
    grep -o 'https://kejilaowang.com/[^"]*' | \
    sort -u | head -15 > "${KB_DIR}/kejilaowang_recent_urls.txt"

# 检查GitHub脚本更新
echo "$(date): 检查GitHub更新..." >> "$LOG_FILE"
curl -s -I "https://github.com/MHSanaei/3x-ui" | \
    grep -i "last-modified\|date" >> "${KB_DIR}/github_check.txt" 2>/dev/null || true

# 清理锁文件
rm -f "$LOCK_FILE"

echo "$(date): 知识库更新完成" >> "$LOG_FILE"
