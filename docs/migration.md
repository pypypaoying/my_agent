# 目录迁移记录

2026-10-11 按用途和教材章节整理目录。`D1/D2/D3` 是原练习标签，与教材章节号不是同一概念。

| 原位置 | 新位置 |
| --- | --- |
| `code/ch1-exercise.py` | `examples/ch01/travel_agent.py` |
| `code/d1-tool_call.py` | `examples/ch04/llm_call.py`（内容为单次 LLM 调用） |
| `code/d2-ReAct.py` | `examples/ch04/react_agent.py` |
| `code/d2-Plan-and-Solve.py` | `examples/ch04/plan_and_solve.py` |
| `code/llm_client.py` | `src/my_agent/llm_client.py` |
| `code/Reflection.ipynb` | `notebooks/ch04/reflection.ipynb` |
| `code/d3-example.ipynb` | `notebooks/ch07/framework_basics.ipynb` |
| `code/simple_agent.ipynb` | `notebooks/ch07/simple_agent.ipynb` |
| `code/react_agent.ipynb` | `notebooks/ch07/react_agent.ipynb` |
| `code/Ch-8/test.py` | `examples/ch08/memory_rag.py` |
| `code/Ch-8/requirements.txt` | `requirements-framework.txt` |
| `code/Ch-8/repair_environment.py` | `scripts/ch08/repair_environment.py` |
| `code/tool-output/check_ch8_embedding.py` | `scripts/ch08/check_embedding.py` |
| `code/tool-output/fix_ch8_configuration.py` | `scripts/ch08/fix_configuration.py` |
| `code/tool-output/qdrant_store.*.py` | `data/local_archive/qdrant_snapshots/`（仅本地保留） |
| `code/memory_data/` | `data/memory_data/` |
| `code/memory/traces/` | `data/memory/traces/` |
| `docs/D1使用文档.md` | `docs/archive/D1使用文档.md` |
| `docs/Python惯用法速补.md` | `docs/notes/Python惯用法速补.md` |
| `docs/D1八股.txt` | `docs/notes/day01_qa.md` |
| `docs/D1问答题回顾.png` | `docs/assets/day01_qa_review.png` |

原编辑器设置、缓存和 Notebook 检查点保存在本地归档。硬编码凭证改为环境变量，共用导入和 `.env` 定位已更新。Notebook 的代码和说明保留，输出与执行编号清空。

早期 D1 文档提到的 `d1_llm_client.py` 四步阶梯脚本在整理前就不存在，归档说明仅作历史学习计划参考。
