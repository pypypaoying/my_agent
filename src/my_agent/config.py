"""统一定位项目配置，避免脚本和 Notebook 依赖本机绝对路径。"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


def load_project_env() -> Path:
    """加载项目根目录 .env，保留调用者已设置的环境变量。"""
    env_path = PROJECT_ROOT / ".env"
    load_dotenv(env_path, override=False)
    # 兼容早期笔记使用的变量名，统一提供 LLM_MODEL_ID / LLM_API_KEY。
    if not os.getenv("LLM_MODEL_ID") and os.getenv("LLM_MODEL"):
        os.environ["LLM_MODEL_ID"] = os.environ["LLM_MODEL"]
    if not os.getenv("LLM_API_KEY") and os.getenv("DEEPSEEK_API_KEY"):
        os.environ["LLM_API_KEY"] = os.environ["DEEPSEEK_API_KEY"]
    return env_path
