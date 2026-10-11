# 环境配置

## 基础示例

使用 Python 3.11，在仓库根目录安装 `requirements.txt`。其中 `-e .` 把 `src/my_agent/` 安装为可编辑包，移动脚本和 Notebook 后仍能导入共用模块。

## 已有 Conda 环境怎么运行

你现有的环境在 `D:\conda_envs\llm`，无需重新创建。先进入项目根目录：

```powershell
cd D:\graduate\my_agent
conda activate D:\conda_envs\llm
python -c "import sys; print(sys.executable); print(sys.version)"
python -m pip install -e .
python examples/ch08/memory_rag.py
```

前两项应分别是 `D:\conda_envs\llm\python.exe` 和 Python 3.11。当前环境已有框架依赖，本项目的可编辑安装已在 2026-10-11 补齐。以后换环境或克隆到另一台电脑，需要在对应环境重新安装。

不想依赖终端激活状态时，可以显式指定解释器：

```powershell
& D:\conda_envs\llm\python.exe examples/ch08/memory_rag.py
```

VS Code 的 Python 解释器也请选择 `D:\conda_envs\llm\python.exe`；Notebook 选择安装了本项目的同一环境内核。

## 为什么 Conda 列表里没有 llm 名称

环境没有丢失。当前 `conda info --envs` 的列表中有 `D:\conda_envs\llm`，只是左侧名称列为空。原因是 `D:\conda_envs` 没有加入 Conda 的 `envs_dirs` 搜索目录；Conda 知道这个环境的完整路径，但不能通过短名称 `llm` 定位它。

按完整路径激活即可。若希望列表显示 `llm`，并支持 `conda activate llm`，可自行执行一次：

```powershell
conda config --append envs_dirs D:\conda_envs
conda info --envs
conda activate llm
```

这会将环境所在的父目录加入用户的 Conda 配置，不会移动或重建环境。本次没有修改该全局配置。

## 导入错误怎么排查

`ModuleNotFoundError: No module named 'my_agent'` 表示当前解释器还没安装本项目。`src/my_agent/` 与示例文件不在同一目录，Python 不能仅靠进入仓库根目录就自动找到它。

使用报错时的同一解释器安装并检查：

```powershell
& D:\conda_envs\llm\python.exe -m pip install -e .
& D:\conda_envs\llm\python.exe -c "import my_agent; print(my_agent.__file__)"
```

输出应指向本仓库的 `src/my_agent/__init__.py`。这一步只解决项目导入；之后若出现 API、向量维度或数据库连接错误，再根据新的报错检查下面的服务配置。

所有示例通过 `my_agent.config.load_project_env()` 加载根目录 `.env`，无需修改本机绝对路径。优先保留终端里已经设置的环境变量。使用统一的 `LLM_MODEL_ID`，也兼容早期配置中的 `LLM_MODEL` 和 `DEEPSEEK_API_KEY`。

| 入口 | 额外配置或依赖 |
| --- | --- |
| `examples/ch04/llm_call.py` | 通用 LLM 配置；这是单次模型调用练习 |
| `examples/ch01/travel_agent.py` | `TAVILY_API_KEY`；天气服务需要联网 |
| `examples/ch04/react_agent.py` | `SERPAPI_API_KEY` |
| `examples/ch04/plan_and_solve.py` | 通用 LLM 配置；运行后输入问题 |
| `notebooks/ch04/reflection.ipynb` | 通用 LLM 配置与 Notebook 环境 |
| `notebooks/ch07/*.ipynb` | `requirements-framework.txt` |

项目只整理目录与配置入口，没有重新验证各服务当前支持的模型与请求选项。模型名请填写你的服务实际支持的 ID。

## 第八章：记忆与 RAG

沿用原练习的 `hello-agents==0.2.0` 与 `qdrant-client==1.19.1`，安装后先执行已有兼容性修复：

