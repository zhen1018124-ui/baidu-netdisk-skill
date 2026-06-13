#!/usr/bin/env bash
# setup-and-test.sh — 一键设置环境变量 + 跑 quota 验证
#
# 用法（Git Bash / WSL）：
#   bash examples/setup-and-test.sh
#
# 会让你输入 BDUSS / STOKEN / BAIDUID（密码形式，输入不回显），然后跑 quota。
# 环境变量只在本 shell 会话生效，关闭 shell 即失效——不会写入任何文件。

set -euo pipefail

echo "============================================"
echo "百度网盘 Skill · 环境变量设置 + 验证"
echo "============================================"
echo ""
echo "请依次粘贴以下三个值（每行一个，密码形式不回显）："
echo ""

read -r -p "BDUSS (192 位):   " BAIDU_BDUSS
if [[ -z "$BAIDU_BDUSS" ]]; then
    echo "[!] BDUSS 不能为空" >&2; exit 1
fi

read -r -p "STOKEN (可空):    " BAIDU_STOKEN
read -r -p "BAIDUID (40 位):  " BAIDU_BAIDUID

echo ""
echo "[i] 已读取:"
echo "    BDUSS 长度:  ${#BAIDU_BDUSS}"
echo "    STOKEN 长度: ${#BAIDU_STOKEN}"
echo "    BAIDUID 长度: ${#BAIDU_BAIDUID}"
echo ""

export BAIDU_BDUSS BAIDU_STOKEN BAIDU_BAIDUID

# 找 python
PY=""
for p in python python3 py; do
    if command -v "$p" >/dev/null 2>&1; then
        PY="$p"; break
    fi
done
if [[ -z "$PY" ]]; then
    echo "[!] 找不到 python，请先装 Python 3.8+" >&2
    exit 2
fi
echo "[i] 使用 Python: $PY ($($PY --version 2>&1))"
echo ""

# 跑 quota
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PCS="$SCRIPT_DIR/../scripts/baidu_pcs.py"

echo "[1/2] 验证 Cookie..."
"$PY" "$PCS" quota || {
    echo ""
    echo "[!] quota 失败。检查点:"
    echo "    1. BDUSS 是否完整（长度应为 192 左右）"
    echo "    2. STOKEN 是否需要重新抓（若 BDUSS 是新抓的，STOKEN 也要重抓）"
    echo "    3. 在浏览器里 F12 看一下 BDUSS 是不是最新的（可能被踢下线）"
    exit 3
}

echo ""
echo "[2/2] 列一下 /apps/bypy/ 看看能否访问（可选测试）"
"$PY" "$PCS" list /apps/bypy/ 2>&1 | head -20 || echo "[i] /apps/bypy/ 不存在或不可访问，正常。"

echo ""
echo "============================================"
echo "[✓] 设置完成！"
echo "============================================"
echo ""
echo "环境变量在当前 shell 有效。常用命令："
echo ""
echo "  # 看容量"
echo "  $PY $PCS quota"
echo ""
echo "  # 上传 + 分享"
echo "  $PY $PCS upload ./my-folder /apps/bypy/my-folder"
echo "  $PY $PCS share /apps/bypy/my-folder --code 8888"
echo ""
echo "  # 一键上传并分享"
echo "  bash $SCRIPT_DIR/upload-and-share.sh ./my-folder /apps/bypy/my-folder 8888"
echo ""
echo "⚠️ 用完记得在 https://pan.baidu.com 设置里撤销设备登录！"