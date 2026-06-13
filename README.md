# 百度网盘工具 · baidu-netdisk

> 通过浏览器 Cookie 调用百度网盘 Web API 的命令行工具集，零外部 SDK 依赖。

支持能力：

- 📦 **上传** 文件或整个目录
- 🔗 **生成分享链接**（永久 / 1/7/30 天，支持提取码）
- 📋 **列出** 网盘目录内容
- 🔍 **查询** 文件元信息
- ⬇️ **下载** 文件（取 dlink）
- 🗑️ **删除** 文件 / 目录
- 💾 **配额查询**（总容量 / 已用 / 剩余）

---

## 快速开始

### 1. 安装依赖

```bash
pip install requests python-dotenv
```

> `python-dotenv` 让本工具自动读取 `.env` 文件（v1.3.0+ 推荐）。不装也能用（走纯环境变量兼容模式）。

### 2. 抓 Cookie（一次性）

详见 [references/auth-setup.md](references/auth-setup.md) —— F12 开发者工具 5 分钟搞定。

简版：

1. 浏览器打开 https://pan.baidu.com 并确认登录
2. F12 → Application → Cookies → https://pan.baidu.com
3. 找到 `BDUSS` / `STOKEN` / `BAIDUID` 三个值，复制到剪贴板

> ⚠️ `STOKEN` 是 HttpOnly，`document.cookie` 拿不到，必须到 Application 面板里看

### 3. 写入 .env

**方式 A：交互式（推荐，bash / zsh）**

```bash
bash examples/setup-env.sh
```

按提示粘贴三个 Cookie，脚本自动：
- 写 `.env` 文件
- `chmod 600` 限制权限
- 跑 quota 验证

**方式 A：交互式（推荐，PowerShell）**

```powershell
.\examples\setup-env.ps1
```

**方式 B：手动编辑**

```bash
cp .env.example .env
chmod 600 .env       # Linux / macOS / Git Bash
# Windows PowerShell: icacls .env /inheritance:r /grant:r "$env:USERNAME:(R,W)"

# 用编辑器打开 .env，把三个值填进去
code .env          # VSCode
# 或 notepad .env  # 记事本
```

`.env` 文件长这样：

```bash
BAIDU_BDUSS=abc123...   # 192 位
BAIDU_STOKEN=def456...  # 64 位
BAIDU_BAIDUID=ghi789... # 32 位（可空）
```

### 4. 验证

```bash
python scripts/baidu_pcs.py quota
```

期望输出：

```
总容量: 5.005 TB  (5,497,558,138,880 bytes)
已用:   1.42 TB   (1,560,234,567,890 bytes)
剩余:   3.58 TB   (3,937,323,570,990 bytes)
```

看到容量数字说明 Cookie 可用。

> 💡 **老用户**：v1.2.0 的 `setup-and-test.sh` / `setup-and-test.ps1` 仍能用（已重定向到 `setup-env.sh` / `setup-env.ps1`）。
>
> 💡 **不想用 .env？** 直接 `export BAIDU_BDUSS=...` 设环境变量也行，脚本会优先读环境变量。

### 4. 上传 + 分享（一行命令）

```bash
# 上传整个目录到网盘
python scripts/baidu_pcs.py upload ./my-project /apps/bypy/my-project

# 生成永久分享链接，提取码 8888
python scripts/baidu_pcs.py share /apps/bypy/my-project --code 8888
```

或直接跑一键脚本：

```bash
bash examples/upload-and-share.sh ./my-project /apps/bypy/my-project 8888
```

---

## 命令速查

| 命令 | 用法 | 说明 |
|------|------|------|
| `quota` | `python scripts/baidu_pcs.py quota` | 查询容量 |
| `list` | `python scripts/baidu_pcs.py list <path>` | 列目录 |
| `meta` | `python scripts/baidu_pcs.py meta <path>` | 查询元信息 |
| `upload` | `python scripts/baidu_pcs.py upload <local> <remote>` | 上传 |
| `download` | `python scripts/baidu_pcs.py download <remote> [local]` | 下载 |
| `share` | `python scripts/baidu_pcs.py share <remote> [--code NNNN] [--period N]` | 生成分享链接 |
| `delete` | `python scripts/baidu_pcs.py delete <path>...` | 删除 |

完整参数 / endpoint 速查：[references/api-cheatsheet.md](references/api-cheatsheet.md)

---

## 作为 AI Agent Skill 使用

本仓库同时是一个 **AI Agent Skill**（即 Claude Code / Cursor 等 AI 工具可识别的 Skill 格式）。如果你想让 AI 自动调用：

1. 把 `SKILL.md` 放到 AI Agent 的 Skill 加载路径下
2. AI 看到用户的"上传到百度网盘""生成百度网盘分享链接"等请求，会自动按 SKILL.md 的指引调用 `scripts/baidu_pcs.py`

详见 [SKILL.md](SKILL.md) 的 `description` 触发词。

---

## 目录结构

```
baidu-netdisk-skill/
├── README.md                       ← 你正在读这个
├── SKILL.md                        ← AI Agent Skill 定义
├── LICENSE                         ← MIT
├── CHANGELOG.md
├── scripts/
│   └── baidu_pcs.py                ← 主 CLI（quota/list/meta/upload/download/share/delete）
├── references/
│   ├── auth-setup.md               ← Cookie 抓取图文教程
│   └── api-cheatsheet.md           ← 百度网盘 Web API 速查
└── examples/
    ├── setup-and-test.sh           ← 一键设置环境变量 + 验证
    ├── upload-and-share.sh         ← 一键上传并生成分享链接
    └── sync-folder.sh              ← 文件夹同步（可配合 cron）
```

---

## 安全警告

⚠️ **BDUSS 等同于账号密码**，请：

- ✅ 只通过环境变量传入，不要写入脚本
- ✅ 妥善保管，不要提交到 git
- ✅ 用完后在 [百度网盘设置](https://pan.baidu.com) → 设备管理里撤销
- ❌ 不要在公开场合演示
- ❌ 不要分享给别人

详细安全清单：[references/auth-setup.md](references/auth-setup.md) 末尾。

---

## 已知限制

- 单文件 ≤ **2GB**（走单步上传接口，超大文件需扩展分片上传，未实现）
- 单账号每日上传量受百度会员等级限制
- 频繁分享可能触发风控（`errno=8001`）

---

## License

MIT — 详见 [LICENSE](LICENSE)

---

## 参考

- 百度网盘开放平台官方文档：https://pan.baidu.com/union/doc/
- 类似工具 bypy：https://github.com/houtianze/bypy（本项目完全脱离 bypy，直接调 Web API）