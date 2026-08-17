# 部署目录说明

本目录用于放置东鹏海外 AI 协同助手的 FastGPT 部署相关文件。

## 当前进度

| 步骤 | 状态 |
|------|------|
| 1. 安装 Docker / Compose | 已完成（本环境） |
| 2. 生成 `docker-compose.yml` | 已完成 → 见 `fastgpt/`（含密钥，勿提交） |
| 3. 拉取镜像并启动服务 | **下一步** |
| 4. 登录并配置模型 | 待做 |
| 5. 创建东鹏知识库与销售助手 | 待做 |

## 下一步（唯一动作）

```bash
cd deploy/fastgpt
sudo docker compose --profile prepull pull
sudo docker compose up -d
```

启动后访问：`http://127.0.0.1:3000`  
账号：`root`（密码见本机 `fastgpt/CREDENTIALS.local.txt`，勿入库）

## 本仓库提供的模板

| 文件 | 说明 |
|------|------|
| [`env.example`](./env.example) | 环境变量示例（无真实密钥） |
| [`knowledge-base-checklist.md`](./knowledge-base-checklist.md) | 东鹏知识库初始化清单 |
| [`fastgpt/install.sh`](./fastgpt/install.sh) | 官方安装脚本副本 |

完整步骤见 [`../docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md)。
