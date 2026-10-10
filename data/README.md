# 本地运行数据

这里保存数据库、原始 trace 和环境快照，内容默认不上传 GitHub。

- `memory_data/`：原 `code/memory_data/` 的 SQLite 记忆数据。
- `memory/traces/`：原 `code/memory/traces/` 的 HTML 与 JSONL 运行记录。
- `traces/`：后续手写 Agent 的运行日志。
- `local_archive/`：旧 Notebook 检查点、缓存、重复编辑器配置和 Qdrant 源码快照。

第八章示例会将工作目录设到这里，让框架的相对路径产物集中存放。旧数据文件已移动到对应位置，没有清空数据库。

如需保存学习成果，请将相关结果脱敏后整理进 `docs/progress/` 或 `docs/notes/`；不要直接提交服务凭证或完整对话 trace。
