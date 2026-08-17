# 东鹏海外 FastGPT — 下一步：拉取镜像并启动
# 在「已生成 docker-compose.yml 的目录」中用 PowerShell 运行本脚本，或逐条复制执行。

# 修改为你的实际部署目录
$DeployDir = Join-Path $HOME "dongpeng-fastgpt"
Set-Location $DeployDir

Write-Host "当前目录: $(Get-Location)" -ForegroundColor Cyan

# 检查 Docker
docker version | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker 不可用。请先安装并启动 Docker Desktop。"
    exit 1
}

Write-Host "1/3 拉取镜像（可能较久）..." -ForegroundColor Yellow
docker compose --profile prepull pull
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "2/3 启动服务..." -ForegroundColor Yellow
docker compose up -d
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "3/3 查看状态..." -ForegroundColor Yellow
docker compose ps

Write-Host ""
Write-Host "完成。浏览器打开: http://127.0.0.1:3000" -ForegroundColor Green
Write-Host "账号: root" -ForegroundColor Green
Write-Host "密码: 见安装脚本输出，或 docker-compose.yml 中 x-default-root-psw" -ForegroundColor Green
Start-Process "http://127.0.0.1:3000"
