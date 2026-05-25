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
服务器启动时会自动运行增量同步，无需每次手动索引。

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

## 可用功能（16 个工具，5 个类别）

### 发现论文（DISCOVER）

| 你说... | AI 调用的工具 | 说明 |
|---|---|---|
| 帮我找关于城市公共服务的论文 | `search_papers` | 关键词+语义混合搜索，RRF 融合排序，无结果时自动回退到 Zotero 全文索引 |
| 找 2024 年以后的 LLM agent 论文 | `search_papers` | 带年份过滤 |
| 标记为 to-read 的论文有哪些 | `search_papers` | 带标签过滤 |
| 找跟这篇类似的论文 | `find_similar_papers` | 用已知论文的标题+摘要做语义检索 |
| 我的库里有哪些文件夹 | `browse_library` | 查看集合/标签/最近添加 |
| 最近加了什么论文 | `browse_library` | scope=recent |
| 我的库里有没有重复的论文 | `find_duplicates` | 按 DOI 和标题查重 |
| 把这些重复的合并一下，保留第一个 | `merge_duplicates` | 合并 tags/collections/子项，去重附件，垃圾桶删除副本 |

### 阅读论文（READ）

| 你说... | AI 调用的工具 | 说明 |
|---|---|---|
| 这篇论文讲了什么 | `get_paper` | 返回元数据+摘要 |
| 这篇论文哪里讨论了 gravity model | `get_paper_content` | 语义搜索模式，返回最相关段落+页码 |
| 看一下这篇论文第 4 页 | `get_paper_content` | 按页查看模式 |
| 给我看这篇论文的完整内容 | `get_paper_content` | mode=fulltext，最多 50 页 |
| 这篇论文的目录结构是什么 | `get_paper_content` | mode=outline，返回 PDF 标题/层级/页码 |
| 我在这篇论文上划了哪些重点 | `get_paper_content` | include_annotations=true |
| 我在所有论文里标注过哪些关于 methodology 的内容 | `search_annotations` | 跨论文搜索，无数量上限 |
| 帮我在这篇论文第 3 页标注这段话 | `create_annotation` | 在 PDF 上创建高亮注释 |

### 写作引用（WRITE）

| 你说... | AI 调用的工具 | 说明 |
|---|---|---|
| 我这段话能引哪些文献（附你写的段落）| `suggest_citations` | 多句自动拆分独立检索，推荐更多样化的引用 |
| 把这 3 篇导出成 BibTeX | `export_bibliography` | 支持 BibTeX 和 plain 格式 |
| 帮我把这篇 arXiv 论文加到库里 | `add_paper` | 支持 DOI/arXiv/ISBN/BibTeX/URL |
| 把这段 BibTeX 导入到 Zotero | `add_paper` | 直接粘贴 BibTeX 字符串 |
| 帮我把 ISBN 978-xxx 这本书加到库里 | `add_paper` | 通过 OpenLibrary 获取书籍元数据 |

### 管理库（MANAGE）

| 你说... | AI 调用的工具 | 说明 |
|---|---|---|
| 给这篇论文加个笔记 | `add_note` | 默认预览，确认后才保存 |
| 给这些论文打个 reviewed 标签 | `edit_tags` | 支持批量添加/删除标签 |
| 创建一个叫 "毕业论文参考" 的文件夹，把这几篇放进去 | `manage_collections` | 创建集合、添加/移除论文 |

### 运维（ADMIN）

| 你说... | AI 调用的工具 | 说明 |
|---|---|---|
| 我刚加了新论文，更新一下索引 | `sync_index` | 增量更新，只处理变化的论文 |

> 注意：服务器启动时会自动在后台运行增量同步，通常不需要手动触发。

---

## 使用技巧

1. **先搜后读**：先用自然语言描述你想找的论文，拿到结果后再对具体某篇说「详细看看这篇」
2. **引用工作流**：写论文时，把你写的段落直接粘给 AI，说「帮我为这段找引用」，然后说「导出 BibTeX」
3. **添加新论文**：可以直接说「帮我把 10.xxxx/yyyy 这篇加到库里」，也可以粘贴 BibTeX 条目或 ISBN
4. **查看论文结构**：对于长论文，先用 outline 模式看目录，再针对感兴趣的章节提问
5. **索引同步**：服务器启动自动增量同步，也可以手动说「更新一下索引」
6. **写操作是安全的**：加笔记、改标签、管理集合、添加论文、创建注释、合并重复 都默认只做预览，AI 会问你确认后才执行
7. **中英文混搜**：可以用中文问题搜索英文论文，反之亦然（bge-m3 原生支持 100+ 语言）

---

## 常见问题

### Q: 搜不到我刚加的论文？

A: 服务器启动时自动做增量同步。如果之后又加了新论文，跟 AI 说「同步一下索引」即可。增量同步只处理新增和修改的论文。

### Q: 中文搜索效果好吗？

A: 嵌入模型用的是 BAAI/bge-m3，同时支持中英文。中文检索质量远优于默认英文模型。

### Q: 能修改我库里的论文信息吗？

A: Zotero 本地 API 是只读的。要使用写操作，需要在 `.env` 里配置 `ZOTERO_API_KEY` 和 `ZOTERO_LIBRARY_ID`。配置后系统自动启用 Hybrid 模式：读操作走本地 API（快），写操作走 Web API。预览功能无论是否配置 API key 都可用。

### Q: AI 怎么知道该用哪个工具？

A: 每个工具的描述都针对一种明确的用途设计，不存在功能重叠。你正常说话就行，AI 会自动选对工具。

### Q: 我可以用什么格式添加论文？

A: 支持 5 种格式：DOI（如 `10.1234/abcd`）、arXiv ID（如 `2301.00001`）、ISBN（如 `978-0-123456-78-9`）、BibTeX 字符串（直接粘贴 `@article{...}`）、URL（如 `https://arxiv.org/abs/...`）。

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
