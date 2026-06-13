# 百度网盘 BDUSS 抓取指南

> 5 分钟搞定，一次设置长期使用。BDUSS 等同于账号密码，请妥善保管。

## 前置条件

- 一个百度账号（已登录 https://pan.baidu.com）
- Chrome / Edge / Firefox 任一浏览器

## 步骤

### 方法 A：一键复制（推荐）

1. 打开 https://pan.baidu.com 并确认已登录
2. 按 `F12` 打开开发者工具
3. 切到 `Console`（控制台）标签
4. 粘贴以下代码并回车：

```javascript
copy(
  "BAIDU_BDUSS=" + document.cookie.match(/BDUSS=([^;]+)/)[1] + "\n" +
  "BAIDU_STOKEN=" + document.cookie.match(/STOKEN=([^;]+)/)[1] + "\n" +
  "BAIDU_BAIDUID=" + document.cookie.match(/BAIDUID=([^;]+)/)[1]
)
```

5. 剪贴板里现在有：

```
BAIDU_BDUSS=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
BAIDU_STOKEN=xxxxxxxxxxxxxxxx
BAIDU_BAIDUID=xxxxxxxx
```

6. 直接粘贴到 shell 的 `~/.bashrc` / `~/.zshrc` 或当前 shell：

```bash
export BAIDU_BDUSS="xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export BAIDU_STOKEN="xxxxxxxxxxxxxxxx"
export BAIDU_BAIDUID="xxxxxxxx"
```

> ⚠️ 上方 `xxxxxxxx` 仅为示例占位符，请替换为你从浏览器抓到的真实 Cookie 值。

### 方法 B：手动从 Application 面板抓

1. F12 → `Application`（应用程序）标签
2. 左侧 `Storage` → `Cookies` → `https://pan.baidu.com`
3. 找到以下三项并复制 Value 列：

| Cookie 名 | 必需 | 说明 |
|-----------|------|------|
| `BDUSS` | ✅ 必需 | 主凭证，决定账号身份 |
| `STOKEN` | ⭕ 推荐 | 安全令牌，部分 API 验证 |
| `BAIDUID` | ⭕ 推荐 | 设备指纹 |

4. 按方法 A 步骤 6 设置环境变量

## 验证

```bash
python scripts/baidu_pcs.py quota
```

期望看到容量信息。若报错 `errno=110` / `errno=-1`，说明 Cookie 过期，重新走一遍流程。

## 持久化建议

### 方案 1：shell rc 文件（最简单）

```bash
# ~/.bashrc 或 ~/.zshrc 末尾追加
export BAIDU_BDUSS="..."
export BAIDU_STOKEN="..."
export BAIDU_BAIDUID="..."
```

⚠️ **注意**：如果你的 shell rc 文件是 git tracked，请改用方案 2。

### 方案 2：独立 env 文件 + direnv（推荐）

1. 创建 `~/.baidu_netdisk_env`（chmod 600）：

```bash
chmod 600 ~/.baidu_netdisk_env
cat > ~/.baidu_netdisk_env <<'EOF'
export BAIDU_BDUSS="<你的 BDUSS>"
export BAIDU_STOKEN="<你的 STOKEN>"
export BAIDU_BAIDUID="<你的 BAIDUID>"
EOF
```

2. 在需要用的项目根目录创建 `.envrc`：

```bash
echo 'source ~/.baidu_netdisk_env' > .envrc
direnv allow .
```

3. 进入目录自动加载，离开自动 unset。

### 方案 3：每次手动 export（最安全）

适合临时使用：

```bash
export BAIDU_BDUSS="..." && python scripts/baidu_pcs.py quota
```

## ⚠️ 安全清单

- [ ] BDUSS 文件权限设为 `chmod 600`（仅当前用户可读）
- [ ] BDUSS **绝不**写入 git tracked 文件
- [ ] 换机器 / 公开场合演示完，立刻在 [百度账号设置](https://passport.baidu.com) → 设备管理里撤销
- [ ] 怀疑泄漏？立刻改密码（同时作废所有 BDUSS）

## 常见疑问

**Q: Cookie 多久过期？**
A: 通常 1-3 个月。若调用出现 `errno=110` 就重新抓。

**Q: STOKEN 找不到怎么办？**
A: 部分浏览器 / 隐身模式下不显示 STOKEN。BDUSS 单独可用，但稳定性差一些，建议换浏览器重试。

**Q: 为什么不用 OAuth？**
A: 百度个人网盘 API OAuth 申请极难（需企业资质），Web Cookie 方案是社区通用做法。

**Q: bypy 已经登录过，能复用吗？**
A: 可以！脚本会兜底读取 `~/.bypy/bypy.json` 里的 token，无需重复抓 Cookie。
