import argparse
import ast
from my_agent.llm_client import HelloAgentsLLM
from my_agent.config import load_project_env
from my_agent.output import RESPONSE_STYLE, add_output_argument, debug, error, set_verbose

# 加载 .env 文件中的环境变量，处理文件不存在异常

load_project_env()


PLANNER_PROMPT_TEMPLATE = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划,```python与```作为前后缀是必要的:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""
EXECUTOR_PROMPT_TEMPLATE = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决“当前步骤”，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对“当前步骤”的回答:
如果当前步骤是最后一步，请结合已有结果直接回答原始问题，不复述计划和执行过程。
当前步骤是否为最后一步: {is_final}
{response_style}
"""


class Planner:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def plan(self, question: str) -> list[str]:
        """
        根据用户问题生成一个行动计划。
        """
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)

        # 为了生成计划，我们构建一个简单的消息列表
        messages = [{"role": "user", "content": prompt}]

        debug("正在生成计划")
        # 使用流式输出来获取完整的计划
        response_text = self.llm_client.think(messages=messages) or ""

        debug(f"计划：\n{response_text}")
        if not response_text:
            return []

        # 解析LLM输出的列表字符串
        try:
            # 找到```python和```之间的内容
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            # 使用ast.literal_eval来安全地执行字符串，将其转换为Python列表
            plan = ast.literal_eval(plan_str)
            if not isinstance(plan, list) or not plan or not all(isinstance(step, str) and step.strip() for step in plan):
                raise ValueError("计划必须是非空的步骤列表")
            return plan
        except (ValueError, SyntaxError, IndexError) as e:
            error(f"无法解析计划：{e}")
            debug(f"原始响应：{response_text}")
            return []
        except Exception as e:
            error(f"生成计划失败：{e}")
            return []

class Executor:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def execute(self, question: str, plan: list[str]) -> str:
        """
        根据计划，逐步执行并解决问题。
        """
        history = "" # 用于存储历史步骤和结果的字符串

        debug("正在执行计划")
        response_text = ""

        for i, step in enumerate(plan):
            debug(f"步骤 {i+1}/{len(plan)}：{step}")

            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question,
                plan=plan,
                history=history if history else "无", # 如果是第一步，则历史为空
                current_step=step,
                is_final="是" if i == len(plan) - 1 else "否",
                response_style=RESPONSE_STYLE,
            )

            messages = [{"role": "user", "content": prompt}]

            response_text = self.llm_client.think(messages=messages) or ""
            if not response_text:
                return None

            # 更新历史记录，为下一步做准备
            history += f"步骤 {i+1}: {step}\n结果: {response_text}\n\n"

            debug(f"步骤结果：{response_text}")

        # 循环结束后，最后一步的响应就是最终答案
        final_answer = response_text
        return final_answer

class PlanAndSolveAgent:
    def __init__(self, llm_client):
        self.planner = Planner(llm_client)
        self.executor = Executor(llm_client)

    def solve(self, question: str) -> str:
        """
        解决用户提出的问题。
        """
        # 第一步：生成计划
        plan = self.planner.plan(question)

        if not plan:
            return None

        debug(f"计划：{plan}")

        # 第二步：执行计划
        final_answer = self.executor.execute(question, plan)

        return final_answer


def main():
    parser = argparse.ArgumentParser(description="Plan-and-Solve 练习")
    parser.add_argument("--question", help="直接传入问题；省略时交互输入")
    add_output_argument(parser)
    args = parser.parse_args()
    set_verbose(args.verbose)
    # 初始化LLM客户端
    llm_client = HelloAgentsLLM()

    # 创建PlanAndSolveAgent实例
    agent = PlanAndSolveAgent(llm_client)

    # 用户输入问题
    question = args.question or input("问题：")

    # 调用solve方法解决问题
    final_answer = agent.solve(question)

    if final_answer:
        print(final_answer)


if __name__ == "__main__":
    main()
