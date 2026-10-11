"""嵌入配置回归测试，不调用模型接口或数据库。"""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from requests.utils import get_environ_proxies

from my_agent import embedding as project_embedding
from my_agent.output import framework_output

with framework_output():
    from hello_agents.memory import embedding as provider
    from hello_agents.memory.embedding import get_text_embedder as imported_provider


class EmbeddingTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "EMBED_MODEL_TYPE": "dashscope",
            "EMBED_MODEL_NAME": "text-embedding-v3",
            "EMBED_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "EMBED_API_KEY": "fake-private-key-123",
            "QDRANT_VECTOR_SIZE": "1024",
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_aliyun_bypasses_proxy_and_huggingface_keeps_proxy(self):
        os.environ.update(HTTPS_PROXY="http://127.0.0.1:7897", NO_PROXY="localhost,127.0.0.1")
        self.assertEqual(project_embedding.configure_embedding_proxy(), "direct")
        self.assertIn("localhost", os.environ["NO_PROXY"])
        self.assertIn("dashscope.aliyuncs.com", os.environ["NO_PROXY"])
        self.assertEqual(get_environ_proxies("https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"), {})
        self.assertEqual(get_environ_proxies("https://huggingface.co/models")["https"], "http://127.0.0.1:7897")
        before = os.environ["NO_PROXY"]
        project_embedding.configure_embedding_proxy()
        self.assertEqual(os.environ["NO_PROXY"], before)

    def test_system_mode_preserves_existing_proxy_settings(self):
        os.environ.update(EMBED_PROXY_MODE="system", NO_PROXY="localhost", HTTPS_PROXY="http://127.0.0.1:7897")
        self.assertEqual(project_embedding.configure_embedding_proxy(), "system")
        self.assertEqual(os.environ["NO_PROXY"], "localhost")
        self.assertEqual(os.environ["HTTPS_PROXY"], "http://127.0.0.1:7897")

    def test_windows_system_proxy_survives_no_proxy_environment_variable(self):
        proxies = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
        with patch.object(project_embedding, "getproxies", return_value=proxies):
            project_embedding.configure_embedding_proxy()
        self.assertEqual(get_environ_proxies("https://huggingface.co/models")["https"], proxies["https"])
        self.assertEqual(get_environ_proxies("https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"), {})

    def test_invalid_proxy_mode_is_reported(self):
        os.environ["EMBED_PROXY_MODE"] = "typo"
        with self.assertRaisesRegex(ValueError, "EMBED_PROXY_MODE"):
            project_embedding.configure_embedding_proxy()

    def test_cloud_failure_is_redacted_and_never_calls_local_factory(self):
        with patch.object(provider, "create_embedding_model", side_effect=RuntimeError("HTTP 401 fake-private-key-123")) as factory:
            with self.assertRaisesRegex(RuntimeError, "HTTP 401 <redacted>"):
                project_embedding._strict_factory("dashscope", model_name="text-embedding-v3", api_key=os.environ["EMBED_API_KEY"])
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(factory.call_args.args[0], "dashscope")

    def test_cloud_model_cannot_be_sent_to_huggingface(self):
        with patch.object(provider, "create_embedding_model") as factory:
            with self.assertRaisesRegex(ValueError, "阿里云模型"):
                project_embedding._strict_factory("local", model_name="text-embedding-v3")
        factory.assert_not_called()

    def test_dimension_mismatch_stops_before_database_use(self):
        with patch.object(provider, "create_embedding_model", return_value=SimpleNamespace(dimension=384)):
            with self.assertRaisesRegex(RuntimeError, "QDRANT_VECTOR_SIZE=1024"):
                project_embedding._strict_factory("dashscope", api_key="fake-key")

    def test_configured_instance_is_shared_and_refresh_remains_strict(self):
        embedder = SimpleNamespace(dimension=1024)
        with patch.object(project_embedding, "load_project_env"), patch.object(provider, "_embedder", None), patch.object(provider, "create_embedding_model_with_fallback", provider.create_embedding_model_with_fallback), patch.object(provider, "create_embedding_model", return_value=embedder) as factory:
            self.assertIs(project_embedding.configure_embedding(), embedder)
            self.assertIs(imported_provider(), embedder)
            self.assertEqual(factory.call_args.args[0], "dashscope")
            factory.side_effect = RuntimeError("connection timed out")
            with self.assertRaisesRegex(RuntimeError, "connection timed out"):
                provider.refresh_embedder()
            self.assertEqual(factory.call_count, 2)

    def test_chapter8_embedding_failure_stops_before_tools_and_llm(self):
        from test_output import load_example
        module = load_example("examples/ch08/memory_rag.py")
        stdout, stderr = StringIO(), StringIO()
        with patch.object(module, "configure_embedding", side_effect=RuntimeError("HTTP 401")), patch.object(module, "HelloAgentsLLM") as llm, patch.object(module, "MemoryTool") as memory, patch("sys.argv", ["memory_rag.py"]), redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(module.main(), 1)
        llm.assert_not_called()
        memory.assert_not_called()
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("HTTP 401", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
