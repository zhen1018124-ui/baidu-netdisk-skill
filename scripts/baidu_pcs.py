#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
baidu_pcs.py — 百度网盘 Web API CLI 工具

通过调用百度网盘 Web API（与 pan.baidu.com 网页版一致）实现上传、下载、
列目录、生成分享链接、删除等操作。

⚠️ 安全约束
- BDUSS / STOKEN / BAIDUID 仅通过环境变量传入，绝不硬编码或写入日志
- 所有请求带标准 User-Agent / Referer / Origin 头，模拟浏览器行为
- 分享链接默认生成 **永久有效**（period=0）；如需限时通过 --period 指定

依赖：requests（环境已有，零新依赖）
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Windows GBK 控制台兼容：强制 UTF-8 输出
# 否则打印 ✓ / ✗ / 中文路径时会 UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass  # Python < 3.7 或已配置环境

# ======== 常量 ========
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
BASE = "https://pan.baidu.com"
TIMEOUT = 30


# ======== 异常 ========
class BaiduError(RuntimeError):
    """百度 API 返回 errno != 0 时抛出"""

    def __init__(self, errno: int, msg: str):
        self.errno = errno
        self.msg = msg
        super().__init__(f"errno={errno} {msg}")


# ======== Session 工厂 ========
def make_session(verbose: bool = False) -> requests.Session:
    """
    从环境变量读取凭证，构造带 Cookie 的 Session。

    凭证来源（按优先级）：
      1. 环境变量 BAIDU_BDUSS / BAIDU_STOKEN / BAIDU_BAIDUID
      2. bypy 缓存文件 ~/.bypy/bypy.json（如果存在）
    """
    bduss = os.environ.get("BAIDU_BDUSS", "").strip()
    stoken = os.environ.get("BAIDU_STOKEN", "").strip()
    baiduid = os.environ.get("BAIDU_BAIDUID", "").strip()

    # 兜底：从 bypy 缓存读
    if not bduss:
        bypy_json = Path.home() / ".bypy" / "bypy.json"
        if bypy_json.exists():
            try:
                data = json.loads(bypy_json.read_text(encoding="utf-8"))
                bduss = data.get("bduss", "")
                stoken = stoken or data.get("stoken", "")
                baiduid = baiduid or data.get("baiduid", "")
                if verbose:
                    print(f"[i] 从 {bypy_json} 读取到凭证", file=sys.stderr)
            except Exception as e:
                if verbose:
                    print(f"[!] 读取 bypy.json 失败: {e}", file=sys.stderr)

    if not bduss:
        print(
            "[!] 缺少 BDUSS。请设置环境变量 BAIDU_BDUSS 后重试。\n"
            "    获取方法见 references/auth-setup.md",
            file=sys.stderr,
        )
        sys.exit(2)

    s = requests.Session()
    s.cookies.set("BDUSS", bduss, domain=".baidu.com")
    s.cookies.set("STOKEN", stoken, domain=".baidu.com")
    s.cookies.set("BAIDUID", baiduid, domain=".baidu.com")
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Referer": f"{BASE}/",
        "Origin": BASE,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    return s


# ======== 通用工具 ========
def get_bdstoken(s: requests.Session) -> str:
    """从首页 HTML 抓 bdstoken。"""
    r = s.get(f"{BASE}/", timeout=TIMEOUT)
    m = re.search(r'"bdstoken"\s*:\s*"([^"]+)"', r.text)
    return m.group(1) if m else ""


def check_ok(data: Dict[str, Any]) -> None:
    """检查 API 返回 errno，非 0 抛出 BaiduError。"""
    errno = data.get("errno", 0)
    if errno != 0:
        msg = data.get("errmsg") or data.get("errortext") or ""
        raise BaiduError(errno, msg)


# ======== 子命令实现 ========
def cmd_quota(args, s: requests.Session) -> int:
    """查看网盘容量。"""
    r = s.get(
        f"{BASE}/api/quota",
        params={"channel": "chunlei", "web": "1"},
        timeout=TIMEOUT,
    )
    data = r.json()
    check_ok(data)

    total = data.get("total", 0)
    used = data.get("used", 0)
    free = total - used

    def human(n: int) -> str:
        tb = 1024 ** 4
        gb = 1024 ** 3
        if n >= tb:
            return f"{n / tb:.3f} TB"
        return f"{n / gb:.2f} GB"

    print(f"总容量: {human(total)}  ({total:,} bytes)")
    print(f"已用:   {human(used)}  ({used:,} bytes)")
    print(f"剩余:   {human(free)}  ({free:,} bytes)")
    return 0


