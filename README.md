# 恒续 Continuum · 长任务桌面 AI Agent Harness

恒续是我开发的一个本地长任务 Agent 运行框架。写它的出发点很直接：Agent 任务一旦超过十几步，就容易跑偏、超预算、中途出错只能从头重来。我给执行过程加上工程化约束——计划先行、敏感操作人工放行、token 预算分档控制、出错从检查点恢复，并且每一步都可回放、可审计。

系统按「会话 — 任务 — 运行」三层组织。后端是 Python + FastAPI Host，通过 WebSocket JSON-RPC 与前端通信；桌面端用 Electron + React，以「深空导航台」为设计语言，把每一次运行的计划、审批、预算和事件轨迹都可视化出来。

核心设计：

- **计划模式**：Agent 先产出分步计划，人工确认后再执行，适合高风险或高成本任务。
- **审批门**：写文件、执行命令、桌面操作等敏感工具按范围（本次 / 会话 / 永久）人工放行。
- **预算控制**：按 token 与模型调用数设置预警、收尾、硬停三档阈值，超限自动进入收尾或停止。
- **检查点恢复**：运行中断后从最近检查点继续，不需要从头重跑。
- **运行探索器**：逐运行回放活动、上下文占用、模型用量、原始事件流，交付物可直接下载。
- **记忆治理**：记忆以提案—评审—批准流程写入核心记忆，可疑条目可隔离并追溯历史。
- **Skill 与 MCP**：内置标准 Skill 目录，支持 MCP 工具服务接入与运行后 Skill 学习沉淀。
- **沙箱与评测**：代码执行沙箱，支持 SWE-bench / FeatureBench 推理评测。

## 架构

```text
desktop/                 Electron + Vite + React 桌面/网页客户端（深空导航台 UI）
├── src/App.tsx          会话、运行、任务、审批、交付物、记忆、偏好等全部视图
├── src/RunExplorer.tsx  运行探索器：预算、上下文、活动、轨迹、原始事件回放
└── electron/            Electron 主进程与预加载桥

backend/
├── continuum/server.py        FastAPI Host：/health、/rpc WebSocket JSON-RPC、静态页面与交付物下载
├── continuum/application.py    应用层：会话、运行、审批、交付物、任务、记忆治理、知识沉淀
├── continuum/agent.py         Agent 循环：工具编排、搜索、规划、反思与总结
├── continuum/tasks.py         持续任务与计划/执行模式
├── continuum/permissions.py   工具权限与审批门
├── continuum/checkpoint.py    运行检查点与崩溃恢复
├── continuum/memory.py       核心记忆提案、评审与隔离
├── continuum/wiki.py         运行知识的 Wiki 化沉淀
├── continuum/skill_learning.py / mcp.py    Skill 学习与 MCP 工具接入
├── continuum/sandbox.py      代码执行沙箱
├── continuum/computer.py     computer-use 桌面操作通道
├── continuum/benchmark.py    SWE-bench / FeatureBench 推理评测
└── continuum/evidence.py     证据留存与运行可审计性
```

## Docker 一键启动

```sh
docker compose build
CONTINUUM_API_KEY=你的_API_Key docker compose up -d
```

服务只监听本机 `127.0.0.1:8765`，浏览器打开 `http://127.0.0.1:8765` 即可使用网页版。

常用环境变量：

| 变量 | 说明 | 默认 |
| --- | --- | --- |
| `CONTINUUM_PROVIDER` | 模型提供方 | `openai` |
| `CONTINUUM_MODEL` | 模型名 | `gpt-4.1-mini` |
| `CONTINUUM_API_KEY` | API Key | 空 |
| `CONTINUUM_BASE_URL` | OpenAI-compatible 接口地址 | `https://api.openai.com/v1` |
| `CONTINUUM_SEARCH_PROVIDER` | 搜索提供方 `auto / tavily / duckduckgo` | `auto` |
| `CONTINUUM_MAX_STEPS` | 单次运行最大步数 | `12` |
| `CONTINUUM_COMPUTER_ENABLED` | 是否启用桌面操作通道 | `false` |

模型同样兼容任意 OpenAI-compatible 服务（如通义百炼、DeepSeek），把 `CONTINUUM_BASE_URL` 指向对应地址即可。

## 桌面端开发

```sh
cd desktop
npm install
npm run dev          # 网页开发模式
npm run electron:dev # Electron 开发模式
npm run build        # 类型检查 + 构建前端与 Electron 入口
npm test             # 单元测试
```

桌面端通过 WebSocket JSON-RPC（`/rpc`）连接 Host，也可通过 `apiConfig.ts` 指向远程部署。

## 后端开发

```sh
cd backend
python -m pip install -r requirements.txt
CONTINUUM_PROVIDER=openai CONTINUUM_MODEL=gpt-4.1-mini python -m continuum.server
```

数据默认写入 `./.continuum`（SQLite），工作目录为 `./workspace`，可通过 `CONTINUUM_DATA_DIR` 与 `CONTINUUM_WORKSPACE_DIR` 调整。

## 评测

支持 SWE-bench 与 FeatureBench 推理评测，详见 [RUN_ON_DOCKER.md](RUN_ON_DOCKER.md)。
