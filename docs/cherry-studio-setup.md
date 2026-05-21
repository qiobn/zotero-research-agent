# Cherry Studio 配置指南 — Zotero Research Assistant

本文档面向实验室成员，说明如何在 Cherry Studio 中接入 Zotero Research Assistant MCP 服务。

---

## 前置条件

1. **Zotero 7** 已安装并运行，本地 API 已开启
   - 打开 Zotero → 编辑 → 首选项 → 高级 → 勾选「Allow other applications on this computer to communicate with Zotero」
   - 确认可访问 `http://localhost:23119/api/`

2. **Cherry Studio** 已安装（[下载页](https://cherry-ai.com/)）

3. MCP 服务器已安装（找你的师兄/师姐要安装脚本，或按下面的「服务端安装」操作）

---

## 服务端安装（仅部署者需做一次）

```bash
# 1. 安装 Python 环境（推荐 3.11+）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 克隆项目
git clone <你的仓库地址> ~/project
cd ~/project

# 3. 创建虚拟环境 & 安装依赖
uv venv .venv --python 3.13
source .venv/bin/activate
uv pip install -e ".[dev]"

# 4. 创建配置文件
cp .env.example .env
# 编辑 .env 确认 ZOTERO_LOCAL=true

# 5. 首次索引（需 Zotero 运行中）
python scripts/index_library.py

# 6. 验证
python -c "from project_a_mcp.server import mcp; print('OK')"
```

索引完成后，所有 PDF 的全文段落都会存入本地向量数据库，支持语义搜索。

---

## Cherry Studio 配置

### 第 1 步：打开 MCP 设置

Cherry Studio → 设置 → MCP 服务器

### 第 2 步：添加 MCP 服务

点击「添加」，选择「命令行（stdio）」模式，填入以下内容：

| 字段 | 值 |
|---|---|
| 名称 | Zotero Research Assistant |
| 命令 | `/path/to/project/.venv/bin/python` |
| 参数 | `-m project_a_mcp.server` |
| 工作目录 | `/path/to/project` |

> 把 `/path/to/project` 替换为你实际的项目路径，比如 `/Users/xxx/project`。

或者直接粘贴 JSON 配置（部分版本支持）：

```json
{
  "mcpServers": {
    "zra-mcp": {
      "command": "/path/to/project/.venv/bin/python",
      "args": ["-m", "project_a_mcp.server"],
      "cwd": "/path/to/project"
    }
  }
}
```

### 第 3 步：测试连接

保存后，在 Cherry Studio 新建对话，输入：

> 我的 Zotero 库里有哪些集合？

如果看到集合列表，说明连接成功。

---

## 可用功能（13 个工具）

### 发现论文

| 你说... | AI 调用的工具 |
|---|---|
| 帮我找关于城市公共服务的论文 | `search_papers` |
| 找 2024 年以后的 LLM agent 论文 | `search_papers`（带年份过滤） |
| 找跟这篇类似的论文 [key] | `find_similar_papers` |
| 我的库里有哪些文件夹 | `browse_library` |
| 最近加了什么论文 | `browse_library` |
| 标记为 to-read 的论文有哪些 | `search_papers`（带标签过滤） |

### 阅读论文

| 你说... | AI 调用的工具 |
|---|---|
| 这篇论文讲了什么 [key] | `get_paper` |
| 这篇论文哪里讨论了 gravity model | `get_paper_content` |
| 看一下这篇论文第 4 页 | `get_paper_content` |
| 我在这篇论文上划了哪些重点 | `get_paper_content`（annotations） |

### 写作引用

| 你说... | AI 调用的工具 |
|---|---|
| 我这段话能引哪些文献（附你写的段落）| `suggest_citations` |
| 把这 3 篇导出成 BibTeX | `export_bibliography` |

### 管理库

| 你说... | AI 调用的工具 |
|---|---|
| 给这篇论文加个笔记（摘要/想法）| `add_note` |
| 给这些论文打个 reviewed 标签 | `edit_tags` |

### 运维

| 你说... | AI 调用的工具 |
|---|---|
| 我刚加了新论文，更新一下索引 | `sync_index` |

---

## 使用技巧

1. **先搜后读**：先用自然语言描述你想找的论文，拿到结果后再对具体某篇说「详细看看这篇」
2. **引用工作流**：写论文时，把你写的段落直接粘给 AI，说「帮我为这段找引用」，然后说「导出 BibTeX」
3. **新论文入库**：在 Zotero 里添加新论文 → 跟 AI 说「更新一下索引」→ 新论文即可被搜索到
4. **写操作是安全的**：加笔记和改标签默认只做预览，AI 会问你确认后才执行

---

## 常见问题

### Q: 搜不到我刚加的论文？

A: 跟 AI 说「同步一下索引」（`sync_index`）。索引现在支持增量更新——只会处理新增和修改的论文，不会重新解析已有论文。如果切换了嵌入模型，会自动触发全量重建。

### Q: 中文搜索效果好吗？

A: 嵌入模型用的是 BAAI/bge-m3，同时支持中英文。中文检索质量远优于默认英文模型。

### Q: 能修改我库里的论文信息吗？

A: 目前 Zotero 本地 API 是只读的。加笔记和改标签需要配置 Zotero Web API（需要 API key）。预览功能始终可用。

### Q: AI 怎么知道该用哪个工具？

A: 每个工具的描述都针对一种明确的用途设计，不存在功能重叠。你正常说话就行，AI 会自动选对工具。

---

## 模型推荐

Cherry Studio 需要配置一个 LLM 来驱动对话。推荐：

| 模型 | 提供商 | 优点 | 成本 |
|---|---|---|---|
| Claude 3.5 Sonnet | Anthropic API | tool calling 最强，中文好 | 中 |
| GPT-4o | OpenAI API | 全面稳定 | 中 |
| DeepSeek-V3 | DeepSeek API | 性价比极高，中文优秀 | 低 |
| Qwen2.5-72B | 阿里 API | 中文最强，开源可本地 | 低/免费 |
| Ollama 本地模型 | 本地 | 免费，隐私，无限调用 | 硬件 |

> 配好 LLM API key 后，在 Cherry Studio 对话设置里选择对应模型即可。
