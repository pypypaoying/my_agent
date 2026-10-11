"""统一回答风格与控制台输出，不改变工具的执行结果。"""

from contextlib import contextmanager, redirect_stdout
from contextvars import ContextVar
from io import StringIO
import os
import re
import sys
import warnings


RESPONSE_STYLE = """最终回答的风格：
先直接回答用户的问题，用自然、简洁的中文。简单定义、确认或计算优先用一至两句话，约八十字。
回答足够就停止，不主动补充用户没有问到的背景、组成、原理、延伸建议或总结。
省略思考过程、工具名称、调用参数、原始结果、初始化日志和重复的完成提示。
只有影响结论或用户下一步行动的信息才需要解释。产物只交代必要内容和使用方式。
用户要求详细说明、完整代码或逐步计算时，保留这些必要内容，不为缩短而删去答案。
执行失败或结果未验证时如实说明，不能声称已经保存、记住、检索或完成。
避免客套开场、反复总结、装饰性标题和表情符号。"""

_verbose = ContextVar("agent_verbose", default=None)
_diagnostic = re.compile(r"^(?:❌|⚠|ERROR\b|WARNING\b|Error:|Warning:|错误[:：]|警告[:：])", re.I)


def is_verbose():
    value = _verbose.get()
    if value is not None:
        return value
    return os.getenv("AGENT_VERBOSE", "0").lower() in {"1", "true", "yes", "on"}


def set_verbose(value=None):
    """None 表示使用环境变量；Notebook 可以显式传入 True。"""
    _verbose.set(value)


def add_output_argument(parser):
    parser.add_argument("--verbose", action="store_true", default=None, help="显示模型和工具的详细运行过程")


def with_style(task_prompt):
    return task_prompt.rstrip() + "\n\n" + RESPONSE_STYLE


def redact(value):
    text = str(value)
    for key, secret in os.environ.items():
        if any(marker in key.upper() for marker in ("KEY", "TOKEN", "PASSWORD", "SECRET")) and len(secret) >= 8:
            text = text.replace(secret, "<redacted>")
    return re.sub(r"\b(?:sk-|tvly-|ghp_|github_pat_)[A-Za-z0-9_-]{12,}\b", "<redacted>", text)


def debug(*values, **kwargs):
    if is_verbose():
        print(*(redact(value) for value in values), **kwargs)


def error(message):
    """失败始终可见，凭证始终脱敏。"""
    print(redact(message), file=sys.stderr)


@contextmanager
def framework_output(verbose=None):
    """控制第三方框架的 stdout；stderr 和异常仍正常传播。

    仅用于本项目的单线程控制台示例。最终答案由调用者在上下文外显示。
    """
    enabled = is_verbose() if verbose is None else verbose
    captured = StringIO()
    try:
        with warnings.catch_warnings():
            if not enabled:
                def show_warning(message, category, filename, lineno, file=None, line=None):
                    print(redact(f"警告（{category.__name__}）：{message}"), file=file or sys.stderr)
                warnings.showwarning = show_warning
            with redirect_stdout(captured):
                yield
    finally:
        if enabled:
            print(redact(captured.getvalue()), end="")
        else:
            for line in captured.getvalue().splitlines():
                if _diagnostic.match(line.strip()):
                    error(line.strip())


def run_quietly(function, *args, **kwargs):
    with framework_output():
        return function(*args, **kwargs)


def quiet_stream(chunks):
    """只屏蔽框架在 next() 内的重复打印，yield 后恢复调用者的 stdout。"""
    iterator = iter(chunks)
    while True:
        with framework_output(verbose=False):
            try:
                chunk = next(iterator)
            except StopIteration:
                return
        yield chunk
