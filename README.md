# my_agent · Hello-Agents 学习记录

记录学习 Hello-Agents 时的代码练习、Notebook、知识笔记和每日进度。保留手写 Agent 与框架练习，逐步学习模型调用、ReAct、Plan-and-Solve、Reflection、记忆与 RAG。

本仓库是持续更新的学习项目。代码存在不代表已完成验收，运行结果与待解决问题请记录在 [学习进度](docs/progress/README.md) 中。

## 目录

```text
my_agent/
├── examples/                 # 按教材章节整理的可运行脚本
│   ├── ch01/travel_agent.py  # 天气查询与景点推荐
│   ├── ch04/                # 模型调用、ReAct、Plan-and-Solve
│   └── ch08/memory_rag.py    # 记忆与知识检索示例
├── notebooks/               # 交互式学习与实验
│   ├── ch04/reflection.ipynb
│   └── ch07/                # 框架入门、SimpleAgent、ReActAgent
├── src/my_agent/            # 共用配置与手写 LLM 客户端
├── scripts/ch08/            # 第八章配置检查与环境修复工具
├── docs/
│   ├── notes/               # 知识笔记、问答与 Python 语法速查
│   ├── assets/              # 笔记配图
│   ├── progress/            # 按日期记录的学习日志
│   ├── archive/             # 保留的早期学习计划
│   ├── setup.md             # 环境配置与第八章运行说明
│   └── migration.md         # 原文件名与新位置对应表
├── data/                    # 本地数据库、原始运行日志与旧环境快照
├── pyproject.toml           # 本地 Python 包配置
├── requirements.txt         # 手写示例的依赖
├── requirements-framework.txt  # 框架与 Notebook 的额外依赖
└── .env.example             # 环境变量模板
```

## 开始使用

使用 Python 3.11，在项目根目录运行以下 PowerShell 命令：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env  # 首次配置时执行，已有 .env 时不要覆盖
```

在本地 `.env` 中填写 `LLM_API_KEY`、`LLM_BASE_URL` 和 `LLM_MODEL_ID`。天气推荐示例另需 `TAVILY_API_KEY`，ReAct 搜索示例另需 `SERPAPI_API_KEY`。

```powershell
python examples/ch04/llm_call.py
python examples/ch04/plan_and_solve.py
python examples/ch04/react_agent.py
python examples/ch01/travel_agent.py
```

运行框架练习或 Notebook 前，再安装额外依赖：

```powershell
python -m pip install -r requirements-framework.txt
python -m ipykernel install --user --name my-agent --display-name "Python (my_agent)"
python -m jupyterlab
```

在 Notebook 中选择上述内核，并按单元格顺序执行。提交的 Notebook 清空了输出和执行编号，重新运行后可以在本地查看结果。模型调用和搜索会使用你配置的 API 服务。

第八章还需要嵌入服务、Qdrant 和 Neo4j，详见 [环境配置](docs/setup.md)。

## 每天记录与同步

1. 将 [日志模板](docs/progress/_template.md) 复制为 `docs/progress/YYYY-MM-DD.md`。
2. 记录今天学习的内容、代码入口、实际运行结果、遇到的问题与下一步。
3. 在 [进度索引](docs/progress/README.md) 中增加当天链接。
4. 查看变更后提交并同步到 GitHub：

```powershell
git status
git diff
git add examples notebooks src scripts docs README.md
git commit -m "study: YYYY-MM-DD 记录学习主题与解决的问题"
git push origin main
```

环境配置文件或依赖有变化时，按需单独 `git add` 对应文件。`.env`、数据库、原始 trace、缓存和 `data/local_archive/` 已被忽略；值得保留的结果请脱敏后写入学习日志或笔记。

## 学习资料

- [Python 惯用法速补](docs/notes/Python惯用法速补.md)
- [D1 问答](docs/notes/day01_qa.md) 与 [回顾配图](docs/assets/day01_qa_review.png)
- [目录迁移说明](docs/migration.md)
- [早期 D1 学习计划（归档）](docs/archive/D1使用文档.md)

教程代码与个人练习并存。当前整理保留了练习逻辑；后续功能修正与评测结果应通过单独提交记录。
