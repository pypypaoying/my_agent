"""使 hello-agents 0.2.0 的 Qdrant 存储兼容新版客户端。
安装 requirements.txt 后运行一次本脚本；重装 hello-agents 后也需要重新运行。
"""
from importlib.util import find_spec
from pathlib import Path
import ast


def main():
    spec = find_spec('hello_agents')
    if spec is None or spec.origin is None:
        raise RuntimeError('请先安装 hello-agents')
    target = Path(spec.origin).parent / 'memory' / 'storage' / 'qdrant_store.py'
    source = target.read_text(encoding='utf-8')
    replacements = {
        'Filter, FieldCondition, MatchValue, SearchRequest': 'Filter, FieldCondition, MatchValue',
        'search_result = self.client.search(': 'search_result = self.client.query_points(',
        'query_vector=query_vector,': 'query=query_vector,',
        'for hit in search_result:': 'for hit in search_result.points:',
    }
    patched = source
    for old, new in replacements.items():
        patched = patched.replace(old, new)
    ast.parse(patched, filename=str(target))
    if 'self.client.search(' in patched or 'SearchRequest' in patched:
        raise RuntimeError('源码与已验证版本不同，请检查后再修改')
    if patched != source:
        backup = target.with_suffix('.py.ch8.bak')
        if not backup.exists():
            backup.write_bytes(target.read_bytes())
        target.write_text(patched, encoding='utf-8', newline='\n')
        print(f'已修复 Qdrant 查询 API: {target}')
    else:
        print('Qdrant 查询 API 已兼容，无需重复修改')
    from hello_agents.memory.storage.qdrant_store import QDRANT_AVAILABLE
    if not QDRANT_AVAILABLE:
        raise RuntimeError('Qdrant 仍无法导入，请检查 requirements.txt 的安装环境')
    print('Qdrant 导入验证通过')


if __name__ == '__main__':
    main()
