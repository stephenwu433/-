# PlanFlow（前端）

Next.js + Clerk + 团队 / 项目 / 邀请 / 排期日历。

## 本地启动

开两个终端：后端见 `../backend/README.md`，前端：

```bash
cd planflow
npm install
npm run dev
```

打开 http://localhost:3000

## 功能（小白地图）

1. `/teams` 我的团队  
2. `/teams/{id}` 项目、成员、邀请、项目排期  
3. `/teams/{id}/projects/{projectId}` **具体任务**（待办/进行中/完成、负责人、截止日期）  
4. `/teams/{id}/calendar` 排期日历  
5. `/invites/{token}` 接受邀请  

## 说明

仓库里的「梅见」文档是另一套品牌洞察系统。当前 PlanFlow 做的是**团队协作排期**主链路；洞察/飞书等可后续再接。
