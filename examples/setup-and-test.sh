#!/usr/bin/env bash
# setup-and-test.sh — 向后兼容入口（重定向到 setup-env.sh）
#
# ⚠️ v1.3.0+ 推荐使用 setup-env.sh
# 本脚本保留仅为兼容老命令，行为已统一：
#   - 写 .env 文件（而非临时环境变量）
#   - 跑 quota 验证
#   - chmod 600 限制权限
#
# 新用户请直接跑：
#   bash examples/setup-env.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[i] setup-and-test.sh 在 v1.3.0 之后已被 setup-env.sh 取代"
echo "[i] 自动跳转到新脚本..."
echo ""

exec "$SCRIPT_DIR/setup-env.sh" "$@"
