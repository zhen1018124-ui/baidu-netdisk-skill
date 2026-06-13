# 百度网盘 Web API 速查

> 本 Skill 用到的所有端点、参数、errno 含义。完整 endpoint 列表远超本文档范围，仅收录高频场景。

## 通用约定

- **Base URL**：`https://pan.baidu.com`
- **认证**：Cookie 中带 `BDUSS` / `STOKEN` / `BAIDUID`
- **必带查询参数**：`channel=chunlei&web=1`
- **必带 header**：`User-Agent`（浏览器 UA）、`Referer: https://pan.baidu.com/`、`Origin: https://pan.baidu.com`
- **bdstoken**：所有写操作需要。从 `GET https://pan.baidu.com/` HTML 中 regex `"bdstoken"\s*:\s*"([^"]+)"` 提取。
- **返回格式**：JSON。`errno=0` 表示成功，其他都是错误。

## 高频端点

### 1. 查询容量

```
GET https://pan.baidu.com/api/quota?channel=chunlei&web=1
```

响应：

```json
{
  "errno": 0,
  "total": 5497558138880,
  "used":  1560234567890,
  "request_id": 1234567890
}
```

### 2. 列出目录内容

```
GET https://pan.baidu.com/api/list?dir=<path>&channel=chunlei&web=1
    &page=1&num=100&order=name&desc=0&showempty=0
```

参数：

| 参数 | 说明 |
|------|------|
| `dir` | 目录路径，如 `/apps/bypy/` |
| `page` | 页码（从 1 开始） |
| `num` | 每页条数（最大 1000） |
| `order` | 排序字段：`name` / `time` / `size` |
| `desc` | `0` 升序 / `1` 降序 |

返回 `list[]`，每项包含 `fs_id`、`path`、`server_filename`、`size`、`isdir`（0 文件 / 1 目录）、`server_mtime`、`md5`。

### 3. 查询文件元信息

```
GET https://pan.baidu.com/api/filemetas?target=["<path>"]&dlink=1&channel=chunlei&web=1
```

参数：

| 参数 | 说明 |
|------|------|
| `target` | JSON 数组，单个路径用 `["/apps/bypy/foo.txt"]` |
| `dlink=1` | 返回下载链接（仅文件） |

返回 `info[0]`：

```json
{
  "fs_id": 1234567890,
  "path": "/apps/bypy/foo.txt",
  "server_filename": "foo.txt",
  "size": 1024,
  "isdir": 0,
  "md5": "abc123...",
  "dlink": "https://d.pcs.baidu.com/file/...",
  "server_mtime": 1718000000
}
```

### 4. 上传（新版三步流程，单文件 ≤ 4GB）

> ⚠️ **2026 起百度网盘已废弃 `/api/upload` 单步端点**。新版必须走三步：

#### Step 1: precreate（预创建）

```
POST https://pan.baidu.com/api/precreate?channel=chunlei&web=1
    &app_id=250528&bdstoken=<TOKEN>
form-data:
  path: <目标路径>
  size: <文件字节数>
  isdir: 0
  block_list: ["<整文件md5>"]   # 单 block 文件
  autoinit: 1
```

返回：

```json
{
  "errno": 0,
  "uploadid": "N1-MT...",
  "block_list": [0],   // 0 = 待上传
  "return_type": 1
}
```

#### Step 2: 上传分片到 pcs.baidu.com

```
POST https://pcs.baidu.com/rest/2.0/pcs/file?method=upload
    &app_id=250528&channel=chunlei&clienttype=0&web=1
    &bdstoken=<TOKEN>&uploadid=<UPLOADID>
    &path=<PATH>&partseq=0
multipart/form-data:
  file: <二进制文件>
```

返回（**文件已自动创建**）：

```json
{
  "ctime": 1781339102,
  "fs_id": 815003276452602,
  "md5": "...",
  "path": "/apps/bypy/...",
  "size": 23291
}
```

#### Step 3: create（合并分片，新版可能跳过）

```
POST https://pan.baidu.com/api/create?aip=1&channel=chunlei&web=1
    &app_id=250528&bdstoken=<TOKEN>
form-data:
  path: <目标路径>
  size: <字节数>
  isdir: 0
  block_list: ["<md5>"]
  uploadid: <UPLOADID>
```

> ⚠️ 新版 Step 2 已自动创建文件，Step 3 调用可能返回 `errno=404` —— 这是正常的，忽略即可。

