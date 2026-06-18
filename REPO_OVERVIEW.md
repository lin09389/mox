# Mox 仓库导览(给开发者/AI 助手)

> 这是「攻击循环(Attack Loop)」功能的**半成品工作区**起点状态。
> 请先通读本文件,再开始任务,避免在错误的地方改动。

## 项目简介
Mox 是 LLM 对抗攻防平台:FastAPI 后端 + React(React 19 + Vite 6 + Tailwind 4 + Recharts)前端。
本仓库当前已有一条**接入前端但未真正实现**的功能线:**攻击循环测试(Attack Loop)**——
用户在前端选择多个模型 + 多种攻击类型 + 多个测试提示,后端循环执行,产出统计与报告。

## 关键:攻击循环功能目前的真实状态(务必先理解)

代码里存在 **三套相关但彼此割裂**的实现,这是当前最大的问题,也是本次任务的核心:

| 文件 | 作用 | 现状 |
|------|------|------|
| `mox/routes/attack_loop.py` | **后端 API 路由**(已挂载到 `/api/v1/attack-loop`,前端在调用) | `simulate_attack()` 是**假的**:用 `random.random() > 0.4` 假装攻击成功,根本没调用任何真实攻击。前端跑出来的「成功率」全是随机数。 |
| `examples/attack_loop_core.py` | 独立的命令行**核心引擎**(执行器/报告/断点/随机提示,功能最完整) | 它有自己**独立**的 `ATTACK_REGISTRY`,直接 `attack.generate_attack()` 真实执行;但**后端 API 完全没用它**,且二者数据结构不统一。 |
| `mox/attacks/registry.py` | 项目的**主攻击注册表**(30+ 种攻击,带工厂函数) | 既不是后端 mock 在用,也不是 core 模块在用——三套各干各的。 |

## 启动方式

```bash
# 后端(默认 http://localhost:8000,Swagger 在 /docs)
pip install -e .
python -m mox api

# 前端(默认 http://localhost:5173)
cd frontend
npm install
npm run dev
```

## 你需要重点查看的文件
- 攻击基类与结果类型:`mox/attacks/base.py`、`mox/core/types.py`(注意 `AttackOutcome` 的字段名)
- 主攻击注册表:`mox/attacks/registry.py`(看 `get_registry()` / `create_attack_instance()`)
- 后端路由(待改):`mox/routes/attack_loop.py`
- 核心引擎(可借鉴/复用):`examples/attack_loop_core.py`(`AttackExecutor` / `ReportGenerator` / `CheckpointManager` / `PromptGenerator` / `TestStatistics`)
- 命令行入口: `examples/attack_loop.py`、`examples/advanced_attack_loop.py`
- 前端页面(待改): `frontend/src/pages/AttackLoopPage.jsx`
- 前端 API 封装:`frontend/src/api/index.js`(`attackLoopApi`)
- 路由/菜单注册:`frontend/src/App.jsx`、`frontend/src/components/Layout.jsx`
- WebSocket 已有能力:`mox/routes/websocket.py`(`ConnectionManager.notify_task_update`)
- FastAPI 装配:`mox/api.py`(看 `_register_routers()`)

## 配置
复制 `.env.example` 为 `.env` 填入 API Key。本地测试可用 Ollama(`base_url` 默认 `http://localhost:11434/v1`)。
