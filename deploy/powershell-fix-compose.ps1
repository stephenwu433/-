# 修复损坏的 docker-compose.yml（纯 PowerShell，不依赖 WSL）
# 整段复制到 PowerShell 执行

$DeployDir = Join-Path $HOME "dongpeng-fastgpt"
Set-Location $DeployDir

# 1) 用 curl 重新下载（避免 Invoke-WebRequest 编码问题）
curl.exe -fsSL "https://doc.fastgpt.cn/deploy/docker/v4.15/cn/docker-compose.pg.yml" -o "docker-compose.yml"

if (-not (Test-Path "docker-compose.yml")) {
    Write-Error "下载失败"
    exit 1
}

# 2) 生成密码
$rootPwd = -join ((1..16) | ForEach-Object { "{0:x}" -f (Get-Random -Max 16) })
Write-Host "ROOT 密码（请立刻保存）: $rootPwd" -ForegroundColor Green
[System.IO.File]::WriteAllText((Join-Path $DeployDir "CREDENTIALS.local.txt"), "root / $rootPwd")

# 3) 按行替换（不用容易弄坏 YAML 的正则）
$lines = [System.IO.File]::ReadAllLines((Join-Path $DeployDir "docker-compose.yml"))
for ($i = 0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match "^x-default-root-psw:") {
        $lines[$i] = "x-default-root-psw: &x-default-root-psw '$rootPwd'"
    }
    elseif ($lines[$i] -match "^x-fe-domain:") {
        $lines[$i] = "x-fe-domain: &x-fe-domain 'http://127.0.0.1:3000'"
    }
    elseif ($lines[$i] -match "^x-agent-sandbox-proxy-url:") {
        $lines[$i] = "x-agent-sandbox-proxy-url: &x-agent-sandbox-proxy-url 'ws://127.0.0.1:3006'"
    }
    elseif ($lines[$i] -match "^\s*SSE_MCP_SERVER_PROXY_ENDPOINT:\s*$") {
        $lines[$i] = "  SSE_MCP_SERVER_PROXY_ENDPOINT: http://127.0.0.1:3003"
    }
}

# 4) 无 BOM 的 UTF-8 写回（Docker 才能正确读取）
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllLines((Join-Path $DeployDir "docker-compose.yml"), $lines, $utf8NoBom)

Write-Host "已修复。请核对前几行：" -ForegroundColor Cyan
Get-Content ".\docker-compose.yml" -TotalCount 15

Write-Host ""
Write-Host "若上面看起来正常，再执行：" -ForegroundColor Yellow
Write-Host "docker compose --profile prepull pull"
Write-Host "docker compose up -d"
