#!/usr/bin/env bash
# setup-env.sh — 交互式写 .env + 跑 quota 验证（持久化）
#
# 用法（Git Bash / WSL / macOS）：
#   bash examples/setup-env.sh
#
# 与 setup-and-test.sh 的区别：
#   setup-and-test.sh —— 环境变量只在本 shell 有效，关掉就没了
#   setup-env.sh       —— 写到 .env 文件，长期有效（推荐）
#
# 首次使用：会自动从 .env.example 复制模板

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
ENV_EXAMPLE="$ROOT_DIR/.env.example"

echo "============================================"
echo "百度网盘 Skill · .env 设置 + 验证"
echo "============================================"
echo ""
echo "将写入: $ENV_FILE"
echo "（输入回车跳过可选项；Ctrl+C 中止）"
echo ""

# 首次使用：复制模板
if [[ ! -f "$ENV_FILE" ]]; then
    if [[ -f "$ENV_EXAMPLE" ]]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo "[i] 已从 .env.example 复制模板"
    else
        touch "$ENV_FILE"
        echo "[i] 创建空 .env（没找到 .env.example）"
    fi
    echo ""
fi

# 读取现有值（如果有）
CURRENT_BDUSS=$(grep -E '^BAIDU_BDUSS=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- || true)
CURRENT_STOKEN=$(grep -E '^BAIDU_STOKEN=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- || true)
CURRENT_BAIDUID=$(grep -E '^BAIDU_BAIDUID=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- || true)

if [[ -n "$CURRENT_BDUSS" ]]; then
    echo "[i] 检测到 .env 已有 BDUSS（长度 ${#CURRENT_BDUSS}），可回车保留"
fi
echo ""

# 交互式输入
read -r -p "BDUSS (192 位):   " BDUSS
BDUSS="${BDUSS:-$CURRENT_BDUSS}"
if [[ -z "$BDUSS" ]]; then
    echo "[!] BDUSS 不能为空" >&2; exit 1
fi
if [[ ${#BDUSS} -lt 100 ]]; then
    echo "[!] BDUSS 长度异常: ${#BDUSS}" >&2; exit 1
fi

read -r -p "STOKEN (可空):    " STOKEN
STOKEN="${STOKEN:-$CURRENT_STOKEN}"

read -r -p "BAIDUID (可空):   " BAIDUID
BAIDUID="${BAIDUID:-$CURRENT_BAIDUID}"

# 写 .env
cat > "$ENV_FILE" <<EOF
# Baidu Netdisk Skill — 凭证（自动生成于 $(date '+%Y-%m-%d %H:%M:%S')）
# ⚠️ 绝不要提交到 git（已在 .gitignore 中）

BAIDU_BDUSS=$BDUSS
BAIDU_STOKEN=$STOKEN
BAIDU_BAIDUID=$BAIDUID
EOF

# 限制权限
chmod 600 "$ENV_FILE"
echo ""
echo "[OK] $ENV_FILE 已写入（权限 600）"
echo "    BDUSS 长度:  ${#BDUSS}"
echo "    STOKEN 长度: ${#STOKEN}"
echo "    BAIDUID 长度: ${#BAIDUID}"
echo ""

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

# 检查 python-dotenv
if ! "$PY" -c "import dotenv" 2>/dev/null; then
    echo "[i] 检测到未装 python-dotenv，尝试安装..."
    "$PY" -m pip install python-dotenv 2>&1 | tail -3 || {
        echo "[!] 安装失败。脚本仍可用（环境变量方式）"
        echo "    手动安装: $PY -m pip install python-dotenv"
    }
    echo ""
fi

# 跑 quota 验证
PCS="$ROOT_DIR/scripts/baidu_pcs.py"

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
cd "$ROOT_DIR"  # 让 .env 自动被找到
"$PY" "$PCS" list /apps/bypy/ 2>&1 | head -20 || echo "[i] /apps/bypy/ 不存在或不可访问，正常。"

echo ""
echo "============================================"
echo "[✓] 设置完成！"
echo "============================================"
echo ""
echo ".env 文件已就位。常用命令（任意目录）："
echo ""
echo "  # 看容量"
echo "  cd $ROOT_DIR"
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
echo "⚠️ 千万不要把 .env 提交到任何 git 仓库！"
