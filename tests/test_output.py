"""无外部服务的输出回归测试。运行：python -m unittest discover -s tests -v。"""

from contextlib import redirect_stderr, redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
import warnings
from unittest.mock import patch

from my_agent import llm_client
from my_agent.config import PROJECT_ROOT
from my_agent.output import debug, framework_output, quiet_stream, set_verbose


def load_example(relative):
    spec = spec_from_file_location(Path(relative).stem, PROJECT_ROOT / relative)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeLLM:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.messages = []

    def think(self, messages, **kwargs):
        self.messages.append(messages)
        return next(self.replies)


class OutputTests(unittest.TestCase):
    def setUp(self):
        self.cwd = Path.cwd()
        set_verbose(False)
        self.env = patch.dict(os.environ, {"AGENT_VERBOSE": "0"})
        self.env.start()

    def tearDown(self):
        set_verbose(None)
        self.env.stop()
        os.chdir(self.cwd)

    def test_normal_logs_hidden_and_warning_visible(self):
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            debug("模型和工具细节")
            with framework_output():
                print("✅ 工具已注册")
                print('{"raw_tool_result": "large result"}')
                print("⚠️ 连接降级，请检查配置")
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("连接降级", stderr.getvalue())

    def test_verbose_logs_available_and_secrets_redacted(self):
        set_verbose(True)
        stdout = StringIO()
        secret = "fake-private-value-123"
        with patch.dict(os.environ, {"TEST_API_KEY": secret}), redirect_stdout(stdout):
            debug("工具结果：", secret)
            with framework_output():
                print("工具已注册", secret)
        self.assertIn("工具已注册", stdout.getvalue())
        self.assertIn("<redacted>", stdout.getvalue())
        self.assertNotIn(secret, stdout.getvalue())

    def test_exception_propagates_and_stdout_is_restored(self):
        stdout = StringIO()
        with redirect_stdout(stdout):
            with self.assertRaisesRegex(RuntimeError, "service failed"):
                with framework_output():
                    print("routine setup")
                    raise RuntimeError("service failed")
            print("仍能显示最终答案")
        self.assertEqual(stdout.getvalue(), "仍能显示最终答案\n")

    def test_warning_keeps_message_without_stack_noise(self):
        stderr = StringIO()
        with redirect_stderr(stderr), framework_output():
            warnings.warn("服务将降级，请检查配置", UserWarning)
        self.assertIn("服务将降级", stderr.getvalue())
        self.assertEqual(len(stderr.getvalue().splitlines()), 1)
        self.assertNotIn("test_output.py", stderr.getvalue())

    def test_stream_chunks_print_once_even_in_verbose_mode(self):
        def vendor_stream():
            print("模型初始化")
            for chunk in ("你", "好"):
                print(chunk, end="", flush=True)
                yield chunk
            print("完成")

        for verbose in (False, True):
            set_verbose(verbose)
            stdout = StringIO()
            with redirect_stdout(stdout):
                for chunk in quiet_stream(vendor_stream()):
                    print(chunk, end="")
                print()
            self.assertEqual(stdout.getvalue(), "你好\n")

    def test_llm_returns_full_response_without_printing_it(self):
        answer = "完整代码或较长答案不能为了简洁而截断。" * 30
        chunks = [SimpleNamespace(choices=[])] + [
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=part))])
            for part in (answer[:100], answer[100:], None)
        ]
        create = SimpleNamespace(create=lambda **kwargs: iter(chunks))
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=create))
        with patch.object(llm_client, "OpenAI", return_value=fake_client):
            client = llm_client.HelloAgentsLLM(model="test", apiKey="fake-key", baseUrl="https://example.invalid")
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = client.think([{"role": "user", "content": "完整答案"}])
        self.assertEqual(result, answer)
        self.assertEqual(stdout.getvalue(), "")

    def test_llm_failure_is_visible_and_redacted(self):
        secret = "fake-private-value-123"

        def fail(**kwargs):
            raise RuntimeError("connection failed " + secret)

        fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fail)))
        with patch.object(llm_client, "OpenAI", return_value=fake):
            client = llm_client.HelloAgentsLLM(model="test", apiKey="fake-key", baseUrl="https://example.invalid")
        stdout, stderr = StringIO(), StringIO()
        with patch.dict(os.environ, {"TEST_API_KEY": secret}), redirect_stdout(stdout), redirect_stderr(stderr):
            result = client.think([])
        self.assertIsNone(result)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("模型调用失败", stderr.getvalue())
        self.assertNotIn(secret, stderr.getvalue())

    def test_react_displays_only_answer_and_keeps_full_tool_result(self):
        module = load_example("examples/ch04/react_agent.py")
        raw = "完整检索结果" * 300
        model = FakeLLM(["Thought: 查询\nAction: search[北京]", "Thought: 完成\nAction: Finish[今天北京晴，建议去公园。]"])
        tools = module.ToolExecutor()

        def search(query):
            print("工具内部日志")
            return raw

        tools.register_tool("search", "测试搜索", search)
        agent = module.ReActAgent(model, tools)
        stdout = StringIO()
        with redirect_stdout(stdout):
            print(agent.run("天气建议"))
        self.assertEqual(stdout.getvalue(), "今天北京晴，建议去公园。\n")
        self.assertIn(raw, model.messages[-1][1]["content"])

    def test_plan_entry_prints_final_answer_once(self):
        module = load_example("examples/ch04/plan_and_solve.py")
        model = FakeLLM(['```python\n["计算折扣", "计算最终价格"]\n```', "折后价格：200元", "最终价格是182元。"])
        stdout = StringIO()
        with patch.object(module, "HelloAgentsLLM", return_value=model), patch("sys.argv", ["plan_and_solve.py", "--question", "计算价格"]), redirect_stdout(stdout):
            module.main()
        self.assertEqual(stdout.getvalue(), "最终价格是182元。\n")
        self.assertIn("折后价格：200元", model.messages[-1][0]["content"])

    def test_chapter8_hides_setup_and_tool_logs(self):
        module = load_example("examples/ch08/memory_rag.py")

        def build():
            print("✅ 工具已注册")

            def run(question):
                print("数据库和工具的原始结果")
                return "记住了，张三。你是一名 Python 开发者。"

            return SimpleNamespace(run=run)

        stdout = StringIO()
        with patch.object(module, "build_agent", side_effect=build), patch("sys.argv", ["memory_rag.py"]), redirect_stdout(stdout):
            code = module.main()
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), "记住了，张三。你是一名 Python 开发者。\n")

    def test_chapter8_failed_rag_does_not_call_model(self):
        module = load_example("examples/ch08/memory_rag.py")
        stdout, stderr = StringIO(), StringIO()
        with patch.object(module, "HelloAgentsLLM"), patch.object(module, "ToolRegistry"), patch.object(module, "MemoryTool"), patch.object(module, "RAGTool", return_value=SimpleNamespace(initialized=False)), patch.object(module, "SimpleAgent") as agent, patch("sys.argv", ["memory_rag.py"]), redirect_stdout(stdout), redirect_stderr(stderr):
            code = module.main()
        self.assertEqual(code, 1)
        agent.assert_not_called()
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("知识检索服务初始化失败", stderr.getvalue())

    def test_notebook_stream_displays_text_once(self):
        from typing import Iterator, Optional
        from hello_agents import Config, Message, SimpleAgent, ToolRegistry
        from my_agent.output import with_style

        book = json.loads((PROJECT_ROOT / "notebooks/ch07/simple_agent.ipynb").read_text(encoding="utf-8"))
        source = next("".join(cell["source"]) for cell in book["cells"] if "class MySimpleAgent" in "".join(cell["source"]))
        namespace = {"SimpleAgent": SimpleAgent, "Config": Config, "Message": Message, "ToolRegistry": ToolRegistry, "Optional": Optional, "Iterator": Iterator, "HelloAgentsLLM": object, "debug": debug, "quiet_stream": quiet_stream, "with_style": with_style}
        exec(compile(source, "simple_agent.ipynb", "exec"), namespace)

        def stream(*args, **kwargs):
            for chunk in ("人工智能", "是让计算机完成智能任务的技术。"):
                print(chunk, end="")
                yield chunk

        agent = namespace["MySimpleAgent"]("test", SimpleNamespace(stream_invoke=stream))
        stdout = StringIO()
        with redirect_stdout(stdout):
            for chunk in agent.stream_run("人工智能是什么"):
                print(chunk, end="")
        self.assertEqual(stdout.getvalue(), "人工智能是让计算机完成智能任务的技术。")

    def test_reflection_returns_full_code_without_repeated_display(self):
        from typing import Any, Dict, List

        book = json.loads((PROJECT_ROOT / "notebooks/ch04/reflection.ipynb").read_text(encoding="utf-8"))
        namespace = {"Any": Any, "Dict": Dict, "List": List, "debug": debug, "INITIAL_PROMPT_TEMPLATE": "{task}", "REFLECT_PROMPT_TEMPLATE": "{task}\n{code}", "REFINE_PROMPT_TEMPLATE": "{task}\n{last_code_attempt}\n{feedback}"}
        for cell in book["cells"]:
            source = "".join(cell["source"])
            if "class Memory:" in source or "class RefectionAgent:" in source:
                exec(compile(source, "reflection.ipynb", "exec"), namespace)
        code = "def primes(n):\n    return [i for i in range(2, n + 1) if all(i % d for d in range(2, i))]"
        model = FakeLLM([code, "无需改进"])
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = namespace["RefectionAgent"](model).run("完整代码")
            print(result)
        self.assertEqual(result, code)
        self.assertEqual(stdout.getvalue(), code + "\n")

    def test_notebook_react_stops_at_step_limit(self):
        from typing import List, Optional
        import re
        from hello_agents import Config, HelloAgentsLLM, Message, ReActAgent, ToolRegistry
        from my_agent.output import with_style

        book = json.loads((PROJECT_ROOT / "notebooks/ch07/react_agent.ipynb").read_text(encoding="utf-8"))
        source = next("".join(cell["source"]) for cell in book["cells"] if "class MyReActAgent" in "".join(cell["source"]))
        namespace = {"re": re, "Config": Config, "Message": Message, "ReActAgent": ReActAgent, "ToolRegistry": ToolRegistry, "Optional": Optional, "List": List, "HelloAgentsLLM": HelloAgentsLLM, "debug": debug, "with_style": with_style, "MY_REACT_PROMPT": "{question}\n{tools}\n{history}"}
        exec(compile(source, "react_agent.ipynb", "exec"), namespace)
        model = SimpleNamespace(invoke=lambda *args, **kwargs: "Thought: 计算\nAction: calculator[2+3]")
        registry = SimpleNamespace(get_tools_description=lambda: "calculator", execute_tool=lambda *args: "5")
        agent = namespace["MyReActAgent"]("test", model, registry, max_steps=2)
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = agent.run("计算")
        self.assertIn("限定步数", result)
        self.assertEqual(len(agent.current_history), 4)
        self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
