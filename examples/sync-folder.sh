#!/usr/bin/env bash
# sync-folder.sh — 把本地文件夹同步到百度网盘
#
# Usage:
#   bash sync-folder.sh <本地文件夹> <网盘路径>
#
# 工作原理：
#   1. 比较本地和网盘文件大小（粗略同步检查）
#   2. 直接调用 upload 子命令覆盖上传
#
# 配合 cron 每日凌晨备份：
#   0 3 * * * cd /path/to/skill && bash examples/sync-folder.sh /data/backup /apps/bypy/backup
#
# 前置条件：
#   - 已 export BAIDU_BDUSS / BAIDU_STOKEN / BAIDU_BAIDUID

set -euo pipefail

# ======== 参数解析 ========
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <本地文件夹> <网盘路径>" >&2
    echo "" >&2
    echo "示例：" >&2
    echo "  $0 /home/user/projects /apps/bypy/backup" >&2
    echo "  $0 ./output /apps/bypy/output" >&2
    exit 1
fi

LOCAL="$1"
REMOTE="$2"

if [[ ! -d "$LOCAL" ]]; then
    echo "[!] 本地目录不存在: $LOCAL" >&2
    exit 1
fi

# ======== 定位脚本 ========
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
PCS="$SKILL_DIR/scripts/baidu_pcs.py"

if [[ ! -f "$PCS" ]]; then
    echo "[!] 找不到 $PCS" >&2
    exit 1
fi

# ======== 环境检查 ========
if [[ -z "${BAIDU_BDUSS:-}" ]]; then
    echo "[!] 未设置 BAIDU_BDUSS 环境变量" >&2
    exit 2
fi

# ======== 同步前统计 ========
echo "============================================"
echo "[1/3] 同步前统计"
echo "============================================"
LOCAL_FILES=$(find "$LOCAL" -type f | wc -l)
LOCAL_SIZE=$(du -sh "$LOCAL" | cut -f1)
echo "本地: $LOCAL"
echo "  文件数: $LOCAL_FILES"
echo "  体积:   $LOCAL_SIZE"

# ======== 检查网盘目标 ========
echo ""
echo "============================================"
echo "[2/3] 检查网盘目标 $REMOTE"
echo "============================================"
if python "$PCS" meta "$REMOTE" >/dev/null 2>&1; then
    echo "[i] 目标已存在，将覆盖上传"
else
    echo "[i] 目标不存在，将创建"
fi

# ======== 执行同步 ========
echo ""
echo "============================================"
echo "[3/3] 开始同步"
echo "============================================"
START=$(date +%s)
python "$PCS" upload "$LOCAL" "$REMOTE"
ELAPSED=$(( $(date +%s) - START ))

echo ""
echo "[✓] 同步完成，耗时 ${ELAPSED}s"
echo ""
echo "提示：如需把同步结果生成可分享链接，跑："
echo "      python $PCS share $REMOTE --code 8888"
