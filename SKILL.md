---
name: baidu-netdisk
description: 上传文件到百度网盘并生成分享链接、列出/删除网盘内容、查询容量。Use when user wants to (1) Upload a local file or folder to Baidu Netdisk, (2) Generate a permanent or time-limited share link, (3) List, query, or delete files in Baidu Netdisk, (4) Sync a local directory with Baidu Netdisk, or (5) Check remaining storage quota. 通过百度网盘 Web API（与 pan.baidu.com 网页版一致）实现，零外部 SDK 依赖。
---

# 百度网盘工具 Skill

> 触发词：「上传到百度网盘」「生成分享链接」「百度网盘分享」「网盘配额」「同步到百度网盘」「百度网盘 CLI」

通过调用百度网盘 Web API（与 pan.baidu.com 网页版一致）实现上传、下载、列目录、生成分享链接、删除等操作。**完全脱离 bypy** —— bypy 不支持生成分享链接，且 OAuth 流程繁琐，本 Skill 直接用浏览器 Cookie 调 API，一步到位。

## When to Use

- 用户说"把这个文件夹传到百度网盘"
- 用户说"生成一个百度网盘分享链接，提取码 8888"
- 用户说"我的网盘还剩多少空间"
- 用户说"列出 `/apps/bypy/` 下的文件"
- 用户说"同步本地项目到网盘"
- Agent 自动化流程中需要上传产物（如生成的报告、配图）

**不适合**：
- 大量小文件（>1000 个）批量上传 —— 单文件 API 较慢，建议先打包成 zip
- 单文件 > 2GB —— 当前实现走单步上传接口，超大文件需扩展分片上传（未实现）
- 需要 OAuth 长期凭证的自动化（无浏览器场景）—— 本 Skill 依赖浏览器 Cookie 短期凭证

## Authentication

### 环境变量（必须）

| 变量 | 必需 | 说明 |
|------|------|------|
| `BAIDU_BDUSS` | ✅ | 网盘主凭证，最关键的 Cookie |
| `BAIDU_STOKEN` | ⭕ 推荐 | 安全令牌，部分 API 需要 |
| `BAIDU_BAIDUID` | ⭕ 推荐 | 设备指纹 |

### 兜底方案

若环境变量未设置，脚本会尝试从 `~/.bypy/bypy.json` 读取之前 bypy 登录过的凭证。这样**已经用 bypy 登录过的机器可以直接复用**，无需重复抓 Cookie。

### 获取方法

详见 [[references/auth-setup.md]] —— 图文步骤讲解用 F12 开发者工具从 `pan.baidu.com` 抓 BDUSS。

### ⚠️ 安全警告

