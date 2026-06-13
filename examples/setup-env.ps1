# setup-env.ps1 — 交互式写 .env + 跑 quota 验证（持久化）
#
# 用法（PowerShell）：
#   .\examples\setup-env.ps1
#
# 与 setup-and-test.ps1 的区别：
#   setup-and-test.ps1 —— 写到 ~/.baidu_netdisk_env.ps1，依赖 Profile 自动加载
#   setup-env.ps1       —— 写到项目目录 .env，更通用（任意 shell 都用）
#
# 首次使用：自动从 .env.example 复制模板

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir = Resolve-Path (Join-Path $ScriptDir '..')
$EnvFile = Join-Path $RootDir '.env'
$EnvExample = Join-Path $RootDir '.env.example'

Write-Host '============================================' -ForegroundColor Cyan
Write-Host '百度网盘 Skill · .env 设置 + 验证' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''
Write-Host "将写入: $EnvFile"
Write-Host '（输入回车跳过可选项；Ctrl+C 中止）'
Write-Host ''

# 首次使用：复制模板
if (!(Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Copy-Item $EnvExample $EnvFile -Force
        Write-Host '[i] 已从 .env.example 复制模板' -ForegroundColor Yellow
    } else {
        New-Item -ItemType File -Path $EnvFile -Force | Out-Null
        Write-Host '[i] 创建空 .env（没找到 .env.example）' -ForegroundColor Yellow
    }
    Write-Host ''
}

# 读取现有值
function Get-EnvValue([string]$Key) {
    if (!(Test-Path $EnvFile)) { return '' }
    $line = Select-String -Path $EnvFile -Pattern ("^$Key=") -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($line) { return ($line.ToString() -split '=', 2)[1] }
    return ''
}

$CurrentBDUSS = Get-EnvValue 'BAIDU_BDUSS'
$CurrentSTOKEN = Get-EnvValue 'BAIDU_STOKEN'
$CurrentBAIDUID = Get-EnvValue 'BAIDU_BAIDUID'

if ($CurrentBDUSS) {
    Write-Host "[i] 检测到 .env 已有 BDUSS（长度 $($CurrentBDUSS.Length)），可回车保留" -ForegroundColor Yellow
}
Write-Host ''

# 交互式输入
$BDUSS = Read-Host 'BDUSS (192 位)'
if (-not $BDUSS) { $BDUSS = $CurrentBDUSS }
if (-not $BDUSS) {
    Write-Host '[!] BDUSS 不能为空' -ForegroundColor Red
    exit 1
}
if ($BDUSS.Length -lt 100) {
    Write-Host "[!] BDUSS 长度异常: $($BDUSS.Length)" -ForegroundColor Red
    exit 1
}

$STOKEN = Read-Host 'STOKEN (可空)'
if (-not $STOKEN) { $STOKEN = $CurrentSTOKEN }

$BAIDUID = Read-Host 'BAIDUID (可空)'
if (-not $BAIDUID) { $BAIDUID = $CurrentBAIDUID }

# 写 .env
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$content = @"
# Baidu Netdisk Skill — 凭证（自动生成于 $timestamp）
# ⚠️ 绝不要提交到 git（已在 .gitignore 中）

BAIDU_BDUSS=$BDUSS
BAIDU_STOKEN=$STOKEN
BAIDU_BAIDUID=$BAIDUID
"@
[System.IO.File]::WriteAllText($EnvFile, $content, [System.Text.UTF8Encoding]::new($false))

# 限制权限
icacls $EnvFile /inheritance:r /grant:r "${env:USERNAME}:(R,W)" | Out-Null
Write-Host ''
Write-Host "[OK] $EnvFile 已写入（仅 $env:USERNAME 可读写）" -ForegroundColor Green
Write-Host "    BDUSS 长度:  $($BDUSS.Length)"
Write-Host "    STOKEN 长度: $($STOKEN.Length)"
Write-Host "    BAIDUID 长度: $($BAIDUID.Length)"
Write-Host ''

# 找 python
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { $python = (Get-Command py -ErrorAction SilentlyContinue).Source }
if (-not $python) {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { $python = $c; break } }
}
if (-not $python) {
    Write-Host '[!] 找不到 python，请先装 Python 3.8+' -ForegroundColor Red
    exit 2
}
Write-Host "[i] 使用 Python: $python (& $python --version 2>&1)" -ForegroundColor Green
Write-Host ''

# 检查 python-dotenv
$hasDotenv = & $python -c "import dotenv" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host '[i] 检测到未装 python-dotenv，尝试安装...' -ForegroundColor Yellow
    & $python -m pip install python-dotenv 2>&1 | Select-Object -Last 3
    Write-Host ''
}

# 跑 quota 验证
Set-Location $RootDir  # 让 .env 自动被找到
$pcsScript = Join-Path $RootDir 'scripts\baidu_pcs.py'

Write-Host '[1/2] 验证 Cookie...' -ForegroundColor Cyan
& $python $pcsScript quota
if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host '[!] quota 失败。检查点:' -ForegroundColor Red
    Write-Host '    1. BDUSS 是否完整（长度应为 192 左右）'
    Write-Host '    2. STOKEN 是否需要重新抓（若 BDUSS 是新抓的，STOKEN 也要重抓）'
    Write-Host '    3. 在浏览器里 F12 看一下 BDUSS 是不是最新的（可能被踢下线）'
    exit 3
}

Write-Host ''
Write-Host '[2/2] 列一下 /apps/bypy/ 看看能否访问（可选测试）' -ForegroundColor Cyan
& $python $pcsScript list /apps/bypy/ 2>&1 | Select-Object -First 20
if ($LASTEXITCODE -ne 0) {
    Write-Host '[i] /apps/bypy/ 不存在或不可访问，正常。' -ForegroundColor Yellow
}

Write-Host ''
Write-Host '============================================' -ForegroundColor Green
Write-Host '[完成] 设置成功！' -ForegroundColor Green
Write-Host '============================================' -ForegroundColor Green
Write-Host ''
Write-Host '.env 文件已就位。常用命令（任意目录）：' -ForegroundColor Yellow
Write-Host ""
Write-Host "  # 看容量"
Write-Host "  cd $RootDir"
Write-Host "  $python $pcsScript quota"
Write-Host ""
Write-Host "  # 上传 + 分享"
Write-Host "  $python $pcsScript upload .\my-folder /apps/bypy/my-folder"
Write-Host "  $python $pcsScript share /apps/bypy/my-folder --code 8888"
Write-Host ""
Write-Host '[警告] 用完记得在 https://pan.baidu.com 撤销设备登录！' -ForegroundColor Red
Write-Host '[警告] 千万不要把 .env 提交到任何 git 仓库！' -ForegroundColor Red