def cmd_list(args, s: requests.Session) -> int:
    """列出目录内容。"""
    path = args.path or "/"
    page = args.page
    size = args.size

    # 先取 dir 里
    r = s.get(
        f"{BASE}/api/list",
        params={
            "dir": path,
            "channel": "chunlei",
            "web": "1",
            "page": page,
            "num": size,
            "order": "name",
            "desc": "0",
            "showempty": "0",
        },
        timeout=TIMEOUT,
    )
    data = r.json()
    check_ok(data)

    items = data.get("list", [])
    if not items:
        print(f"(空目录: {path})")
        return 0

    print(f"路径: {path}  共 {len(items)} 项")
    print(f"{'类型':<6} {'大小':>12}  {'修改时间':<20}  名称")
    print("-" * 80)
    for it in items:
        kind = "目录" if it.get("isdir") == 1 else "文件"
        size_bytes = it.get("size", 0)
        if kind == "目录":
            size_str = "-"
        elif size_bytes >= 1024 ** 2:
            size_str = f"{size_bytes / 1024 ** 2:.1f} MB"
        elif size_bytes >= 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes} B"
        mtime = it.get("server_mtime", 0)
        mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)) if mtime else "-"
        name = it.get("server_filename", "?")
        print(f"{kind:<6} {size_str:>12}  {mtime_str:<20}  {name}")
    return 0


def cmd_meta(args, s: requests.Session) -> int:
    """查询文件/目录元信息。"""
    target = args.path
    r = s.get(
        f"{BASE}/api/filemetas",
        params={
            "target": json.dumps([target], separators=(",", ":")),
            "dlink": "0",
            "channel": "chunlei",
            "web": "1",
        },
        timeout=TIMEOUT,
    )
    data = r.json()
    check_ok(data)

    info = (data.get("info") or [])
    if not info:
        print(f"[!] 未找到: {target}", file=sys.stderr)
        return 1
    item = info[0]
    # 打印关键字段
    keys = [
        "fs_id", "path", "server_filename", "size", "isdir",
        "md5", "server_mtime", "category",
    ]
    print(json.dumps({k: item.get(k) for k in keys}, ensure_ascii=False, indent=2))
    return 0


def cmd_upload(args, s: requests.Session) -> int:
    """
    上传文件 / 目录到网盘。

    单文件走新版三步上传（precreate → pcs.upload → create），≤ 4GB 单 block。
    目录递归上传每个文件，远程子目录不存在则先创建（ensure_dir 走旧 /api/create）。
    """
    local = Path(args.local)
    remote = args.remote.rstrip("/")
    if not local.exists():
        print(f"[!] 本地路径不存在: {local}", file=sys.stderr)
        return 1

    bdstoken = get_bdstoken(s)
    if not bdstoken:
        print("[!] 获取 bdstoken 失败", file=sys.stderr)
        return 1

    files_to_upload: List[tuple] = []
    if local.is_file():
        files_to_upload = [(local, remote)]
    else:
        # 目录：递归
        for p in local.rglob("*"):
            if p.is_file():
                rel = p.relative_to(local).as_posix()
                files_to_upload.append((p, f"{remote}/{rel}"))
        # 确保目标目录存在
        ensure_dir(s, remote)

    if not files_to_upload:
        print(f"[!] 没有可上传的文件: {local}", file=sys.stderr)
        return 1

    print(f"[+] 准备上传 {len(files_to_upload)} 个文件 → {remote}")
    ok_count = 0
    for src, dst in files_to_upload:
        try:
            upload_one(s, src, dst, bdstoken)
            print(f"  ✓ {src} → {dst}")
            ok_count += 1
        except BaiduError as e:
            print(f"  ✗ {src}: {e}", file=sys.stderr)
    print(f"[+] 完成: {ok_count}/{len(files_to_upload)}")
    return 0 if ok_count == len(files_to_upload) else 1


