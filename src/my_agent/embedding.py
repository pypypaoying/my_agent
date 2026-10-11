"""第八章嵌入入口：按配置直连，失败时保留原因，不更换模型。"""

import os
from urllib.parse import urlsplit
from urllib.request import getproxies

from my_agent.config import load_project_env
from my_agent.output import redact


def configure_embedding_proxy():
    """只为选中的嵌入域名设置 NO_PROXY，其他服务沿用原代理。"""
    backend = os.getenv("EMBED_MODEL_TYPE", "dashscope").strip().lower()
    url = os.getenv("EMBED_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    host = urlsplit(url).hostname
    aliyun = host and (host == "aliyuncs.com" or host.endswith(".aliyuncs.com"))
    default_mode = "direct" if backend == "dashscope" and aliyun else "system"
    mode = os.getenv("EMBED_PROXY_MODE", default_mode).strip().lower()
    if mode not in {"direct", "system"}:
        raise ValueError("EMBED_PROXY_MODE 只能是 direct（直连）或 system（沿用代理）。")
    if mode == "direct":
        if not host:
            raise ValueError("直连模式需要有效的 EMBED_BASE_URL。")
        # Windows 的 getproxies() 会在发现 NO_PROXY 后停止读取系统代理。
        # 先将当前有效的代理保留到进程环境，防止 Hugging Face 意外变成直连。
        proxies = getproxies()
        for scheme in ("http", "https", "all"):
            variable = f"{scheme.upper()}_PROXY"
            if proxies.get(scheme) and variable not in os.environ and variable.lower() not in os.environ:
                os.environ[variable] = proxies[scheme]
        entries = []
        for value in (os.getenv("NO_PROXY", ""), os.getenv("no_proxy", ""), host):
            for item in value.split(","):
                item = item.strip()
                if item and item not in entries:
                    entries.append(item)
        # 同时兼容 Windows 与 Linux 上读取不同大小写变量的客户端。
        os.environ["NO_PROXY"] = os.environ["no_proxy"] = ",".join(entries)
    return mode


def _strict_factory(preferred_type="dashscope", **kwargs):
    from hello_agents.memory.embedding import create_embedding_model

    backend = preferred_type.strip().lower()
    if backend in {"sentence_transformer", "huggingface"}:
        backend = "local"
    if backend == "local":
        model_name = kwargs.get("model_name", "sentence-transformers/all-MiniLM-L6-v2")
        if model_name.startswith("text-embedding-"):
            raise ValueError("text-embedding 系列是阿里云模型，请设置 EMBED_MODEL_TYPE=dashscope。")
        kwargs = {"model_name": model_name}
    elif backend == "tfidf":
        kwargs = {key: value for key, value in kwargs.items() if key == "max_features"}
    elif backend == "dashscope":
        if not kwargs.get("api_key"):
            raise ValueError("请在 .env 中填写 EMBED_API_KEY。")
        kwargs.setdefault("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    else:
        raise ValueError(f"不支持的 EMBED_MODEL_TYPE：{backend}")

    try:
        embedder = create_embedding_model(backend, **kwargs)
        expected = os.getenv("QDRANT_VECTOR_SIZE")
        if expected and int(expected) != embedder.dimension:
            raise ValueError(
                f"嵌入维度为 {embedder.dimension}，QDRANT_VECTOR_SIZE={expected}；"
                "请确认模型与已有集合的维度一致。"
            )
        return embedder
    except Exception as exc:
        raise RuntimeError(f"{backend} 嵌入初始化失败：{redact(exc)}") from None


def configure_embedding():
    """初始化框架共享实例；应在创建 MemoryTool / RAGTool 之前调用。"""
    load_project_env()
    configure_embedding_proxy()
    from hello_agents.memory import embedding

    # hello-agents 0.2.0 没有注册 provider 的接口。替换其公开工厂后，
    # refresh_embedder 重建所有记忆类型共用的实例，也让后续刷新保持严格选择。
    embedding.create_embedding_model_with_fallback = _strict_factory
    return embedding.refresh_embedder()
