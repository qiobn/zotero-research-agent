# 开发任务流程设计与执行

> 本文档是整个项目的开发路线图。两个项目共用一份核心库 `research_core`，
> Project A 包装成 MCP server 供实验室使用，Project B 包装成端到端 Agent 应用用于求职。

---

## 项目定位

| | Project A · Zotero MCP for Lab | Project B · 文献助手 Agent |
|---|---|---|
| **形态** | 纯 MCP 服务器，Cherry Studio 当前端 | 端到端全栈：前端 + 后端 + Agent + RAG + 评测 |
| **用户** | 实验室师弟师妹（无代码基础） | 招聘方 demo + 个人使用 |
| **核心价值** | tool 设计质量、稳定性、低运维 | 架构决策力、RAG 工程、可观测性、真实使用数据 |
| **关系** | 先做 A 验证核心 → A 的真实数据是 B 简历的最强证据 | 在 A 的基础上拓展 agent + 前端 + 评测 |

---

## 仓库结构

```
project/
├── research_core/           # 共享核心库（80% 代码在这里）
│   ├── zotero/              # pyzotero 封装 + Item/Attachment/Annotation 模型
│   ├── parsers/             # PDF/EPUB/DOCX 解析 + chunking + 页码保留
│   ├── rag/                 # indexer / retriever / hybrid search / reranker
│   ├── llm/                 # LiteLLM 包装 + 模型注册表 + 重试
│   ├── tools/               # 纯函数式 tool 集合（search / cite / summarize / digest）
│   └── eval/                # retrieval / answer 评测脚手架
├── project_a_mcp/           # Project A：thin MCP 外壳
│   └── server.py            # fastmcp 注册 research_core.tools
├── project_b_agent/         # Project B：thick agent + 前端外壳
│   └── backend/             # FastAPI + LangGraph agents
├── tests/
│   ├── core/                # research_core 单元测试
│   ├── mcp/                 # MCP tool 集成测试
│   └── agent/               # Agent 端到端测试
├── docs/                    # 文档
├── scripts/                 # 运维/部署脚本
├── pyproject.toml           # 单仓依赖管理
├── .env.example             # 环境变量模板
└── DEVELOPMENT.md           # ← 你正在读的这个文件
```

---

## 技术栈总览

### 共享核心 (research_core)

| 层 | 选型 |
|---|---|
| 语言 | Python 3.11+，uv 管理依赖 |
| Zotero | pyzotero + Zotero 7 local API |
| 向量库 | ChromaDB (embedded, SQLite-based) |
| Embedding | bge-m3 / sentence-transformers（中文友好），可选 OpenAI |
| PDF 解析 | PyMuPDF，扫描版可选 OCR fallback |
| LLM | LiteLLM（统一 OpenAI / Claude / Ollama / Gemini） |
| 持久化 | SQLite (aiosqlite) |
| 测试 | pytest + ruff |

### Project A 额外依赖

| 层 | 选型 |
|---|---|
| MCP | fastmcp（stdio + SSE + streamable-http） |
| 部署 | Docker + Caddy/Nginx，实验室服务器一台机器 |

### Project B 额外依赖

| 层 | 选型 |
|---|---|
| Agent 编排 | LangGraph + langgraph-checkpoint-sqlite |
| 结构化输出 | instructor + Pydantic |
| Hybrid RAG | rank-bm25 + bge-reranker |
| Web 搜索 | tavily-python + duckduckgo-search |
| 前端 | Next.js 15 + React 19 + Tailwind v4 + shadcn/ui |
| 前端 AI | Vercel AI SDK (@ai-sdk/react) |
| 可观测性 | Langfuse + Sentry |
| 部署 | Vercel (前端) + Fly.io/Render (后端) |

---

## 开发阶段与任务清单

### Phase 0 · 环境初始化 ✅

- [x] 安装 uv 包管理器
- [x] 创建 monorepo 目录结构
- [x] 编写 pyproject.toml（核心依赖 + optional agent/dev 依赖）
- [x] 创建 research_core 各子模块骨架
- [x] 创建 project_a_mcp/server.py 的 MCP 入口
- [x] 创建 project_b_agent/backend/app.py 的 FastAPI 占位
- [x] 创建 .env.example / .gitignore
- [x] 初始化 git 仓库
- [x] 编写本文档（DEVELOPMENT.md）
- [x] `uv pip install -e ".[dev]"` 安装所有依赖
- [x] 跑通 `pytest tests/core/test_chunker.py`

---

### Phase 1 · research_core MVP ✅

