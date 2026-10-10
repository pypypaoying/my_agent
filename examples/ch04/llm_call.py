"""早期 D1 练习：单次模型调用（尚未实现工具调用循环）。"""

import os

from openai import OpenAI

from my_agent.config import load_project_env


def main():
    load_project_env()
    client = OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ["LLM_BASE_URL"])

    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL_ID"],
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "你好，我有点伤心，你可以安慰我吗？"},
        ],
        stream=False,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )



    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
