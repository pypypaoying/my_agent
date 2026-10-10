> 历史归档：本文保留早期计划与旧路径，当前使用方式以根目录 README 为准。文中四步阶梯脚本未包含在整理前的项目中。

# mini-agent

> 轨道 B ｜ 一个不依赖任何 Agent 框架、从零手写的迷你 Agent。
> 起点：2026-09-29 ｜ 对应规划：Week1（9.28—10.5）→ Hello-Agents Ch7 自研框架

## 这个仓库和 `llm-from-scratch` 什么关系

| 仓库 | 轨道 | 训练什么 | 允许看答案吗 |
|---|---|---|---|
| `D:\llm-from-scratch` | A ｜手写地基 | 从第一性原理推导与实现（micrograd → makemore → 手写 Transformer） | ❌ 不允许，必须白纸推 |
| `D:\mini-agent`（本仓库） | B ｜Agent 工程 | 读懂、调通、改对、讲清（llm_client → ReAct → 记忆 → RAG） | ✅ 允许，而且必须查 SDK 文档 |

两个轨道都是简历上的独立项目，缺一个都不行：
只有 A 你像研究者不像工程师，只有 B 你像调包侠。

## 环境

```bash
conda activate llm          # D:\conda_envs\llm，Python 3.11
cd D:\mini-agent
pip install openai python-dotenv pydantic
copy .env.example .env      # 然后填入你的 API key
```

`.env` 三个字段：

```
LLM_API_KEY=sk-xxxx
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

> ⚠️ `.env` 已在 `.gitignore` 里。**密钥进过 Git 历史就等于泄露**，
> 一旦误提交，去 GitHub Settings → Developer settings 撤销并重新生成 key，
> 不要只删文件（历史里还在）。

## 目录结构

| 路径 | 内容 |
|---|---|
| `d1_llm_client.py` | D1 四步阶梯练习 + 参考答案（**先读 `docs/D1使用文档.md`**） |
| `docs/D1使用文档.md` | 这份代码怎么用、算不算成功、每天目标是什么 |
| `docs/notes/Python惯用法速补.md` | 代码里所有 Python 语法点的最小例子讲解 |
| `demos/` | D1 下午起，你自己写的独立 demo 脚本 |
| `traces/` | D2 起的 JSONL 运行日志 |

## 三条纪律

1. 每一步跑完立刻 commit，message 写「我撞了什么坑」，不写「完成 step1」。
2. 卡住 30 分钟就换策略：查文档 → 搜报错原文 → 打印中间变量 → 缩小规模 → 最后才看参考答案。
3. 没有数字的产出等于没做。每个模块都要有自建的评测集和实测数字。