> 目标：核心库能跑通「索引一批 PDF → 语义检索 → 返回带页码的结果」

- [x] **1.1 Zotero 客户端验证**
  - Zotero 7 local API 连接成功（端点 `http://127.0.0.1:23119/api`，需将 `pyzotero` 的 `endpoint` 字段覆盖）
  - `ZoteroClient.search_items` / `get_recent` / `get_collections` / `get_tags` 全部对真实库验证通过
  - `get_pdf_items_with_paths` 通过 `~/Zotero/storage/<key>/` 或 `/file` redirect 解析 PDF 本地路径

- [x] **1.2 PDF 解析与 chunking**
  - 对 65 篇真实 PDF 跑 `extract_pdf_text` + `chunk_text`（chunk_size=800, overlap=120）
  - 中英文页码准确
  - `tests/core/test_chunker.py` 3/3 通过

- [x] **1.3 RAG 流水线**
  - `Indexer.index_chunks` 写入 ChromaDB，metadata 含 `item_key/title/year/page_start/page_end/chunk_idx`
  - `Retriever.search` 支持 where 过滤；新增 `search_within_item / get_item_chunks / list_indexed_items`
  - `scripts/index_library.py` 全库一键索引（增量 + force_rebuild），实际索引 **65 PDF → 4618 chunks**

- [ ] **1.4 LLM 集成验证**（待开始）
  - 配置 `.env`，验证 `llm_completion` 对 OpenAI/Ollama 的调用
  - 实现一个简单的 RAG 问答函数：检索 → 拼 prompt → LLM 回答
  - 确认 streaming 正常

---

### Phase 2 · Project A MCP Server（进行中）

> 目标：师弟师妹能在 Cherry Studio 里通过自然语言操作 Zotero。
> 工具表面以**用户意图**而非**底层机制**分类，确保 LLM 不会在功能重叠工具间犹豫。

- [x] **2.1 MCP tool surface 设计与实现** ✅

  **9 个工具，4 个意图类别，零功能重叠：**

  | 类别 | 工具名 | 意图（一句话） |
  |---|---|---|
  | DISCOVER | `search_papers` | 按主题/关键词/过滤找论文（hybrid: keyword + semantic，RRF 合并） |
  | DISCOVER | `find_similar_papers` | 给定一篇论文，找库里类似的论文 |
  | DISCOVER | `browse_library` | 浏览库结构（scope = collections / tags / recent / collection_items）|
  | READ | `get_paper` | 单篇论文的元数据 + 摘要 |
  | READ | `get_paper_content` | 读一篇论文内部的段落（query / page / 默认 + 可选 include_annotations） |
  | WRITE | `suggest_citations` | 为用户草稿段落推荐引用（按论文去重，附 evidence + page） |
  | WRITE | `export_bibliography` | 导出指定论文的 BibTeX / 引文格式 |
  | MANAGE | `add_note` | 给论文加笔记（dry-run + confirm） |
  | MANAGE | `edit_tags` | 批量加/删标签（dry-run + confirm） |
  | ADMIN | `sync_index` | 同步向量库与 Zotero 库（增量 / force_rebuild） |

  设计原则（来自 Writer RAG-MCP 基准 + MCP 2025-06-18 spec）：
  - 工具名 = 动词 + 名词
  - description 明示「什么时候用、什么时候**不要**用」
  - 工具间通过 `item_key` 串联，形成 discover → read → cite → manage 链
  - 在 9 个工具（10-20 安全区下沿），不超过 LLM 选择阈值

- [x] **2.2 写操作安全** ✅
  - `add_note` 与 `edit_tags` 默认 `confirm=False`，先返回 diff 预览
  - 已知约束：Zotero 7 local API **只读**；写操作返回明确提示，指引切换 web API
  - dry-run 内容会附带 `warning` 字段说明此限制

- [ ] **2.3 部署与分发**
  - 编写 `Dockerfile` + `docker-compose.yml`
  - 部署到实验室服务器（SSE / streamable-http 对外）
  - 编写 `docs/cherry-studio-setup.md`：Cherry Studio 配置截图 + JSON 模板
  - 做一次 30 分钟培训

- [ ] **2.4 缺口与下一轮迭代**
  - 中文嵌入：当前默认 ChromaDB 内置 `all-MiniLM-L6-v2` 对中文检索分数偏低，下一步切 `bge-m3`
  - 写支持：评估 Zotero 7.1+ 的 local write 是否开放，否则文档化 web API 路径
  - 未实现但有需求的工具（Phase 2 后期）：`add_paper_by_doi/url`、`manage_collections`、`find_duplicates`
  - 调用日志：接入 Langfuse trace 每个 tool 的调用频次与耗时

