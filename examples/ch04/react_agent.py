import argparse
import os
import re
from my_agent.config import load_project_env
from my_agent.llm_client import HelloAgentsLLM
from my_agent.output import RESPONSE_STYLE, add_output_argument, debug, error, run_quietly, set_verbose
from typing import List, Dict
from serpapi import SerpApiClient
from typing import Dict, Any


# 加载 .env 文件中的环境变量
load_project_env()

# ReAct 提示词模板
REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下:
{tools}

请严格按照以下格式进行回应:

Thought: 用一句话说明下一步行动依据，不展开推理过程。
Action: 你决定采取的行动，必须是以下格式之一:
- `{{tool_name}}[{{tool_input}}]`:调用一个可用工具。
- `Finish[最终答案]`:当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在Action:字段后使用 Finish[最终答案] 来输出最终答案。

Finish 内的最终答案遵循以下要求：
{response_style}

现在，请开始解决以下问题:
Question: {question}
History: {history}
"""

def search(query: str) -> str:
    """
    一个基于SerpApi的实战网页搜索引擎工具。
    它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。
    """
    debug(f"搜索：{query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "错误:SERPAPI_API_KEY 未在 .env 文件中配置。"

        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",  # 国家代码
            "hl": "zh-cn", # 语言代码
        }

        client = SerpApiClient(params)
        results = client.get_dict()

        # 智能解析:优先寻找最直接的答案
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)

        return f"对不起，没有找到关于 '{query}' 的信息。"

    except Exception as e:
        return f"搜索时发生错误: {e}"

class ToolExecutor:
    """
    一个工具执行器，用于调用各种工具函数。
    """
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, tool_name: str,description: str,tool_func: Any):
        """
        注册一个新的工具函数。
        """
        if tool_name in self.tools:
            raise ValueError(f"工具 '{tool_name}' 已经注册。")
        self.tools[tool_name] = {"description": description, "function": tool_func}

    def getTool(self, tool_name: str) -> Any:
        """
        获取已注册的工具函数。
        """
        if tool_name not in self.tools:
            raise ValueError(f"工具 '{tool_name}' 未注册。")
        return self.tools[tool_name]["function"]

    def getToolDescription(self) -> str:
        """
        返回所有已注册工具的描述。
        """
        return "\n".join([f"{name}: {info['description']}" for name, info in self.tools.items()])

class ReActAgent:
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor,max_steps: int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.history: List[Dict[str, str]] = []
        self.max_steps = max_steps

    def run(self, question: str):
        self.history = []
        current_step = 0

        while current_step < self.max_steps:
            # 构建提示词
            tools_description = self.tool_executor.getToolDescription()
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tools_description,
                question=question,
                history=self.history,
                response_style=RESPONSE_STYLE,
            )
            messages = [
                {"role": "system", "content": "你是一个有能力调用外部工具的智能助手。"},
                {"role": "user", "content": prompt}
            ]

            # 调用LLM进行思考
            response = self.llm_client.think(messages)
            if not response:
                return None

            # 解析LLM的输出
            action_match = re.search(r"(?ms)^\s*Action:\s*(.*)", response)
            if not action_match:
                error("模型未返回有效行动，暂时无法完成请求。")
                return None
            action_content = action_match.group(1).strip()
            finish = re.fullmatch(r"Finish\[(.*)\]", action_content, re.S)
            if finish:
                return finish.group(1).strip()

            # 解析工具调用
            if "[" in action_content and "]" in action_content:
                tool_name, tool_input = action_content.split("[", 1)
                tool_input = tool_input.rstrip("]")
                try:
                    tool_func = self.tool_executor.getTool(tool_name.strip())
                    tool_output = run_quietly(tool_func, tool_input.strip())
                except Exception as exc:
                    tool_output = f"工具调用失败：{exc}"
                debug(f"工具 {tool_name.strip()}：{tool_output}")

                # 更新历史记录
                self.history.append({"role": "assistant", "content": response})
                self.history.append({"role": "tool", "content": f"{tool_name.strip()}[{tool_input.strip()}] -> {tool_output}"})

            else:
                error("模型返回的行动格式无效，暂时无法完成请求。")
                return None

            current_step += 1

        error("达到最大执行步数，暂时无法完成请求。")
        return None


# --- 客户端使用示例 ---
def main():
    parser = argparse.ArgumentParser(description="ReAct 练习")
    parser.add_argument("--question", default="你好，请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。")
    add_output_argument(parser)
    args = parser.parse_args()
    set_verbose(args.verbose)
    # 初始化LLM客户端
    llm_client = HelloAgentsLLM()

    # 初始化工具执行器并注册工具
    tool_executor = ToolExecutor()
    tool_executor.register_tool("search", "基于SerpApi的网页搜索工具", search)

    # 创建ReAct智能体
    agent = ReActAgent(llm_client, tool_executor)

    # 用户问题示例
    user_question = args.question

    # 运行智能体
    answer = agent.run(user_question)
    if answer:
        print(answer)


if __name__ == '__main__':
    main()