def upload_one(
    s: requests.Session,
    src: Path,
    remote_path: str,
    bdstoken: str,
) -> None:
    """上传单个文件（新版三步流程：precreate → pcs.upload → create）。

    百度网盘新版已废弃 /api/upload 单步端点，改为：
      1. POST /api/precreate  预创建，拿到 uploadid
      2. POST pcs.baidu.com 上传分片（单 block 文件无需分片）
      3. POST /api/create     合并分片（新版 Step 2 已自动完成，此步可能 errno=404）

    单文件 ≤ 4GB 走单 block 流程即可；更大需扩展真正的分片上传（未实现）。
    """
    size = src.stat().st_size
    if size > 4 * 1024 ** 3:
        raise BaiduError(
            -1,
            f"{src} 超过 4GB 单 block 上传上限，请用分片接口（未实现）",
        )

    with open(src, "rb") as f:
        data = f.read()
    block_md5 = hashlib.md5(data).hexdigest()

    # Step 1: precreate（生成 uploadid）
    r = s.post(
        f"{BASE}/api/precreate",
        params={
            "channel": "chunlei",
            "web": "1",
            "app_id": "250528",
            "bdstoken": bdstoken,
        },
        data={
            "path": remote_path,
            "size": str(size),
            "isdir": "0",
            "block_list": json.dumps([block_md5]),
            "autoinit": "1",
        },
        timeout=TIMEOUT,
    )
    pre_resp = r.json()
    check_ok(pre_resp)
    uploadid = pre_resp["uploadid"]

    # Step 2: 上传分片到 pcs.baidu.com
    r = s.post(
        "https://pcs.baidu.com/rest/2.0/pcs/file",
        params={
            "method": "upload",
            "app_id": "250528",
            "channel": "chunlei",
            "clienttype": "0",
            "web": "1",
            "bdstoken": bdstoken,
            "uploadid": uploadid,
            "path": remote_path,
            "partseq": "0",
        },
        files={"file": (src.name, data)},
        timeout=300,
    )
    up_resp = r.json()
    check_ok(up_resp)

    # Step 3: create（新版 Step 2 已自动创建，此步可能 errno=404，忽略）
    r = s.post(
        f"{BASE}/api/create",
        params={
            "aip": "1",
            "channel": "chunlei",
            "web": "1",
            "app_id": "250528",
            "bdstoken": bdstoken,
        },
        data={
            "path": remote_path,
            "size": str(size),
            "isdir": "0",
            "block_list": json.dumps([block_md5]),
            "uploadid": uploadid,
        },
        timeout=TIMEOUT,
    )
    try:
        cr = r.json()
        if cr.get("errno") not in (0, 404):
            # 其它错误上报
            check_ok(cr)
    except Exception:
        # create 步骤偶尔返回非 JSON，忽略（文件已在 Step 2 创建好）
        pass


def ensure_dir(s: requests.Session, remote_dir: str) -> None:
    """确保远程目录存在（递归创建）。"""
    parts = [p for p in remote_dir.split("/") if p]
    cur = ""
    for p in parts:
        cur = f"{cur}/{p}"
        # 创建（已存在会返回 errno=8/-30，忽略）
        s.post(
            f"{BASE}/api/create",
            params={"channel": "chunlei", "web": "1"},
            data={"path": cur, "isdir": "1", "block_list": "[]"},
            timeout=TIMEOUT,
        )


def cmd_download(args, s: requests.Session) -> int:
    """
    下载文件/目录。
    文件：取 dlink → 重定向到真实下载 URL → 保存。
    目录：递归 list + download。
    """
    remote = args.path
    local = Path(args.local or Path(remote).name)

    # 判断是文件还是目录
    try:
        meta = get_meta_raw(s, remote)
    except BaiduError as e:
        print(f"[!] meta 查询失败: {e}", file=sys.stderr)
        return 1

    if meta.get("isdir") == 1:
        print(f"[+] 目录: {remote} → {local}/")
        local.mkdir(parents=True, exist_ok=True)
        items = list_dir_all(s, remote)
        ok_count = 0
        for it in items:
            rel = it["path"].lstrip("/").replace(remote.lstrip("/"), "", 1).lstrip("/")
            dst = local / Path(rel).name if "/" not in rel else local / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                download_one(s, it, dst)
                print(f"  ✓ {it['path']}")
                ok_count += 1
            except BaiduError as e:
                print(f"  ✗ {it['path']}: {e}", file=sys.stderr)
        print(f"[+] 完成: {ok_count}/{len(items)}")
        return 0 if ok_count == len(items) else 1
    else:
        print(f"[+] 文件: {remote} → {local}")
        download_one(s, meta, local)
        return 0


def get_meta_raw(s: requests.Session, path: str) -> Dict[str, Any]:
    r = s.get(
        f"{BASE}/api/filemetas",
        params={
            "target": json.dumps([path], separators=(",", ":")),
            "dlink": "1",
            "channel": "chunlei",
            "web": "1",
        },
        timeout=TIMEOUT,
    )
    data = r.json()
    check_ok(data)
    return (data.get("info") or [{}])[0]


def list_dir_all(s: requests.Session, path: str) -> List[Dict[str, Any]]:
    """递归列出目录下所有文件。"""
    out: List[Dict[str, Any]] = []
    page = 1
    while True:
        r = s.get(
            f"{BASE}/api/list",
            params={
                "dir": path, "channel": "chunlei", "web": "1",
                "page": page, "num": 1000, "order": "name", "desc": "0",
            },
            timeout=TIMEOUT,
        )
        data = r.json()
        check_ok(data)
        items = data.get("list", [])
        if not items:
            break
        for it in items:
            if it.get("isdir") == 1:
                out.extend(list_dir_all(s, it["path"]))
            else:
                out.append(it)
        if len(items) < 1000:
            break
        page += 1
    return out


