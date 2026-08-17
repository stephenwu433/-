# 部署目录说明

本目录用于放置东鹏海外 AI 协同助手的 FastGPT 部署相关文件。

## 推荐做法

1. 在目标服务器新建独立目录（示例：`/opt/dongpeng-fastgpt`）  
2. 使用官方交互式脚本生成 `docker-compose.yml`：  

```bash
FASTGPT_DEPLOY_BASE_URL=https://doc.fastgpt.cn \
  bash <(curl -fsSL https://doc.fastgpt.cn/deploy/install.sh)
```

3. 将生成的 `docker-compose.yml`、`.env`（如有）、`config.json`（如有）备份到本仓库的 `deploy/` 或公司私有配置仓（**勿提交真实密钥与密码**）  

## 本仓库提供的模板

| 文件 | 说明 |
|------|------|
| [`env.example`](./env.example) | 环境变量示例（无真实密钥） |
| [`knowledge-base-checklist.md`](./knowledge-base-checklist.md) | 东鹏知识库初始化清单 |

完整步骤见 [`../docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md)。
