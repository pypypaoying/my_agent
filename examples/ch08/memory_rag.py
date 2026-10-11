"""第 8 章：记忆与 RAG，运行数据统一写入项目 data/。"""

import argparse
import os

from my_agent.config import DATA_DIR, load_project_env
from my_agent.embedding import configure_embedding
from my_agent.output import add_output_argument, error, framework_output, set_verbose, with_style

# 框架导入时可能读取服务配置，先加载根目录 .env。
load_project_env()

with framework_output():
    from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
    from hello_agents.tools import MemoryTool, RAGTool


def build_agent():
    configure_embedding()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(DATA_DIR)
    # 创建LLM实例
    llm = HelloAgentsLLM()

    # 创建工具注册表
    tool_registry = ToolRegistry()

    # 添加记忆工具
    memory_tool = MemoryTool(user_id="user123")
    tool_registry.register_tool(memory_tool)

    # 添加RAG工具
    rag_tool = RAGTool(knowledge_base_path="./knowledge_base")
    if not rag_tool.initialized:
        raise RuntimeError("知识检索服务初始化失败，请检查嵌入与 Qdrant 配置。")
    tool_registry.register_tool(rag_tool)

    # 创建Agent并配置工具
    agent = SimpleAgent(
        name="智能助手",
        llm=llm,
        system_prompt=with_style("你是一个有记忆和知识检索能力的AI助手。"),
        tool_registry=tool_registry
    )

    return agent


def main():
    parser = argparse.ArgumentParser(description="第八章：记忆与 RAG")
    parser.add_argument("--question", default="你好！请记住我叫张三，我是一名Python开发者")
    add_output_argument(parser)
    args = parser.parse_args()
    set_verbose(args.verbose)
    try:
        with framework_output():
            agent = build_agent()
            response = agent.run(args.question)
        if not response:
            raise RuntimeError("模型没有返回有效回答。")
        print(response)
    except Exception as exc:
        error(f"运行失败：{exc}")
        if args.verbose:
            raise
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