---

### Phase 3 · Project B 后端 Agent（第 5-8 周）

> 目标：跑通 Chat / Citation / Deep Research 三个 agent

- [ ] **3.1 Chat Agent（Level 0: RAG 链）**
  - 实现 `/chat` 端点：query → 检索 → 拼 prompt → streaming 回答
  - 回答必须带引用：`[item_key, page]`
  - 会话历史存 SQLite

- [ ] **3.2 Citation Agent（Level 1: tool calling）**
  - 用户贴一段草稿 → agent 调用 `find_citations` 工具
  - 返回推荐引用 + 每条引用对应草稿中的哪句话
  - 支持输出 BibTeX block

- [ ] **3.3 Deep Research Agent（Level 2: LangGraph 状态机）**
  - 设计状态图：Plan → Search(库内+网搜) → Synthesize → Self-Review → Report
  - 用 `instructor` 约束 Planner 输出结构化子问题
  - 用 `langgraph-checkpoint-sqlite` 持久化状态（断点可续）
  - 网搜通过 tavily / duckduckgo

- [ ] **3.4 Hybrid RAG 升级**
  - 加入 BM25（`rank_bm25`）做 hybrid 检索
  - 加入 bge-reranker 做 top-k 重排
  - 建评测集：固定文献 + 固定问答 → 计算 recall@k / MRR / answer faithfulness
  - 把指标写进 README

- [ ] **3.5 MCP 暴露**
  - 把 Project B 自身也注册为 MCP server（同进程，fastmcp）
  - 证明它既是 agent 应用，也能被 Claude Desktop / Cursor 当 tool 提供方

---

### Phase 4 · Project B 前端（第 9-10 周）

> 目标：一个可 demo 的 chat UI + 引用展示 + PDF 预览

- [ ] **4.1 前端骨架**
  - `npx create-next-app` + Tailwind v4 + shadcn/ui
  - 用 `jotai` 做状态管理
  - 实现 chat 页面：消息列表 + 输入框 + streaming 渲染

- [ ] **4.2 AI SDK 集成**
  - `@ai-sdk/react` 的 `useChat` hook 接后端 SSE
  - tool call 结果的 inline 渲染（引用卡片、论文元数据）

- [ ] **4.3 引用展示**
  - 回答中的 `[item_key, page]` 渲染为可点击引用
  - 点击引用弹出论文详情 + 相关段落

- [ ] **4.4 Agent Trace 可视化**（加分项）
  - 展示 Deep Research 的状态流转
  - 每步的耗时、token、检索结果

---

### Phase 5 · 产品化与求职准备（第 11-12 周）

> 目标：公开仓库、在线 demo、简历可用

- [ ] **5.1 可观测性**
  - 接入 Langfuse，trace 每次 LLM / embedding / retrieval 调用
  - 记录耗时、token 用量、成功率
  - 接入 Sentry 做错误监控

- [ ] **5.2 CI/CD**
  - GitHub Actions：PR 自动跑 ruff + pytest + type check
  - 前端加 Playwright smoke test

- [ ] **5.3 部署**
  - 前端 → Vercel
  - 后端 → Fly.io / Render / 自托管
  - 提供 `docker-compose.yml` 一键自托管方案

- [ ] **5.4 文档与展示**
  - 中英文 README
  - 架构图（Mermaid / Excalidraw）
  - Demo 视频（2-3 分钟，展示核心工作流）
  - 一篇 blog 文章（讲架构决策）
  - 落地页（可选，Next.js 静态页）

- [ ] **5.5 求职话术**
  - 「为什么用 LangGraph 而不是自己写 while 循环」
  - 「Hybrid RAG 比纯向量检索 recall@10 提升了 X%」
  - 「Project A 在实验室服务了 N 人，跑了 N 千次调用」
  - 「写操作默认 dry-run + 操作日志，如何保证安全」
  - 「同一核心库两种出口（MCP server + Agent app），说明协议与产品的边界」

---

## 关键原则

1. **先做 A 再做 B**：A 的真实使用数据是 B 简历的最强证据
2. **核心逻辑只在 research_core**：A 和 B 只是不同的外壳
3. **chunk 必须带页码和 item_key**：可追溯证据是研究场景的核心可信度来源
4. **写操作必须 dry-run**：避免 AI 误改 Zotero 库
5. **不提前引入重框架**：Phase 1-2 不需要 LangGraph/LangChain，Phase 3 才上
6. **评测驱动**：retrieval metric 不是"做着玩"，是简历能写的数字
