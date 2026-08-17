# 不依赖 WSL：用 PowerShell 下载并生成本地 FastGPT 配置
# 在 PowerShell 中整段执行

$DeployDir = Join-Path $HOME "dongpeng-fastgpt"
New-Item -ItemType Directory -Force -Path $DeployDir | Out-Null
Set-Location $DeployDir

# 1) 下载 compose
$composeUrl = "https://doc.fastgpt.cn/deploy/docker/v4.15/cn/docker-compose.pg.yml"
Invoke-WebRequest -Uri $composeUrl -OutFile "docker-compose.yml"

# 2) 生成本地密码（请复制保存）
$rootPwd = -join ((1..16) | ForEach-Object { "{0:x}" -f (Get-Random -Max 16) })
Write-Host "ROOT 密码（请立刻保存）: $rootPwd" -ForegroundColor Green
Set-Content -Path "CREDENTIALS.local.txt" -Value "root / $rootPwd`nhttp://127.0.0.1:3000" -Encoding UTF8

# 3) 写入本机访问地址与密码
$content = Get-Content "docker-compose.yml" -Raw
$content = $content -replace "x-default-root-psw: &x-default-root-psw '1234'", "x-default-root-psw: &x-default-root-psw '$rootPwd'"
$content = $content -replace "x-fe-domain: &x-fe-domain ''", "x-fe-domain: &x-fe-domain 'http://127.0.0.1:3000'"
$content = $content -replace "x-agent-sandbox-proxy-url: &x-agent-sandbox-proxy-url ''", "x-agent-sandbox-proxy-url: &x-agent-sandbox-proxy-url 'ws://127.0.0.1:3006'"

# MCP 地址（若模板里该行为空，补上 localhost）
$content = $content -replace "(?m)^(\s*SSE_MCP_SERVER_PROXY_ENDPOINT:\s*).*$", '${1}http://127.0.0.1:3003'

Set-Content -Path "docker-compose.yml" -Value $content -Encoding UTF8

Write-Host ""
Write-Host "配置已生成: $DeployDir\docker-compose.yml" -ForegroundColor Cyan
Write-Host "下一步再执行: docker compose --profile prepull pull" -ForegroundColor Yellow
Get-ChildItem
