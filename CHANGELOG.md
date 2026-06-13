# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-06-13

### Added
- **.env 文件支持**：自动从项目根目录 `.env` 读取凭证
  - 在 `baidu_pcs.py` 顶部加 `try: from dotenv import load_dotenv; load_dotenv()`（向后兼容，未装 `python-dotenv` 也能跑）
  - 新增 `.env.example` 模板（**已 git track**，只有占位符）
  - `.gitignore` 加 `.env` 排除 + `!.env.example` 重新包含
- **新 setup 脚本**（推荐入口）：
  - `examples/setup-env.sh` —— bash / zsh / Git Bash / WSL / macOS 通用
  - `examples/setup-env.ps1` —— PowerShell 原生版
  - 两个脚本都会：交互输入 → 写 `.env` → `chmod 600` / `icacls` 限制权限 → 跑 quota 验证

### Changed
- **setup-and-test.sh / .ps1 改为向后兼容 wrapper**（v1.2.0 用户的命令不破）
  - 跑旧脚本会自动跳转到 `setup-env.sh` / `setup-env.ps1`
  - 老用户能继续 `bash setup-and-test.sh`，行为已统一为"写 .env"

### Documentation
- README 快速开始重写：`.env` 优先（占第 1 位）
- SKILL.md 新增".env 文件示例"段，凭证来源优先级写明
- SKILL.md Endpoints 表修正：上传改三步、删除补 `opera=delete` 参数

### Why this matters
之前的 `setup-and-test.ps1` 用 `SecureString` + `$PROFILE` 持久化，**只有 Windows PowerShell 用着顺手**。
换成 `.env` 之后，bash / PowerShell / zsh / fish / VSCode 全部统一用法，
而且**多项目多账号**、**关掉重开不丢**、**跨平台** 三个维度都更优。

## [1.2.0] - 2026-06-13

### Added
- **PowerShell 原生支持**：`examples/setup-and-test.ps1` 提供 Windows PowerShell 一键设置：
  - 交互式读取 BDUSS / STOKEN（SecureString 输入不回显）
  - 自动检测 Python 路径
  - 写 `~/.baidu_netdisk_env.ps1`（UTF-8 BOM）
  - 限制文件权限（仅当前用户）
  - 修改 `$PROFILE` 自动加载
  - 跑 quota 验证
  - UTF-8 BOM 关键！否则 PowerShell 把中文当 GBK 解析会报错
- env 文件额外加 `Set-Alias python`（PowerShell 默认不继承 Git Bash PATH）
- 加载时打印 `[Baidu Netdisk Skill] Loaded` 提示

### 验证

| 场景 | 结果 |
|------|------|
| 首次跑 ps1（交互输入） | ✅ quota 跑通 |
| 关掉 PowerShell 重开，跑 `python ... quota` | ✅ Profile 自动加载，无需任何操作 |

## [1.1.1] - 2026-06-13

### Fixed
- **`delete` 命令修复**：百度网盘新版 `/api/filemanager/delete` 需要 `opera=delete` 参数（不然返回 `errno=2` 参数错误）。已加到 query string。

## [1.1.0] - 2026-06-13

### Fixed
- **`upload` 命令修复**：百度网盘新版已废弃 `/api/upload` 单步端点，改为三步流程：
  1. `POST /api/precreate` —— 生成 `uploadid`
  2. `POST pcs.baidu.com/rest/2.0/pcs/file?method=upload` —— 上传数据
  3. `POST /api/create` —— 合并分片（新版 Step 2 已自动创建，可能 `errno=404`，忽略）
- **GBK 编码问题**：Windows 控制台默认 GBK 编码会导致 `print("✓ ...") / 中文路径` 时 `UnicodeEncodeError`。已在脚本顶部强制 `sys.stdout.reconfigure(encoding="utf-8")`

### Changed
- 单文件上限从 2GB 提升到 4GB（单 block 流程）

## [1.0.0] - 2026-06-13

### Added
- 初版发布
- 7 个 CLI 子命令：`quota` / `list` / `meta` / `upload` / `download` / `share` / `delete`
- 通过浏览器 Cookie（BDUSS + STOKEN + BAIDUID）调用百度网盘 Web API
- 支持分享链接生成（永久 / 1/7/30 天有效期，可选 4 位提取码）
- 支持递归目录上传
- 支持文件夹同步脚本（`examples/sync-folder.sh`，可配合 cron）
- AI Agent Skill 格式（`SKILL.md`）—— Claude Code / Cursor 等可识别
- 完整的 API 速查表（`references/api-cheatsheet.md`）
- Cookie 获取图文教程（`references/auth-setup.md`）
- 交互式环境变量设置脚本（`examples/setup-and-test.sh`）

### Security
- 强制 BDUSS 走环境变量，不允许硬编码
- 脚本对调用域名仅限 `*.baidu.com`，无第三方外发
- README 顶部明确标注安全警告

### Known Limitations
- 单文件 ≤ 2GB（v1.1.0 提升到 4GB；未实现真正分片上传）
- 大量小文件批量上传性能一般（建议先 zip）
- 频繁分享触发风控需等待