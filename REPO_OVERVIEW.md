# Mox 仓库导览 (给开发者/AI 助手)

> 请先通读本文件，再开始任务，避免在错误的地方改动。

## 项目简介

Mox 是 LLM 对抗攻防平台：FastAPI 后端 + React (React 19 + Vite 6 + Tailwind 4) 前端。

## 前端路由结构 (Hub 模式)

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | SecurityDashboard | 安全总览 |
| `/tasks` | TaskProgressPage | 任务调度 |
| `/attack` | AttackHubPage | 单点渗透（基础/高级/新型/Agent/多模态） |
| `/testing` | AutoTestingHubPage | 自动化引擎（画布/红队/攻击循环/OWASP/传统红队） |
| `/evaluation` | EvaluationHubPage | 能力评估（基准/安全卡片/代码安全/偏见） |
| `/defense` | DefensePage | 防御验证 |
| `/governance` | GovernanceHubPage | 资产治理（历史/报告/模板/数据集/审计） |

旧路径（`/auto-redteam`、`/canvas`、`/benchmark` 等）会自动重定向到对应 Hub。

## 攻击循环 (Attack Loop) 状态

| 模块 | 状态 |
|------|------|
| `mox/attack_loop/core.py` | ✅ 真实引擎，使用 `mox.attacks.registry` 主注册表 |
| `mox/routes/attack_loop.py` | ✅ REST API，挂载于 `/api/v1/attack-loop` |
| `frontend/.../AttackLoopPage.jsx` | ✅ 通过 `attackLoopApi` 调用，入口在 `/testing?tab=loop` |

## API 约定

**Canonical 前缀：`/api/v1`** — 所有新代码与前端调用均应使用此路径。

| 前缀 | 状态 | 说明 |
|------|------|------|
| `/api/v1` | ✅ 正式 | 攻击、防御、评估、平台、攻击循环、Agent/多模态等全部能力 |
| `/api` | ⚠️ 兼容层 | 部分路由的临时别名，响应带 `Deprecation` / `Sunset: 2026-12-31` |
| `/api/v2` | ⚠️ 已弃用 | 薄兼容层（`mox/routes/api_v2.py`），内部委托 v1 handler，计划移除 |

- 路由装配：`mox/api.py`（v1 注册全部 router；`/api` 与 `/api/v2` 仅作迁移过渡）
- 共享 handler：`mox/routes/services/`（`attack_service.py`、`specialized_attack.py`、`advanced_handlers.py`）
- 前端封装：`frontend/src/api/index.js`（`API_PREFIX = '/api/v1'`，不调用 v2）
- 环境变量：`VITE_API_URL`（生产部署时设置后端地址）

## 启动方式

```bash
# 后端 (http://localhost:8000, Swagger 在 /docs)
pip install -e .
python -m mox api

# 前端 (http://localhost:3000, Vite 代理 /api -> 8000)
cd frontend
npm install
npm run dev
```

## 关键文件

- 攻击注册表：`mox/attacks/registry.py`
- 攻击循环引擎：`mox/attack_loop/core.py`
- 自动红队 Agent：`mox/auto_redteam/agent.py`
- 画布编排引擎：`mox/workflows/canvas_engine.py`
- API 装配：`mox/api.py`
- 前端路由：`frontend/src/App.jsx`
- 前端 API：`frontend/src/api/index.js`

## 配置

复制 `.env.example` 为 `.env` 填入 API Key。本地测试可用 Ollama (`base_url` 默认 `http://localhost:11434/v1`)。