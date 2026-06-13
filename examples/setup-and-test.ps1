# setup-and-test.ps1 — 向后兼容入口（重定向到 setup-env.ps1）
#
# ⚠️ v1.3.0+ 推荐使用 setup-env.ps1
# 本脚本保留仅为兼容老命令，行为已统一：
#   - 写 .env 文件（而非 ~/.baidu_netdisk_env.ps1）
#   - 跑 quota 验证
#   - icacls 限制权限
#
# 新用户请直接跑：
#   .\examples\setup-env.ps1

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host '[i] setup-and-test.ps1 在 v1.3.0 之后已被 setup-env.ps1 取代' -ForegroundColor Yellow
Write-Host '[i] 自动跳转到新脚本...' -ForegroundColor Yellow
Write-Host ''

$target = Join-Path $ScriptDir 'setup-env.ps1'
& $target @args
exit $LASTEXITCODE