```powershell
python -m pip install -r requirements-framework.txt
python scripts/ch08/repair_environment.py
```

修复工具会修改当前 Python 环境中 `hello_agents/memory/storage/qdrant_store.py`，首次修改前保存 `.py.ch8.bak`。重装框架后需要重新运行。它是原练习环境的兼容补丁，后续升级依赖应重新验证。

补丁同时处理搜索 API 和集合统计：新版 `CollectionInfo` 不再包含 `vectors_count`，读取缺失字段时返回 `None`，保留 `points_count` 等有效统计，不将未知数量当成零。遇到旧进程仍引用此字段时，运行修复脚本后重新启动程序或 Notebook 内核。参见 [Qdrant 字段移除说明](https://github.com/qdrant/qdrant/releases/tag/v1.9.0)。

在 `.env` 中配置：

- LLM 服务的模型、地址与密钥。
- 嵌入服务的 `EMBED_*` 变量；`QDRANT_VECTOR_SIZE` 必须与实际嵌入维度一致。
- Qdrant 实例的地址、集合名与可选密钥。
- Neo4j 实例的地址、用户名、密码与数据库名。

按需执行检查或示例：

```powershell
python scripts/ch08/check_embedding.py
python scripts/ch08/check_embedding.py --fix-config
python scripts/ch08/fix_configuration.py
python examples/ch08/memory_rag.py
```

`check_embedding.py` 会调用真实嵌入接口；只有传入 `--fix-config` 时才尝试修正旧版百炼 Base URL。`fix_configuration.py` 会连接 Neo4j 并调整本地 `.env` 中的数据库名和原练习使用的向量维度（1024），仅用于对应嵌入配置。

记忆数据库、知识库和 trace 写入 `data/`。运行不同嵌入模型时，应确认已有集合的维度是否匹配。

### 阿里云与 Hugging Face 的代理冲突

`text-embedding-v3` 是阿里云 API 模型，不需要从 Hugging Face 下载。旧框架会在阿里云调用失败后静默尝试本地模型，并误把这个名称交给 Hugging Face；此时下载超时会掩盖最初的接口错误。

本项目的第八章入口先调用 `my_agent.embedding.configure_embedding()`：按 `EMBED_MODEL_TYPE` 初始化共享模型，失败时显示真实原因并停止，不自动切换模型或向量维度。新增第八章脚本也应在创建 `MemoryTool` / `RAGTool` 前调用它。

阿里云嵌入域名默认加入当前 Python 进程的 `NO_PROXY`，其他域名保留原有代理。可以在 `.env` 中明确设置：

```dotenv
EMBED_MODEL_TYPE=dashscope
EMBED_MODEL_NAME=text-embedding-v3
EMBED_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBED_PROXY_MODE=direct
```

开启代理后，先运行 `python scripts/ch08/check_embedding.py`；显示维度 1024 后，再运行 `python examples/ch08/memory.py` 或 `python examples/ch08/memory_rag.py`。若希望嵌入也走原代理，改为 `EMBED_PROXY_MODE=system`，然后重新启动脚本或 Notebook 内核。

`NO_PROXY` 可绕过 Requests 使用的系统或环境代理，不能改变 TUN 的路由。若代理软件开启 TUN 或强制全局路由，还需在其规则中将 `dashscope.aliyuncs.com` 设为 `DIRECT`，Hugging Face 继续走代理。此设置不修改 Windows 全局代理。

参考：[Requests 代理配置](https://requests.readthedocs.io/en/stable/user/advanced/#proxies)、[阿里云文本嵌入 API](https://www.alibabacloud.com/help/en/model-studio/text-embedding-synchronous-api)。

## Notebook

使用安装过本项目与框架依赖的同一 Python 内核，按顺序运行单元格。仓库里的 Notebook 清空执行输出，以减少无关变更和意外上传敏感信息；实际运行结论应填写到每日学习日志。
