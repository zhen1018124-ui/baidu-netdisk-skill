#!/usr/bin/env bash
# upload-and-share.sh — 一键上传 + 生成分享链接
#
# Usage:
#   bash upload-and-share.sh <本地路径> <网盘路径> [提取码] [有效期天数]
#
# Examples:
#   bash upload-and-share.sh ./my-project /apps/bypy/my-project
#   bash upload-and-share.sh ./report.pdf /apps/bypy/reports/2026-06.pdf 8888
#   bash upload-and-share.sh ./tmp /apps/bypy/tmp 1234 7    # 7 天有效期
#
# 前置条件：
#   - 已 export BAIDU_BDUSS / BAIDU_STOKEN / BAIDU_BAIDUID
#   - 脚本路径：scripts/baidu_pcs.py

set -euo pipefail

# ======== 参数解析 ========
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <本地路径> <网盘路径> [提取码] [有效期天数]" >&2
    echo "       有效期可选：0=永久(默认) / 1 / 7 / 30" >&2
    exit 1
fi

LOCAL="$1"
REMOTE="$2"
CODE="${3:-}"
PERIOD="${4:-0}"

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
    echo "    获取方法：参见 $SKILL_DIR/references/auth-setup.md" >&2
    exit 2
fi

echo "============================================"
echo "[1/3] 检查容量"
echo "============================================"
python "$PCS" quota

echo ""
echo "============================================"
echo "[2/3] 上传 $LOCAL → $REMOTE"
echo "============================================"
python "$PCS" upload "$LOCAL" "$REMOTE"

echo ""
echo "============================================"
echo "[3/3] 生成分享链接"
echo "============================================"

SHARE_ARGS=("$PCS" share "$REMOTE" "--period" "$PERIOD")
if [[ -n "$CODE" ]]; then
    SHARE_ARGS+=("--code" "$CODE")
fi

python "${SHARE_ARGS[@]}"

echo ""
echo "[✓] 完成！链接已复制到剪贴板（如系统支持）"
echo ""
echo "提示：测试完成后如不再需要，可在网盘网页版"我的分享"取消，"
echo "      或执行：python $PCS delete $REMOTE"
