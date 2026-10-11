"""验证框架补丁与真实 Qdrant 客户端兼容，使用隔离的内存数据库。"""

from importlib.util import find_spec, module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from qdrant_client import QdrantClient, models

from my_agent.config import PROJECT_ROOT


class QdrantCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = spec_from_file_location("repair_environment", PROJECT_ROOT / "scripts/ch08/repair_environment.py")
        repair = module_from_spec(spec)
        spec.loader.exec_module(repair)
        origin = find_spec("hello_agents").origin
        source = (Path(origin).parent / "memory/storage/qdrant_store.py").read_text(encoding="utf-8")
        patched = repair.patch_source(source)
        if repair.patch_source(patched) != patched:
            raise AssertionError("Repeated repair changed the source")
        namespace = {"__name__": "qdrant_compat_test"}
        exec(compile(patched, "qdrant_store_patched.py", "exec"), namespace)
        cls.store_type = namespace["QdrantVectorStore"]

    def make_store(self, client):
        # 跳过会初始化真实远端集合的构造函数。
        store = self.store_type.__new__(self.store_type)
        store.client = client
        store.collection_name = "compat_test"
        store.vector_size = 2
        store.distance = models.Distance.COSINE
        store.search_ef = 128
        store.search_exact = True
        return store

    def test_new_collection_info_and_search_with_real_client(self):
        client = QdrantClient(location=":memory:")
        self.addCleanup(client.close)
        client.create_collection("compat_test", vectors_config=models.VectorParams(size=2, distance=models.Distance.COSINE))
        client.upsert("compat_test", points=[
            models.PointStruct(id=1, vector=[1.0, 0.0], payload={"tag": "match"}),
            models.PointStruct(id=2, vector=[0.0, 1.0], payload={"tag": "other"}),
        ])
        store = self.make_store(client)
        self.addCleanup(setattr, store, "client", None)
        info = store.get_collection_info()
        self.assertEqual(info["points_count"], 2)
        self.assertIsNone(info["vectors_count"])
        self.assertEqual(info["config"]["vector_size"], 2)
        self.assertEqual(store.get_collection_stats()["store_type"], "qdrant")
        hits = store.search_similar([1.0, 0.0], limit=1, where={"tag": "match"})
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["id"], 1)
        self.assertEqual(hits[0]["metadata"]["tag"], "match")

    def test_legacy_count_and_unknown_points_are_preserved(self):
        client = Mock()
        client.get_collection.return_value = SimpleNamespace(
            vectors_count=7, indexed_vectors_count=5, points_count=None, segments_count=1,
        )
        info = self.make_store(client).get_collection_info()
        self.assertEqual(info["vectors_count"], 7)
        self.assertEqual(info["indexed_vectors_count"], 5)
        self.assertIsNone(info["points_count"])

    def test_connection_failure_still_reports_an_error(self):
        client = Mock()
        client.get_collection.side_effect = RuntimeError("server unavailable")
        with self.assertLogs("qdrant_compat_test", level="ERROR") as logs:
            self.assertEqual(self.make_store(client).get_collection_info(), {})
        self.assertIn("server unavailable", logs.output[0])


if __name__ == "__main__":
    unittest.main()