def download_one(s: requests.Session, meta: Dict[str, Any], dst: Path) -> None:
    dlink = meta.get("dlink")
    if not dlink:
        raise BaiduError(-1, f"{meta.get('path')} 无 dlink")
    # 跟随重定向
    r = s.get(dlink, timeout=300, allow_redirects=True)
    r.raise_for_status()
    dst.write_bytes(r.content)


def cmd_share(args, s: requests.Session) -> int:
    """
    生成分享链接。
    --code 指定提取码（4 位数字）；省略则无提取码
    --period 有效期天数（1/7/30），默认 0 = 永久
    """
    path = args.path
    pwd = args.code
    period = args.period

    bdstoken = get_bdstoken(s)
    if not bdstoken:
        print("[!] 获取 bdstoken 失败", file=sys.stderr)
        return 1

    # 1. 取 fs_id
    meta = get_meta_raw(s, path)
    fs_ids = [meta["fs_id"]]

    # 2. 调 share/set
    payload = {
        "fid_list": json.dumps(fs_ids, separators=(",", ":")),
        "schannel": "4",
        "channel_list": "[]",
        "period": str(period),
        "bdstoken": bdstoken,
    }
    if pwd:
        payload["pwd"] = pwd

    r = s.post(
        f"{BASE}/share/set",
        params={"channel": "chunlei", "clienttype": "0", "web": "1"},
        data=payload,
        timeout=TIMEOUT,
    )
    data = r.json()
    check_ok(data)

    link = data.get("link", "")
    if pwd:
        full = f"{link}?pwd={pwd}"
    else:
        full = link

    print(f"[+] 分享创建成功")
    print(f"    路径:     {path}")
    print(f"    链接:     {full}")
    if pwd:
        print(f"    提取码:   {pwd}")
    if period == 0:
        print(f"    有效期:   永久")
    else:
        print(f"    有效期:   {period} 天")
    print(f"    share_id: {data.get('shareid', '')}")
    return 0


def cmd_delete(args, s: requests.Session) -> int:
    """删除文件 / 目录。"""
    paths = args.paths
    bdstoken = get_bdstoken(s)
    if not bdstoken:
        print("[!] 获取 bdstoken 失败", file=sys.stderr)
        return 1

    r = s.post(
        f"{BASE}/api/filemanager/delete",
        params={"channel": "chunlei", "web": "1", "bdstoken": bdstoken, "opera": "delete"},
        data={
            "filelist": json.dumps(paths, separators=(",", ":")),
            "ondup": "overwrite",
        },
        timeout=TIMEOUT,
    )
    data = r.json()
    check_ok(data)
    print(f"[+] 已删除: {paths}")
    return 0


# ======== CLI 入口 ========
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="baidu_pcs.py",
        description="百度网盘 Web API CLI（上传/下载/分享/列目录/删除）",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # quota
    sub.add_parser("quota", help="查看网盘容量")

    # list
    sp = sub.add_parser("list", help="列出目录内容")
    sp.add_argument("path", nargs="?", default="/", help="网盘路径，默认 /")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--size", type=int, default=100)

    # meta
    sp = sub.add_parser("meta", help="查询文件/目录元信息")
    sp.add_argument("path", help="网盘路径")

    # upload
    sp = sub.add_parser("upload", help="上传文件/目录")
    sp.add_argument("local", help="本地路径")
    sp.add_argument("remote", help="网盘目标路径，如 /apps/bypy/agent-skills")

    # download
    sp = sub.add_parser("download", help="下载文件/目录")
    sp.add_argument("path", help="网盘路径")
    sp.add_argument("local", nargs="?", help="本地保存路径（默认同网盘名）")

    # share
    sp = sub.add_parser("share", help="生成分享链接")
    sp.add_argument("path", help="网盘路径")
    sp.add_argument("--code", help="提取码（如 8888）；省略则无提取码")
    sp.add_argument("--period", type=int, default=0,
                    help="有效期天数（1/7/30），默认 0 = 永久")

    # delete
    sp = sub.add_parser("delete", help="删除文件/目录")
    sp.add_argument("paths", nargs="+", help="一个或多个网盘路径")

    return p


COMMANDS = {
    "quota": cmd_quota,
    "list": cmd_list,
    "meta": cmd_meta,
    "upload": cmd_upload,
    "download": cmd_download,
    "share": cmd_share,
    "delete": cmd_delete,
}


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    verbose = os.environ.get("BAIDU_VERBOSE", "") == "1"
    s = make_session(verbose=verbose)

    handler = COMMANDS.get(args.cmd)
    if handler is None:
        parser.print_help()
        return 2

    try:
        return handler(args, s)
    except BaiduError as e:
        print(f"[!] API 错误: {e}", file=sys.stderr)
        return 1
    except requests.RequestException as e:
        print(f"[!] 网络错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
