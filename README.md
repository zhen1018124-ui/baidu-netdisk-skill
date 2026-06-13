<div align="center">

# 🚀 百度网盘命令行神器
# Baidu Netdisk CLI · Permanent Share Links in One Command

### **32KB Python 脚本 · 一行命令生成分享链接 · bypy 永远做不到的事**
### **32KB Python · One-command share links · What bypy cannot do**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.3.0-green.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)
![Size](https://img.shields.io/badge/size-32.6KB-success.svg)
![Platform](https://img.shields.io/badge/platform-Win%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![No OAuth](https://img.shields.io/badge/auth-browser%20cookie-orange.svg)

**Stop clicking 50 times to upload 50 files.**
**一个 32KB 的脚本搞定「上传 + 永久分享链接」全流程。**

[English](#english) · [中文](#中文) · [30 秒上手](#30-秒上手) · [vs bypy](#为什么不用-bypy) · [命令速查](#命令速查) · [Roadmap](#roadmap)

</div>

---

<a id="中文"></a>

## 中文

> ⚡ **痛点直击**：百度网盘官方客户端不支持批处理 / 自动化 / 服务器 / 自定义提取码分享；`bypy` 又不生成分享链接。**这个 32KB 脚本完全脱离 bypy**，直接调百度网盘 Web API —— **一行命令生成永久分享链接 + 自定义提取码**。

---

### 30 秒上手

```bash
# 1. 装依赖
pip install requests python-dotenv

# 2. 抓 Cookie（F12 → Application → Cookies → pan.baidu.com）
#    复制 BDUSS / STOKEN 到 .env

# 3. 验证
python scripts/baidu_pcs.py quota
# 总容量: 5.005 TB  (5,497,558,138,880 bytes)
# 已用:   1.42 TB   (1,560,234,567,890 bytes)
# 剩余:   3.58 TB   (3,937,323,570,990 bytes)

# 4. 一键上传 + 永久分享
python scripts/baidu_pcs.py upload ./my-project /apps/bypy/my-project
python scripts/baidu_pcs.py share /apps/bypy/my-project --code 8888
```

```
[+] 分享创建成功
    路径:     /apps/bypy/my-project
    链接:     https://pan.baidu.com/s/1xxxxx?pwd=8888
    提取码:   8888
    有效期:   永久
```

---

### 为什么不用 bypy？

| 维度 | bypy | **本工具** |
|------|:---:|:---:|
| **生成永久分享链接** | ❌ 不支持 | ✅ **一行命令** |
| **自定义提取码** | ❌ 不支持 | ✅ `--code 8888` |
| **有效期可选** | ❌ | ✅ 永久 / 1 / 7 / 30 天 |
| **依赖 OAuth 流程** | ⚠️ 繁琐 | ✅ 浏览器 Cookie 3 个值 |
| **单文件体积** | ~3MB | **32.6 KB** |
| **外部依赖** | requests + 复杂 setup | 仅 `requests`（`.env` 可选 `python-dotenv`） |
| **单文件上传上限** | 2GB（老 API） | **4GB**（新版三步 API） |
| **跨平台脚本** | ⚠️ bash 优先 | ✅ Win / macOS / Linux / WSL 都有 |
| **AI Agent Skill** | ❌ | ✅ `SKILL.md` 一键接入 Claude Code / Cursor |
| **`errno=2` 删除 bug** | ❌ 没修 | ✅ v1.1.1 已修 |

> bypy 装半天不支持分享链接、OAuth 流程又繁琐？本项目**用一个浏览器 Cookie 搞定一切**。

---

### 适合什么场景？

- 🚀 **批处理**：50 个 G 的素材要挨个点"上传"？脚本一行搞定
- 🤖 **自动化**：每天凌晨 3 点把日志目录同步到网盘做备份
- 🪜 **CI/CD**：发布流水线里产物要直接推到网盘发版
- 💻 **服务器**：Linux 服务器没图形界面、装不了客户端
- 🎯 **分享链接**：想生成一个**永久分享 + 自定义提取码**的链接给客户
- 🧩 **AI Agent**：让 Claude / Cursor 帮你自动上传报告 / 截图到网盘

---

### 快速开始

#### 1. 安装依赖

```bash
pip install requests python-dotenv
```

> `python-dotenv` 让本工具自动读取 `.env` 文件（v1.3.0+ 推荐）。不装也能用（走纯环境变量兼容模式）。

#### 2. 抓 Cookie（一次性，5 分钟）

详见 [references/auth-setup.md](references/auth-setup.md) —— F12 开发者工具图文教程。

**简版步骤**：
1. 浏览器打开 https://pan.baidu.com 并确认登录
2. `F12` → `Application` → `Cookies` → `https://pan.baidu.com`
3. 找到 `BDUSS` / `STOKEN` / `BAIDUID` 三个值，复制到剪贴板

> ⚠️ `STOKEN` 是 **HttpOnly** 的，`document.cookie` 拿不到，**必须到 Application 面板里看**。

#### 3. 写入 .env

**方式 A：交互式脚本（推荐）**

```bash
bash examples/setup-env.sh       # Git Bash / WSL / macOS
.\examples\setup-env.ps1        # PowerShell
```

按提示粘贴三个 Cookie，脚本自动：写 `.env` → `chmod 600` 限制权限 → 跑 quota 验证。

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

> 💡 **不想用 .env？** 直接 `export BAIDU_BDUSS=...` 设环境变量也行，脚本会优先读环境变量。

#### 4. 验证 + 上传 + 分享

```bash
# 验证 Cookie 可用
python scripts/baidu_pcs.py quota

# 上传整个目录
python scripts/baidu_pcs.py upload ./my-project /apps/bypy/my-project

# 生成永久分享链接 + 自定义提取码
python scripts/baidu_pcs.py share /apps/bypy/my-project --code 8888
```

或直接跑一键脚本：

```bash
bash examples/upload-and-share.sh ./my-project /apps/bypy/my-project 8888
```

---

### 命令速查

| 命令 | 用法 | 说明 |
|------|------|------|
| `quota` | `python scripts/baidu_pcs.py quota` | 查询容量 |
| `list` | `python scripts/baidu_pcs.py list <path>` | 列目录 |
| `meta` | `python scripts/baidu_pcs.py meta <path>` | 查询元信息 |
| `upload` | `python scripts/baidu_pcs.py upload <local> <remote>` | 上传文件或目录 |
| `download` | `python scripts/baidu_pcs.py download <remote> [local]` | 下载（取 dlink） |
| `share` | `python scripts/baidu_pcs.py share <remote> [--code NNNN] [--period N]` | **生成分享链接** |
| `delete` | `python scripts/baidu_pcs.py delete <path>...` | 删除文件 / 目录 |

完整参数 / endpoint / errno 速查：[references/api-cheatsheet.md](references/api-cheatsheet.md)

---

### 作为 AI Agent Skill 使用

本仓库同时是一个 **AI Agent Skill**（即 Claude Code / Cursor 等 AI 工具可识别的 Skill 格式）。如果你想让 AI 自动调用：

1. 把 `SKILL.md` 放到 AI Agent 的 Skill 加载路径下
2. AI 看到用户的「上传到百度网盘」「生成百度网盘分享链接」等请求，会自动按 `SKILL.md` 的指引调用 `scripts/baidu_pcs.py`

详见 [SKILL.md](SKILL.md) 的 `description` 触发词。Agent 自动调用示例：

```python
import subprocess
result = subprocess.run([
    "python", "scripts/baidu_pcs.py", "upload",
    "/tmp/report.pdf", "/apps/bypy/reports/2026-06-13.pdf"
], capture_output=True, text=True)
assert result.returncode == 0
```

---

### 目录结构

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
    ├── setup-env.sh / .ps1         ← 一键设置 .env + 验证
    ├── upload-and-share.sh         ← 一键上传并生成分享链接
    └── sync-folder.sh              ← 文件夹同步（可配合 cron）
```

---

### ⚠️ 安全警告

**`BDUSS` 等同于账号密码**，请务必：

- ✅ 只通过环境变量 / `.env` 传入，不要写入脚本
- ✅ 妥善保管，**不要提交到 git**（`.env` 已在 `.gitignore` 中）
- ✅ 用完后在 [百度网盘设置 → 设备管理](https://pan.baidu.com/settings/security/auth) 撤销 token
- ❌ 不要在公开场合演示
- ❌ 不要分享给别人
- ❌ 不要硬编码到代码里（本工具设计上已强制走环境变量）

---

### 已知限制

- 单文件 ≤ **4GB**（单步上传流程；>4GB 需真正分片上传，Roadmap 中）
- 单账号每日上传量受百度会员等级限制
- 频繁分享可能触发风控（`errno=8001`）
- 大量小文件（>1000）批量上传性能一般（建议先 zip）

---

### 故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| `errno=110` / `-1` | BDUSS 过期 | 重新从浏览器抓 |
| `errno=-9` | 路径不存在 | 先用 `meta` 确认父目录 |
| `errno=8` | 文件/目录已存在 | 重新生成路径 |
| `errno=403` | STOKEN 缺失 | 重新抓 STOKEN |
| 上传 0 字节 | 老 API / 网络拦截 | 升级到 v1.1.0+（新版三步 API） |
| 分享链接立即失效 | 触发风控 | 24 小时内不要频繁分享 |

---

<a id="roadmap"></a>

### Roadmap (v1.4 计划)

- [ ] **分片上传**：单文件 > 4GB 的真正分片流程
- [ ] **GitHub / Gitee Release 同步发版**：v1.4 tag + zip 附件
- [ ] **Chrome 插件版**：网页右键「上传到百度网盘」
- [ ] **Windows .exe**：给完全不会 Python 的同事用
- [ ] **错误码中文速查表**

---

### License

MIT — 详见 [LICENSE](LICENSE)

### 参考

- 百度网盘开放平台官方文档：https://pan.baidu.com/union/doc/
- 类似工具 bypy：https://github.com/houtianze/bypy（本项目完全脱离 bypy，直接调 Web API）

---

<a id="english"></a>

## English

**Baidu Netdisk CLI** — A 32KB Python script that talks directly to Baidu Netdisk's public web API (no SDK, no OAuth dance), letting you upload files, generate permanent share links with custom extract codes, and manage your cloud storage from the command line.

### Why not just use `bypy`?

`bypy` is the de-facto Baidu Netdisk CLI, but it has one deal-breaker for many users: **it cannot generate share links**. This tool fills that gap.

| Feature | bypy | **This tool** |
|---|:---:|:---:|
| Permanent share links | ❌ | ✅ one command |
| Custom extract codes | ❌ | ✅ `--code 8888` |
| Auth method | OAuth (heavy) | Browser cookie (3 values) |
| Single-file size | ~3 MB | **32.6 KB** |
| External deps | requests + setup | `requests` only |
| Max upload size | 2 GB (legacy API) | **4 GB** (new 3-step API) |
| AI Agent Skill | ❌ | ✅ `SKILL.md` |
| Cross-platform scripts | bash-first | Win / macOS / Linux / WSL |

### Quick start

```bash
pip install requests python-dotenv
cp .env.example .env
# Edit .env with BDUSS / STOKEN from F12 → Application → Cookies → pan.baidu.com
python scripts/baidu_pcs.py quota
python scripts/baidu_pcs.py upload ./my-project /apps/bypy/my-project
python scripts/baidu_pcs.py share /apps/bypy/my-project --code 8888
```

### Note to international users

This tool targets **Baidu Netdisk** (百度网盘) — a Chinese cloud storage service. You will need a Baidu account and the `pan.baidu.com` cookies to use it. The [中文](#中文) section above is the authoritative reference.

### License

MIT — see [LICENSE](LICENSE)
