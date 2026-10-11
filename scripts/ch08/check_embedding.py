"""修正第八章示例的百炼 URL，并独立验证嵌入接口。"""
import argparse
import os
from dotenv import dotenv_values
from my_agent.config import PROJECT_ROOT, load_project_env
from my_agent.embedding import configure_embedding

parser = argparse.ArgumentParser()
parser.add_argument('--fix-config', action='store_true')
args = parser.parse_args()
env_path = PROJECT_ROOT / '.env'
old_url = 'https://dashscope.aliyuncs.com/api/v1'
new_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
if args.fix_config:
    values = dotenv_values(env_path)
    if (values.get('EMBED_BASE_URL') or '').rstrip('/') == old_url:
        with env_path.open('r', encoding='utf-8', newline='') as handle:
            content = handle.read()
        lines = content.splitlines(keepends=True)
        for i, line in enumerate(lines):
            if line.lstrip().startswith('EMBED_BASE_URL='):
                ending = '\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
                lines[i] = 'EMBED_BASE_URL=' + new_url + ending
                break
        else:
            raise RuntimeError('未找到 EMBED_BASE_URL 配置行')
        with env_path.open('w', encoding='utf-8', newline='') as handle:
            handle.write(''.join(lines))
        print('已修正 EMBED_BASE_URL，其他配置保持原值', flush=True)
load_project_env()
backend = os.getenv('EMBED_MODEL_TYPE', 'dashscope')
if backend != 'dashscope':
    raise RuntimeError('此检查针对当前配置的 dashscope 嵌入服务')
model = os.getenv('EMBED_MODEL_NAME') or 'text-embedding-v3'
url = os.getenv('EMBED_BASE_URL')
print(f'配置文件: {env_path}', flush=True)
print(f'模型: {model}; Base URL: {url}', flush=True)
try:
    embedder = configure_embedding()
    print(f'嵌入接口正常，向量维度: {embedder.dimension}', flush=True)
except Exception as exc:
    message = str(exc)
    for name, value in os.environ.items():
        if any(marker in name.upper() for marker in ('KEY', 'TOKEN', 'PASSWORD')) and len(value) > 8:
            message = message.replace(value, '<redacted>')
    print(f'{type(exc).__name__}: {message}', flush=True)
    raise SystemExit(1)