- **绝不要把 BDUSS 提交到 git**
- **绝不要在脚本里硬编码 BDUSS**（本 Skill 强制走环境变量）
- 用完建议在 [百度网盘设置 → 设备管理](https://pan.baidu.com/settings/security/auth) **撤销 token**
- BDUSS 等同于账号密码，泄漏后他人可完全控制你的网盘

## Commands

完整 CLI 子命令（脚本路径 `scripts/baidu_pcs.py`）：

| 命令 | 用法 | 说明 |
|------|------|------|
| `quota` | `python scripts/baidu_pcs.py quota` | 查询容量（总/已用/剩余） |
| `list` | `python scripts/baidu_pcs.py list <网盘路径>` | 列目录内容 |
| `meta` | `python scripts/baidu_pcs.py meta <网盘路径>` | 查询 fs_id / isdir / size 等元信息 |
| `upload` | `python scripts/baidu_pcs.py upload <本地路径> <网盘路径>` | 上传文件或目录 |
| `download` | `python scripts/baidu_pcs.py download <网盘路径> [本地路径]` | 下载文件或目录 |
| `share` | `python scripts/baidu_pcs.py share <网盘路径> [--code NNNN] [--period N]` | 生成分享链接 |
| `delete` | `python scripts/baidu_pcs.py delete <网盘路径> [<网盘路径>...]` | 删除文件或目录 |

### share 命令详解

```bash
# 永久链接，无提取码
python scripts/baidu_pcs.py share /apps/bypy/agent-skills

# 永久链接，提取码 8888
python scripts/baidu_pcs.py share /apps/bypy/agent-skills --code 8888

# 7 天有效期，提取码 1234
python scripts/baidu_pcs.py share /apps/bypy/agent-skills --code 1234 --period 7

# period 可选值：1 / 7 / 30（其他值百度会拒绝）
```

输出格式：
```
[+] 分享创建成功
    路径:     /apps/bypy/agent-skills
    链接:     https://pan.baidu.com/s/1xxxxx?pwd=8888
    提取码:   8888
    有效期:   永久
    share_id: 1234567890
```

## Endpoints（参考速查）

| 操作 | 方法 | 端点 |
|------|------|------|
| 容量 | GET | `https://pan.baidu.com/api/quota` |
| 列目录 | GET | `https://pan.baidu.com/api/list` |
| 元信息 | GET | `https://pan.baidu.com/api/filemetas` |
| 上传 | POST | `https://pan.baidu.com/api/upload` |
| 创建目录 | POST | `https://pan.baidu.com/api/create` |
| 下载 | GET | `dlink` 字段返回的 URL（自动重定向） |
| 分享 | POST | `https://pan.baidu.com/share/set` |
| 删除 | POST | `https://pan.baidu.com/api/filemanager/delete` |

`bdstoken` 通过 GET `https://pan.baidu.com/` HTML 抓取（regex `"bdstoken"\s*:\s*"([^"]+)"`）。

完整 endpoint/参数/errno 含义见 [[references/api-cheatsheet.md]]。

## Examples

### 1. 一键上传 + 分享（推荐工作流）

```bash
export BAIDU_BDUSS="..."
export BAIDU_STOKEN="..."
# 一步到位：上传整个目录并生成分享链接
bash examples/upload-and-share.sh ./my-project /apps/bypy/my-project 8888
```

### 2. 同步本地文件夹到网盘

```bash
# 配合 cron，每天凌晨 3 点同步备份
bash examples/sync-folder.sh /home/user/projects /apps/bypy/backup
```

### 3. 查询容量

```bash
python scripts/baidu_pcs.py quota
# 总容量: 5.005 TB  (5,497,558,138,880 bytes)
# 已用:   1.42 TB   (1,560,234,567,890 bytes)
# 剩余:   3.58 TB   (3,937,323,570,990 bytes)
```

### 4. 检查目录里有没有指定文件

```bash
python scripts/baidu_pcs.py meta /apps/bypy/agent-skills
# 看 fs_id、isdir、size 即可判断
```

### 5. Agent 自动分享流程

当 Agent 需要把产物分享给用户时：

```python
import subprocess
result = subprocess.run([
    "python", "scripts/baidu_pcs.py", "upload",
    "/tmp/report.pdf", "/apps/bypy/reports/2026-06-13.pdf"
], capture_output=True, text=True)
assert result.returncode == 0

result = subprocess.run([
    "python", "scripts/baidu_pcs.py", "share",
    "/apps/bypy/reports/2026-06-13.pdf", "--code", "8888"
], capture_output=True, text=True)
# 从 result.stdout 提取分享链接
```

## Security Notes

1. **不要把 BDUSS 写入任何 git tracked 文件** —— 本 Skill 设计上规避了这一点
2. **不要在日志里打印完整 BDUSS** —— 如果调试需要，先 print 前 6 位即可
3. **用完即弃**：任务完成后在 [百度账号设置](https://passport.baidu.com/v2/?ucenter) 撤销设备登录
4. **BDUSS 失效迹象**：`errno=110` 或 `errno=-1` 大概率是 BDUSS 过期，重新抓一次即可
5. **网络层**：本 Skill 仅调 `*.baidu.com` 域名，无第三方外发

## 故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| `errno=110` / `-1` | BDUSS 过期 | 重新从浏览器抓（见 auth-setup.md） |
| `errno=-9` | 路径不存在 | 先用 `meta` 确认父目录 |
| `errno=8` | 文件/目录已存在 | 重新生成路径，或在上传时加 `ondup=overwrite` |
| `errno=403` | STOKEN 缺失或过期 | 重新抓 STOKEN |
| 上传 0 字节 | 文件被防火墙拦截 | 检查文件大小 > 0 且可读 |
| `分享链接立即失效` | 触发风控 | 24 小时内不要频繁分享 |

## 清理建议

- 用完 `share` 命令创建的链接若不需要长期保留，调用 `delete` 命令删除网盘上的对应文件即可同时让链接失效
- 想"取消分享但保留文件"，百度网页版有"我的分享 → 取消分享"按钮，API 上对应 endpoint 是 `/share/cancel`（本 Skill 未实现，可参考 api-cheatsheet.md 自加）

## References

- [[references/auth-setup.md]] — 如何从浏览器抓 BDUSS Cookie（图解）
- [[references/api-cheatsheet.md]] — 百度网盘 Web API 完整速查表
- [[examples/upload-and-share.sh]] — 上传 + 分享一键脚本
- [[examples/sync-folder.sh]] — 文件夹同步脚本（可配合 cron）

## 历史

- **2026-06-13**：初版。从临时 `share_to_baidu.py` 升级而来，扩展为完整 CLI（quota/list/meta/upload/download/share/delete）