⚠️ **限制**：单文件 ≤ 4GB。更大需扩展真正的分片上传（多 block），本 Skill 未实现。

### 5. 创建目录

```
POST https://pan.baidu.com/api/create?channel=chunlei&web=1
form-data:
  path: <目录路径>
  isdir: 1
  block_list: []
```

### 6. 下载文件

```
GET <dlink URL>  # 跟随重定向
```

`dlink` 是临时链接，会 302 到 `pcs.baidu.com` 的真实下载地址。直接 `curl -L` 或 Python `requests.get(allow_redirects=True)`。

### 7. 生成分享链接 ⭐

```
POST https://pan.baidu.com/share/set?channel=chunlei&clienttype=0&web=1
form-data:
  fid_list: [fs_id]        # JSON 数组
  schannel: 4
  channel_list: []
  period: 0                # 0=永久, 1=1天, 7=7天, 30=30天
  bdstoken: <TOKEN>
  pwd: <提取码>             # 可选，4 位数字
```

成功响应：

```json
{
  "errno": 0,
  "link": "https://pan.baidu.com/s/1xxxxx",
  "shareid": 1234567890,
  "shorturl": "1xxxxx",
  "ctime": 1718000000,
  "pwd": "8888"
}
```

### 8. 删除文件/目录

```
POST https://pan.baidu.com/api/filemanager/delete?channel=chunlei&web=1
    &bdstoken=<TOKEN>&opera=delete
form-data:
  filelist: ["<path>", "<path>"]
  ondup: overwrite
```

> ⚠️ 必须带 `opera=delete` query 参数，否则返回 `errno=2` 参数错误。

### 9. 取消分享（未在 Skill 实现，可参考扩展）

```
POST https://pan.baidu.com/share/cancel?channel=chunlei&web=1&bdstoken=<TOKEN>
form-data:
  shareid_list: [1234567890]
```

## errno 错误码速查

| errno | 含义 | 解决 |
|-------|------|------|
| 0 | 成功 | — |
| -1 | 通用错误（通常是凭证失效） | 重抓 BDUSS |
| -7 | 权限不足 / 文件被锁 | 检查路径权限 |
| -8 | 文件/目录已存在 | 改路径或用 ondup=overwrite |
| -9 | 路径不存在 | 先创建父目录 |
| -30 | 文件/目录已存在（同 -8） | 同上 |
| 2 | 参数错误 | 检查 form-data 字段名 |
| 110 | BDUSS 过期或被踢下线 | 重抓 Cookie |
| 403 | STOKEN 缺失或过期 | 重抓 STOKEN |
| 404 | endpoint 不存在 | 检查 URL 是否拼错 |
| 500 | 服务器内部错误 | 重试，或联系百度反馈 |
| 8001 | 分享失败（频率过高） | 等待 24h 或换账号 |

完整 errno 表参见 https://pan.baidu.com/union/doc/ （百度网盘开放平台官方文档，部分 endpoint 已下线但 errno 表仍权威）。

## 已知限制 / 黑魔法

1. **上传限制**：
   - 单文件 ≤ 2GB（单步接口）
   - 单账号每日上传 ≤ 几 GB（取决于会员等级）
   - 频繁上传触发风控 → `errno=8001` 或静默失败

2. **分享限制**：
   - `period` 只支持 0/1/7/30，其他值返回 errno=2
   - 提取码必须 4 位字符（百度会自动补齐）
   - 风控：`errno=8001` 表示"分享太频繁"，需等待

3. **大文件下载**：
   - 普通用户单文件下载限速 ~100KB/s（不开会员）
   - dlink 是临时链接，**不要缓存**，每次重新取

4. **目录嵌套**：
   - 路径前缀 `/apps/bypy/` 是 bypy 专用，应用上传会落到 `/apps/<app_name>/`
   - 普通上传（无 `app_id`）会落到 `/我的应用数据/` 或网盘根

## 调试技巧

设置 `BAIDU_VERBOSE=1` 让脚本打印额外诊断信息（暂未全部实现，扩展时可加）：

```bash
BAIDU_VERBOSE=1 python scripts/baidu_pcs.py quota
```

直接调 API 时用：

```bash
# 用 curl 调 quota 验证 Cookie
curl -s "https://pan.baidu.com/api/quota?channel=chunlei&web=1" \
  -b "BDUSS=xxx; STOKEN=xxx; BAIDUID=xxx" | python -m json.tool
```
