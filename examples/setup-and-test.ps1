﻿# setup-and-test.ps1 — PowerShell 版：设置持久化环境变量 + 验证 quota
#
# 用法（PowerShell 里跑）：
#   .\setup-and-test.ps1
#
# 效果：
#   1. 创建 C:\Users\<你>\.baidu_netdisk_env.ps1（带 UTF-8 BOM）
#   2. 限制 env 文件权限（仅当前用户可读写）
#   3. 在 $PROFILE 末尾追加 `.<env 文件路径>`
#   4. 立刻在当前会话加载一次
#   5. 跑 quota 验证 Cookie 有效
#
# 之后：
#   - 重开 PowerShell 自动加载（无需任何操作）
#   - `python` 命令直接可用（不用绝对路径）

# 强制 UTF-8 输出（避免 GBK 乱码）
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# 1. 凭证输入
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "百度网盘 Skill · 环境变量设置 + 验证" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "请依次粘贴以下三个值（输入不回显）："
Write-Host ""

$secureBDUSS = Read-Host "BDUSS (192 位)" -AsSecureString
$secureSTOKEN = Read-Host "STOKEN (64 位, 必填)" -AsSecureString
$BAIDUID = Read-Host "BAIDUID (可空, 回车跳过)"

$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureBDUSS)
$BDUSS = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureSTOKEN)
$STOKEN = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# 2. 校验长度
if ($BDUSS.Length -lt 100) {
    Write-Host "[!] BDUSS 长度异常: $($BDUSS.Length)" -ForegroundColor Red
    exit 1
}
if ($STOKEN.Length -lt 30) {
    Write-Host "[!] STOKEN 长度异常: $($STOKEN.Length)" -ForegroundColor Red
    exit 1
}

# 3. Python 路径自动检测
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) {
    $python = (Get-Command py -ErrorAction SilentlyContinue).Source
}
if (-not $python) {
    # 尝试常见安装位置
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "C:\Python313\python.exe",
        "C:\Python311\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $python = $c; break }
    }
}
if (-not $python) {
    Write-Host "[!] 找不到 python，请先装 Python 3.8+ 或手动设置 \$python" -ForegroundColor Red
    exit 2
}
Write-Host "[i] 使用 Python: $python" -ForegroundColor Green

# 4. 写 env 文件（UTF-8 BOM）
$envFile = "$HOME\.baidu_netdisk_env.ps1"

$baiduidLine = if ($BAIDUID) { "`$env:BAIDU_BAIDUID = '$BAIDUID'" } else { "" }

$envContent = @"
# Baidu Netdisk Skill - Auto-load credentials + python alias

# Python absolute path
`$python = '$python'
Set-Alias -Name python -Value `$python -Force -Scope Global
Set-Alias -Name py -Value `$python -Force -Scope Global

# Credentials
`$env:BAIDU_BDUSS = '$BDUSS'
`$env:BAIDU_STOKEN = '$STOKEN'
$baiduidLine

Write-Host '[Baidu Netdisk Skill] Loaded'
"@

[System.IO.File]::WriteAllText($envFile, $envContent, [System.Text.UTF8Encoding]::new($true))
Write-Host "[OK] Env 文件已写入: $envFile" -ForegroundColor Green

# 5. 限制权限
icacls $envFile /inheritance:r /grant:r "${env:USERNAME}:(R,W)" | Out-Null
Write-Host "[OK] 权限已限制（仅 $env:USERNAME 可读写）" -ForegroundColor Green

# 6. 修改 Profile
$profilePath = $PROFILE
if (!(Test-Path $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
}
$profileMarker = "# Baidu Netdisk Skill auto-load"
if (!(Select-String -Path $profilePath -Pattern $profileMarker -Quiet -ErrorAction SilentlyContinue)) {
    Add-Content -Path $profilePath -Value "`n$profileMarker`n. `"$envFile`""
    Write-Host "[OK] Profile 已更新: $profilePath" -ForegroundColor Green
} else {
    Write-Host "[i] Profile 已包含加载语句，跳过" -ForegroundColor Yellow
}

# 7. 立即加载
. $envFile

# 8. 验证
Write-Host ""
Write-Host "=== 验证 ===" -ForegroundColor Cyan
Write-Host "BDUSS  length: $($env:BAIDU_BDUSS.Length)"
Write-Host "STOKEN length: $($env:BAIDU_STOKEN.Length)"
Write-Host "Python:        $python"

# 9. 跑 quota
Write-Host ""
Write-Host "=== quota 测试 ===" -ForegroundColor Cyan
& python $PSScriptRoot\..\scripts\baidu_pcs.py quota

# 10. 完成提示
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "[完成] 设置成功！" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "下次开 PowerShell 自动加载。常用命令：" -ForegroundColor Yellow
Write-Host "  python $PSScriptRoot\..\scripts\baidu_pcs.py quota"
Write-Host "  python $PSScriptRoot\..\scripts\baidu_pcs.py upload <local> <remote>"
Write-Host "  python $PSScriptRoot\..\scripts\baidu_pcs.py share <remote> --code 8888"
Write-Host ""
Write-Host "[警告] 用完记得在 https://pan.baidu.com 撤销设备登录！" -ForegroundColor Red