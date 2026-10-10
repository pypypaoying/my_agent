# Python 惯用法速补 ｜ 读懂 `d1_llm_client.py` 需要的全部语法

> 你说「代码完全看不懂」——**不是 AI 难，是 Python 工程惯用法你没接触过**。
> 这份文档把 `d1_llm_client.py` 里用到的每一个语法点，都拆成一个 3 行最小例子。
> 每个例子都可以直接复制到 `.py` 里跑。跑一遍比读十遍有用。

## 怎么用这份文档

- **不要从头读到尾**。卡在哪个语法点，就 `Ctrl+F` 搜它。
- 每个条目都有【在 d1 里的位置】，可以对着原文件看真实用法。
- 【自测】那一句要**真的在心里回答**，不然等于没读。
- 全部 21 条过完约 90 分钟。建议 D1 之前先扫一遍第一梯队（1–8 条，约 40 分钟）。

## 三个梯队

| 梯队 | 条目 | 什么时候必须掌握 |
|---|---|---|
| 🔴 第一梯队 | 1–8 | **现在**。不掌握就读不懂 D1 的任何一行 |
| 🟠 第二梯队 | 9–21 | D1 会用到，D2 起天天用 |
| ⚪ 第三梯队（预告） | 22–28 | D4–D7 才出现，现在扫一眼混个脸熟即可 |

---

# 🔴 第一梯队（1–8）

## 1. f-string 与四种格式化后缀

**是什么**：`f"..."` 里的 `{}` 可以塞任何表达式。冒号后面是格式说明。

```python
name, tokens, ttft = "深圳", 42, 1.23456
print(f"{name} 消耗 {tokens} token")        # 深圳 消耗 42 token
print(f"{tokens:>5}")                        # '   42'   右对齐，占 5 格
print(f"{name:<38} = {tokens!r}")            # 左对齐占 38 格；!r 用 repr 显示
print(f"{ttft:.2f}s")                        # 1.23s   保留两位小数
```

**`!r` 为什么重要**：它调用 `repr()` 而不是 `str()`，能看出**类型差异**：

```python
s = "1"
print(f"{s}")     # 1      ← 看不出是字符串还是数字
print(f"{s!r}")   # '1'    ← 有引号，一眼看出是字符串
print(f"{None!r}")  # None
print(f"{''!r}")    # ''     ← 空字符串，不是 None！
```

**在 d1 里的位置**：`step1_raw` 的字段表用 `{name:<38} = {value!r}` 对齐；`step3_buggy` 打印 `参数原文 {tc.function.arguments!r}`。

**不这么写会怎样**：BUG 1 你就看不出来。`arguments` 打印成 `{"city": "深圳"}` 你以为它是 dict，加了 `!r` 显示成 `'{"city": "深圳"}'`——**外面那层引号说明它是字符串**。这一个引号就是 BUG 1 的全部线索。

**自测**：`print(f"{0!r}")` 和 `print(f"{''!r}")` 分别输出什么？怎么区分 `None`、`0`、空字符串？

---

## 2. dict：字面量、嵌套、`in`、`.get()` vs `[]`

**是什么**：字典是键值对。工具 schema 就是一个三层嵌套的 dict。

```python
d = {"city": "深圳", "unit": "celsius"}
print(d["city"])              # 深圳
print(d.get("city"))          # 深圳
print(d.get("temp"))          # None      ← 键不存在，返回 None，不报错
print(d.get("temp", "未知"))   # 未知      ← 可以指定默认值
print(d["temp"])              # 💥 KeyError: 'temp'   ← 键不存在直接崩
print("city" in d)            # True      ← 判断键是否存在
```

**🔑 `[]` vs `.get()` 的选择，是一个工程决策，不是风格问题**：

| 用哪个 | 什么时候 |
|---|---|
| `d[k]` | 这个键**必须**存在，不存在就是程序 bug，应该立刻崩掉让你发现 |
| `d.get(k)` | 这个键**可能**不存在，且不存在是正常情况，你要自己处理 |
| `d.get(k) or 默认` | 键可能不存在，**或者存在但是 None/空** |

**在 d1 里的位置**：
- `WEATHER_DB[city]` 用 `[]` —— 故意的，查不到的城市就该抛 `KeyError`，这是 BUG 3 的测试夹具
- `os.environ.get("LLM_API_KEY", "")` 用 `.get()` —— 没配 key 是正常情况，要给出友好提示而不是崩
- `out.get("content")` 在判分器里 —— 用户可能根本没返回这个键，不能崩

**不这么写会怎样**：判分器里如果写 `out["content"]`，用户返回的 dict 少一个键，判分器自己先崩了，你就看不到「哪一项 FAIL」。

**自测**：`_WEATHER_DB[city]` 为什么故意用 `[]` 而不用 `.get()`？（提示：它是测试夹具）

---

## 3. `**` 摊开：把 dict 变成函数参数

**是什么**：`**` 在**调用处**把字典摊开成关键字参数；在**函数定义处**收集多余的关键字参数。

```python
def get_weather(city, unit="celsius"):
    return f"{city}/{unit}"

args = {"city": "深圳", "unit": "celsius"}
print(get_weather(**args))         # 深圳/celsius   ← 等价于 get_weather(city="深圳", unit="celsius")

def f(**kwargs):                    # 定义处：收集成一个 dict
    print(kwargs)
f(a=1, b=2)                         # {'a': 1, 'b': 2}
```

**`dict(...)` 构造 + `**` 摊开，是「按需组装参数」的标准写法**：

```python
kwargs = dict(model="deepseek-chat", messages=[...])
if tools:
    kwargs["tools"] = tools          # 有条件地加参数
r = client.chat.completions.create(**kwargs)
```

**在 d1 里的位置**：
- `step3_buggy` 的 `get_weather(**args)` ← **这就是 BUG 1 崩的地方**
- `ref_chat` 的 `kwargs = dict(...)` + `create(**kwargs)`

**不这么写会怎样**：BUG 1 的报错原文是
```
TypeError: get_weather() argument after ** must be a mapping, not str
```
「must be a mapping, not str」= 「`**` 后面必须是字典，你给的是字符串」。看懂这句报错，BUG 1 就修好了。

**如果不按需组装，你就得写**：
```python
# 丑陋且容易漏参数的写法
if tools and response_format:
    r = create(model=M, messages=msgs, tools=tools, response_format=response_format, ...)
elif tools:
    r = create(model=M, messages=msgs, tools=tools, ...)
elif response_format:
    ...   # 4 个可选参数 = 16 种组合，写不完
```

**自测**：`f(**{"a": 1})` 和 `f({"a": 1})` 有什么区别？

---

## 4. `x or 默认值`：Python 最常用的兜底惯用法

**是什么**：`or` 返回**第一个「真值」**。Python 里 `None`、`""`、`0`、`[]`、`{}` 都是「假值」。

```python
print(None or "默认")      # 默认
print("" or "默认")        # 默认
print("实际值" or "默认")   # 实际值
print([] or ["空"])        # ['空']
print(0 or 99)             # 99    ← ⚠️ 0 也是假值！
```

**在 d1 里的位置**（这个惯用法在文件里出现了 6 次，必须形成肌肉记忆）：

```python
for tc in tcs or []:                       # tcs 是 None 时当空列表，避免 "for None" 崩
raw = tc.function.arguments or ""          # arguments 是 None 时当空字符串
json.loads(tc.function.arguments or "{}")  # 空参数当空字典
u.prompt_tokens or 0                       # usage 字段是 None 时补 0
os.environ.get("LLM_BASE_URL") or None     # 空字符串也当 None
out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)
```

**为什么必须这么写**：OpenAI 兼容 API 的很多字段**可能是 None**。`msg.tool_calls` 在模型不调工具时是 `None`，不是 `[]`。直接 `for tc in msg.tool_calls:` 会抛 `TypeError: 'NoneType' object is not iterable`。

**⚠️ 唯一的陷阱**：`0` 也是假值。

```python
count = 0
print(count or 10)    # 10  ← 你本意是「count 没赋值时用 10」，但 0 被吃掉了
```
如果 0 是合法值，必须写成 `count if count is not None else 10`。

**不这么写会怎样**：`ref_usage(None)` 里如果不写 `if u else {...}`，流式模式下会抛 `AttributeError: 'NoneType' object has no attribute 'prompt_tokens'`。

**自测**：`tc.function.arguments or "{}"` —— 如果模型返回的 arguments 是空字符串 `""`，`json.loads` 收到的是什么？如果不加这个 `or "{}"` 会怎样？

---

## 5. 列表推导式

**是什么**：一行写完「遍历 + 变换 + 可选过滤」，生成一个新列表。

```python
nums = [1, 2, 3, 4]
print([n * 10 for n in nums])               # [10, 20, 30, 40]
print([n for n in nums if n % 2 == 0])       # [2, 4]        过滤
print([n if n > 2 else 0 for n in nums])     # [0, 0, 3, 4]   变换（三元在 for 前）
```

**读法**：从**中间**的 `for` 开始读，再看后面的 `if`，最后看前面的表达式。

**在 d1 里的位置**：`ref_assistant_message` 和 `step3_fixed` 里把 SDK 对象转成 dict 列表：

```python
"tool_calls": [
    {"id": t.id, "type": "function",
     "function": {"name": t.function.name, "arguments": t.function.arguments}}
    for t in msg.tool_calls
]
```

等价的传统写法（4 行变 1 个表达式）：
```python
result = []
for t in msg.tool_calls:
    result.append({"id": t.id, "type": "function",
                   "function": {"name": t.function.name, "arguments": t.function.arguments}})
```

**为什么要转成 dict**：SDK 返回的是 `ChatCompletionMessageToolCall` 对象，**不能直接 `json.dumps`**。而 D10 要把每条调用落成 JSONL Trace 文件，所以必须转成纯 dict。这也是「换厂商时上层代码不用改」的前提。

**自测**：`[{"k": v} for v in [1,2]]` 输出什么？

---

## 6. `try / except as e / raise` 与指数退避

**是什么**：异常处理。这是 Agent 工程的**核心技能**，因为 LLM 和工具随时会失败。

```python
try:
    n = int("abc")
except ValueError as e:            # 只接特定类型，as e 拿到异常对象
    print(f"出错：{type(e).__name__}: {e}")     # 出错：ValueError: invalid literal...
else:
    print("没出错才走这里")
finally:
    print("不管出没出错都走这里")
```

**三个关键写法**：

```python
type(e).__name__     # 'ValueError'  ← 异常类名，比 str(e) 更适合做分类统计
raise                # 裸 raise：把当前异常【原样】抛出去，保留完整堆栈
raise ValueError("新错误") from e   # 抛新的但保留原因链
```

**指数退避重试（生产级必备）**：

```python
for i in range(3):
    try:
        return do_something()
    except Exception:
        if i == 2:        # 最后一次仍失败
            raise         # 原样抛出，不吞异常
        time.sleep(2 ** i)   # 1s → 2s → 4s
```

`2 ** i` 是幂运算：`2**0=1`、`2**1=2`、`2**2=4`。

**为什么退避而不是立刻重试**：限流（429）和网络抖动都需要时间恢复。立刻重试三次会在 100ms 内全部失败，等于没重试；退避给服务端喘息时间，成功率显著提高。

**在 d1 里的位置**：`ref_chat` 的重试循环、`step3_fixed` 的三处 try、`step4_verify` 的 `except Exception as e`。

**⚠️ 一个反面教材（面试常考的坏味道）**：

```python
try:
    ...
except Exception:
    pass          # ⛔ 吞掉所有异常。出了 bug 你永远不知道，这是最坏的写法
```

**在 Agent 里的正确姿势**：工具抛异常时**不要**让程序崩，也**不要**静默吞掉，而是**把错误变成一条观测结果回灌给模型**：

```python
except Exception as e:
    observation = f"调用失败：{type(e).__name__}: {e}。请修正参数后重试。"
```

这样模型有机会自己纠正。这是 BUG 3 的标准修法，也是八股「工具报错你怎么处理」的答案。

**自测**：为什么 `if i == max_retries - 1: raise` 里的 `raise` 不写成 `raise e`？（提示：堆栈信息）

---

## 7. `json.loads` vs `json.dumps`，以及 `ensure_ascii=False`

**是什么**：JSON 是**文本格式**，dict 是**Python 对象**。两者要互相转换。

```python
import json
d = {"city": "深圳", "temp": 29}

s = json.dumps(d)                       # dict → 字符串
print(s)                                # {"city": "\u6df1\u5733", "temp": 29}   ← 中文被转义了！
print(json.dumps(d, ensure_ascii=False)) # {"city": "深圳", "temp": 29}          ← 这才是你要的

back = json.loads(s)                     # 字符串 → dict
print(back["city"], type(back["city"]))  # 深圳 <class 'str'>
```

**记忆法**：`loads` = **load string**（读进来），`dumps` = **dump string**（吐出去）。

**`ensure_ascii=False` 为什么必须加**：默认 True 时，所有非 ASCII 字符被转义成 `\uXXXX`。后果有两个：
1. **token 白翻好几倍**（`\u6df1\u5733` 是 12 个字符，`深圳` 是 2 个）
2. **Trace 文件完全没法读**（打开全是 `\u` 转义）

**`json.loads` 会抛 `JSONDecodeError`**，这是 function calling 的头号敌人：

```python
try:
    args = json.loads(tc.function.arguments or "{}")
    parse_error = None
except json.JSONDecodeError as e:
    args, parse_error = {}, str(e)
```

**为什么会不合法**：模型输出被 `max_tokens` 截断、多了一个逗号、用了中文引号 `“”` 而不是 `""`、或者外面裹了 ` ```json ` 代码围栏。

**在 d1 里的位置**：`step3_fixed` 的 BUG 1 修复、`ref_norm_tool_calls`、`ref_tool_message`。

**官方依据（面试可直接引用）**：DeepSeek 文档原话——「模型并不总是生成有效的 JSON，并且可能会臆造出你函数模式中未定义的参数。**在调用函数之前，请在代码中验证这些参数。**」

**自测**：`json.loads('{"a": 1}')` 返回什么类型？`json.dumps({"a": "中文"})` 不加 `ensure_ascii=False` 会输出什么？

---

## 8. `isinstance` 与鸭子类型

**是什么**：判断对象是不是某个类型。

```python
print(isinstance("abc", str))            # True
print(isinstance({"a": 1}, dict))         # True
print(isinstance([1, 2], (list, tuple)))  # True   ← 第二个参数可以是元组，表示「其中之一」
print(isinstance(True, int))              # True   ← ⚠️ bool 是 int 的子类！
```

**在 d1 里的位置**：

```python
observation = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)
```

**为什么需要**：工具可能返回字符串，也可能返回 dict 或 list。但 `role="tool"` 消息的 `content` 字段**必须是字符串**。所以要判断：是字符串就直接用，不是就先序列化。

**判分器里也用它**：`isinstance(out, dict)`、`isinstance(out.get("total_tokens"), int)` —— 检查用户写的 `my_chat` 返回类型对不对。

**⚠️ 一个陷阱**：`isinstance(True, int)` 是 `True`。所以判分器里 `total_tokens` 如果用户返回了 `True`，也会被当成 int 通过。实际不太可能，但你要知道有这个坑。

**自测**：为什么不直接写 `str(out)` 而要先 `isinstance` 判断？（提示：`str({"a": 1})` 用的是单引号，不是合法 JSON）

---

# 🟠 第二梯队（9–21）

## 9. 类型标注：`-> dict`、`: str`、`list[dict]`

**是什么**：给参数和返回值标类型。**⚠️ Python 运行时完全不检查它**，纯粹是给人和 IDE 看的。

```python
def f(a: int, b: str = "x") -> dict:
    return {"a": a, "b": b}

f("不是int")        # ✅ 不报错！类型标注不做运行时检查
```

**常见写法**：

```python
def g() -> list[dict]:        # 返回「dict 组成的列表」，Python 3.9+ 可以直接这么写
def h(x: str | None):         # 可以是 str 或 None，Python 3.10+
def i(x: "MyClass"):          # 前向引用，用字符串
```

**在 d1 里的位置**：`_preflight() -> bool`、`ref_usage(u) -> dict`、`ref_norm_tool_calls(tcs) -> list`、`ref_tool_message(tool_call_id: str, result) -> dict`。

**为什么还要写**：
1. IDE 能自动补全（写了 `-> dict`，你打 `r["` 时它会提示有哪些键）
2. 阅读代码的人立刻知道输入输出形状
3. `mypy` / `pyright` 可以做静态检查
4. **D4 会用 `typing.get_type_hints()` 读取这些标注，自动生成工具的 JSON Schema** —— 那时候它就变成运行时真的有用的东西了

**自测**：类型标注写错了，程序会崩吗？

---

## 10. `getattr(obj, "name", default)`

**是什么**：安全地取属性。取不到就返回默认值，不抛 `AttributeError`。

```python
class A: pass
a = A()
print(getattr(a, "x", None))     # None   ← 属性不存在，返回默认值
print(a.x)                        # 💥 AttributeError
print(getattr(a, "x"))            # 💥 AttributeError（没给默认值）
```

**和 `dict.get()` 的对应关系**：

| 对象类型 | 安全取值 | 直接取值会崩 |
|---|---|---|
| dict | `d.get("k", 默认)` | `d["k"]` → KeyError |
| 对象 | `getattr(o, "k", 默认)` | `o.k` → AttributeError |

**在 d1 里的位置**：`ref_chat_stream` 里

```python
if getattr(chunk, "usage", None):
    usage = ref_usage(chunk.usage)
```

**为什么必须用 `getattr`**：**不同厂商的流式 chunk 结构不一样**。有的每一块都带 `usage=None`，有的中间块**根本没有 `usage` 这个属性**。直接写 `chunk.usage` 在后者上会 `AttributeError`。用 `getattr` 就两种都能兼容。

这就是「跨厂商可移植」的具体含义——不是抽象概念，就是这一行代码。

**自测**：为什么这里不用 `hasattr(chunk, "usage") and chunk.usage`？（提示：两种都行，但 `getattr` 少一次属性查找）

---

## 11. 生成器与 `yield`（流式输出的基础）

**是什么**：函数里出现 `yield`，它就不再是普通函数，而是**生成器函数**。调用它不会执行函数体，而是返回一个可以逐步「吐值」的迭代器。

```python
def count():
    print("开始")
    yield 1
    print("吐完 1 了")
    yield 2
    print("结束")

g = count()          # ⚠️ 这一行什么都不打印！函数体还没执行
print(next(g))       # 打印"开始"，然后 1
print(next(g))       # 打印"吐完 1 了"，然后 2
print(next(g))       # 打印"结束"，抛 StopIteration

for x in count():    # for 循环会自动处理 StopIteration
    print(x)
```

**🔑 核心区别**：`return` 一次性给全部结果；`yield` **边算边给**，给一个停一下，等你要下一个再继续。

**为什么流式必须用 `yield`**：模型是一个 token 一个 token 生成的。如果用 `return`，你必须等全部生成完（可能 30 秒）才能返回；用 `yield`，第一个 token 一到（可能 0.5 秒）就能显示给用户。这就是 **TTFT（Time To First Token）** 的意义。

**在 d1 里的位置**：`ref_chat_stream`

```python
yield {"delta": delta.content}                                    # 每来一块增量就吐出去
yield {"done": True, "content": "".join(parts), "usage": usage}   # 最后吐一个「结束信号」
```

调用方这样用：
```python
for ev in ref_chat_stream(messages):
    if "delta" in ev:
        print(ev["delta"], end="", flush=True)   # end="" 不换行，flush=True 立刻刷到屏幕
    if ev.get("done"):
        print(ev["usage"])
```

**`flush=True` 为什么必须加**：Python 的 stdout 默认有缓冲，不加的话你会看到「卡住 10 秒，然后一次性全部出现」——流式的意义完全丧失。

**自测**：`g = count()` 这一行执行时，"开始" 会被打印吗？为什么？

---

## 12. 三元表达式 `a if 条件 else b`

**是什么**：一行的 if-else，是个**表达式**（有返回值），不是语句。

```python
n = 7
label = "大" if n > 5 else "小"      # "大"
print(f"{'✅' if ok else '❌'} 通过")   # 常用来做条件符号
```

**读法**：先看中间的 `if`，成立就取**最左边**的值，不成立就取 `else` 后面的值。

**在 d1 里的位置**：
```python
client = OpenAI(...) if (OpenAI and API_KEY) else None
QUESTION = sys.argv[2] if len(sys.argv) > 2 else "深圳今天天气怎么样？"
observation = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)
```

**⚠️ 不要嵌套**。两层以上的三元表达式没人读得懂，老老实实写 if-else。

**自测**：`x = 1 if False else 2 if False else 3`，x 是多少？

---

## 13. `assert`：给代码装自检

**是什么**：条件不成立就抛 `AssertionError`。用来表达「我断定这里必须成立」。

```python
assert 1 + 1 == 2
assert r2.usage.prompt_tokens > r1.usage.prompt_tokens, "第二轮应该更贵"   # 逗号后是失败提示
```

**在 d1 里的位置**：`step1b_multiturn`（证明历史重发）、`step4_verify`（证明流式拿到了 usage）。

**⚠️ 两个重要限制**：
1. **`python -O` 优化模式下所有 assert 会被跳过**。所以 assert **不能**用来做生产环境的输入校验，只能用来做「开发期自检」。
2. 生产代码里校验用户输入要用 `if ... raise ValueError(...)`，不是 assert。

**为什么 D1 要用它**：你要**用数字证明**一个结论（历史重发、流式有 usage），assert 就是把这个证明写进代码里。跑通了 = 证明成立。这比「我看文档说应该是这样」有说服力得多——**这也正是「没有数字的产出等于没做」的具体落地**。

**自测**：能用 assert 校验用户传的 API key 格式吗？为什么？

---

## 14. `if __name__ == "__main__"` 与 `sys.argv`

**是什么**：区分「这个文件被直接运行」和「被别的文件 import」。

```python
# a.py
def hello(): print("hi")
print("模块级代码")              # import 时也会执行！

if __name__ == "__main__":
    hello()                      # 只有直接 python a.py 时才执行
```

```python
import a        # 会打印"模块级代码"，但不会打印"hi"
```

**`sys.argv` 是命令行参数列表，`argv[0]` 永远是脚本名本身**：

```python
# 运行：python d1_llm_client.py 3 上海天气
import sys
print(sys.argv)        # ['d1_llm_client.py', '3', '上海天气']
print(len(sys.argv))   # 3
```

**⚠️ 所以取第一个「真实参数」要用 `sys.argv[1]`，而且必须先判断长度**：

```python
arg = sys.argv[1] if len(sys.argv) > 1 else ""     # 不带参数时不会 IndexError
```

**在 d1 里的位置**：文件末尾的 `main()` 和 `if __name__ == "__main__": main()`；顶部的 `QUESTION = sys.argv[2] if len(sys.argv) > 2 else "..."`。

**为什么必须有 `if __name__`**：D2 起你会 `from llm_client import chat`。如果没有这个保护，**每次 import 都会把整个测试流程跑一遍**。

**自测**：`python d1_llm_client.py` 不带任何参数，`sys.argv` 是什么？为什么不报错？

---

## 15. 生成器表达式 + `all()` + 元组解包

**是什么**：三个惯用法组合在一起，是 Python 里做「批量检查」的标准写法。

```python
checks = [("名字对", True), ("类型对", False), ("非空", True)]

for name, ok in checks:            # 元组解包：一次拿两个变量
    print(name, ok)

print(all(ok for _, ok in checks))    # False  ← 有一个 False 就 False
print(any(ok for _, ok in checks))    # True   ← 有一个 True 就 True
```

- `(ok for _, ok in checks)` 是**生成器表达式**（圆括号），不是列表推导式（方括号）。它惰性求值，`all()` 遇到第一个 False 就立刻停止，不遍历完。
- `_` 是约定的「我不需要这个值」的变量名。

**在 d1 里的位置**：`step2_selftest` 的判分逻辑。

**自测**：`all([])` 返回什么？（答案：`True`。空集合「所有元素都满足」是真的——这叫 vacuous truth）

---

## 16. 模块级代码在 import 时就执行

**是什么**：不在任何函数里的代码，叫模块级代码。**它在文件被 import 或运行的那一刻就执行一次**。

```python
# config.py
import os
print("我被执行了")                 # import 时就打印
API_KEY = os.environ.get("KEY", "")  # import 时就取值
client = OpenAI(api_key=API_KEY)     # import 时就建连接
```

**在 d1 里的位置**：顶部这一整段

```python
if load_dotenv:
    load_dotenv()
API_KEY = os.environ.get("LLM_API_KEY", "")
BASE_URL = os.environ.get("LLM_BASE_URL") or None
MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")
client = OpenAI(...) if (OpenAI and API_KEY) else None
QUESTION = sys.argv[2] if len(sys.argv) > 2 else "深圳今天天气怎么样？"
```

**⚠️ 两个后果**：
1. **`.env` 必须在建 client 之前 `load_dotenv()`**。顺序反了，`os.environ` 里还没有 key，client 就是 None。这是新手最常踩的坑。
2. **模块级代码不能抛异常**，否则这个文件连 import 都做不到，你连「读代码」都不行。所以 d1 文件里 `client` 用了条件表达式兜底，而不是直接 `OpenAI(api_key=os.environ["LLM_API_KEY"])`。

**自测**：如果把 `load_dotenv()` 挪到 `client = OpenAI(...)` 后面，会发生什么？

---

## 17. `raise NotImplementedError` 作占位

**是什么**：写一个「故意没实现」的函数，运行时明确报错，而不是静默返回 None。

```python
def my_chat(messages):
    raise NotImplementedError("把这一行删掉，写你自己的实现")
```

**为什么不用 `pass`**：

```python
def my_chat(messages):
    pass                      # ⛔ 返回 None，调用方会在【别的地方】崩，报错信息误导你
```

`raise NotImplementedError` 的好处是：**报错点就在没实现的那个函数里**，一眼看到。

**在 d1 里的位置**：`my_chat` —— 你的作业起点。判分器专门捕获它：

```python
except NotImplementedError:
    print("你还没写 my_chat()。")
    return
```

**自测**：为什么 `pass` 比 `raise NotImplementedError` 更危险？

---

## 18. 多变量同时赋值

**是什么**：一行给多个变量赋值，右边可以是元组。

```python
a, b = 1, 2
a, b = b, a              # 交换，不需要临时变量
args, parse_error = {}, str(e)      # 异常分支里同时设两个
x = y = z = 0            # 链式赋值，三个都指向同一个对象
```

**在 d1 里的位置**：

```python
try:
    args = json.loads(tc.function.arguments or "{}")
    parse_error = None
except json.JSONDecodeError as e:
    args, parse_error = {}, str(e)      # ← 一行同时设两个，保证状态一致
parts, usage, finish = [], None, None   # ← 一行初始化三个
```

**为什么这么写**：`args` 和 `parse_error` 必须**同时**处于一致状态。分两行写，中间如果出异常，状态就不一致了。

**自测**：`a, b = 1, 2, 3` 会怎样？

---

## 19. `range` / `len` / `enumerate` / `for-else`

```python
for i in range(6):              # 0,1,2,3,4,5（不含 6）
for i in range(2, 6):           # 2,3,4,5
for i in range(0, 10, 2):       # 0,2,4,6,8（步长 2）

len([1,2,3])                    # 3

for i, v in enumerate(["a","b"]):    # (0,'a') (1,'b')  ← 同时要下标和值
    print(i, v)
```

**`for ... else`（少见但很重要）**：`else` 在循环**正常结束、没有被 break** 时执行。

```python
for tc in tool_calls:
    if tc["name"] == "get_weather":
        print("找到了"); break
else:
    print("没找到 —— 只有循环没被 break 才会走到这里")
```

**在 d1 里的位置**：`for turn in range(6)` 是 Agent 的最大轮次限制。Week1 附录 A.2 的 demo 用 `for...else` 打印「6 回合未收敛」。

**为什么 `range(6)` 很重要**：这是**双重终止条件**的一半。没有它，模型陷入「调工具 → 失败 → 再调同一个工具」的死循环时，你的程序会永远跑下去，把 API 额度烧光。D9 会加另一半：参数指纹去重。

**自测**：`for i in range(3): pass` 之后，`i` 的值是多少？（答案：2。Python 的循环变量在循环结束后仍然存在）

---

## 20. 字符串拼接与 `"".join(list)`

```python
parts = ["你", "好", "世界"]
print("".join(parts))        # 你好世界   ← 空字符串连接
print("-".join(parts))       # 你-好-世界
print("\n".join(parts))      # 每个一行

# ⛔ 不要用 += 在循环里拼字符串
s = ""
for p in parts: s += p       # 每次 += 都创建新字符串，O(n²) 复杂度
```

**在 d1 里的位置**：`ref_chat_stream` 最后 `"".join(parts)` 把所有增量片段拼成完整回答。

**为什么用 list 收集 + join**：Python 字符串不可变，`+=` 每次都要复制整个字符串。1000 个片段就是 1000 次复制。`append` 到 list 再 `join` 是一次性的 O(n)。

**自测**：流式返回 1000 个片段，`s += chunk` 和 `parts.append(chunk); "".join(parts)` 哪个快？为什么？

---

## 21. `sys.stdout.reconfigure` 与 `print` 的参数

```python
print("a", "b")                    # a b        默认用空格分隔
print("a", "b", sep="|")           # a|b
print("不换行", end="")             # 不换行，接着输出
print("立刻显示", flush=True)        # 立刻刷到屏幕，不等缓冲
```

```python
# Windows 控制台编码兜底
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
```

**为什么需要**：Python 在 Windows 上默认按系统代码页（中文系统是 GBK/cp936）输出。在 PowerShell / VS Code 终端 / Git Bash 里可能显示乱码。

**在 d1 里的位置**：文件顶部。如果还是乱码，在终端先执行一次 `chcp 65001`。

**`flush=True` 和流式的关系**：见第 11 条。没有它，流式输出会「卡住然后一次性全出现」，完全失去意义。

**自测**：`print(ev["delta"], end="", flush=True)` 里两个参数分别解决什么问题？

---

# ⚪ 第三梯队｜D4–D7 预告（现在扫一眼即可）

## 22. 装饰器 `@tool`（D4 工具注册表）

```python
TOOLS = {}
def tool(fn):                        # 装饰器就是一个「接收函数、返回函数」的函数
    TOOLS[fn.__name__] = fn
    return fn

@tool                                # 等价于 get_weather = tool(get_weather)
def get_weather(city: str) -> str:
    """查天气"""
    return "晴"

print(TOOLS)                         # {'get_weather': <function get_weather>}
```

D4 要用它实现「写个 `@tool` 就自动注册 + 自动生成 JSON Schema」。

## 23. `dataclass`（D4 的 `AgentResult`）

```python
from dataclasses import dataclass, field

@dataclass
class AgentResult:
    answer: str
    steps: int = 0
    tokens: dict = field(default_factory=dict)   # ⚠️ 可变默认值必须用 default_factory
```

比手写 `__init__` 少 20 行，还自带 `__repr__` 和 `__eq__`。

## 24. `with` 上下文管理器（D5 SQLite、D6 文件读写）

```python
with open("traces/day2.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(record, ensure_ascii=False) + "\n")
# 离开 with 块自动关闭文件，即使中间抛异常也关
```

## 25. `inspect.signature` + `typing.get_type_hints`（D4 自动生成 Schema）

```python
import inspect, typing
def get_weather(city: str, unit: str = "celsius") -> str:
    """查天气。city 是城市名。"""

print(inspect.signature(get_weather))            # (city: str, unit: str = 'celsius') -> str
print(typing.get_type_hints(get_weather))        # {'city': <class 'str'>, 'unit': <class 'str'>, 'return': <class 'str'>}
print(get_weather.__doc__)                        # 查天气。city 是城市名。
```

这三样合起来，就能**从一个普通 Python 函数自动生成 function calling 需要的 JSON Schema**——D4 的核心。

## 26. `dict.setdefault` 与 `defaultdict`（流式 tool_calls 累积）

```python
acc = {}
for d in deltas:                          # arguments 是分片到达的
    slot = acc.setdefault(d.index, {"name": "", "args": ""})
    slot["args"] += d.function.arguments or ""
# 之后才能 json.loads(acc[0]["args"])
```

`setdefault(k, 默认)`：键存在就返回已有值，不存在就先设成默认值再返回。省掉 `if k not in d: d[k] = ...`。

## 27. `pathlib.Path`（比 `os.path` 好用）

```python
from pathlib import Path
p = Path("traces") / "day2.jsonl"      # 用 / 拼路径，跨平台
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text("...", encoding="utf-8")
```

## 28. `functools.wraps`（写装饰器必备）

```python
from functools import wraps
def tool(fn):
    @wraps(fn)                          # 不加这行，被装饰函数的 __name__/__doc__ 会丢失
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper
```

不加 `@wraps`，`get_weather.__name__` 会变成 `'wrapper'`，D4 的自动注册就会把所有工具都注册成同一个名字。

---

## 附：三条学习建议

1. **每个最小例子都真的跑一遍**。新建一个 `scratch.py`，复制进去，`python scratch.py`。跑过和读过是两回事。
2. **报错原文是最好的老师**。看到 `TypeError: ... must be a mapping, not str` 时，逐词翻译它，而不是立刻去搜。90% 的报错已经把答案写在里面了。
3. **不要试图一次记住全部**。这份文档是**查询手册**，不是教材。卡住了再回来查，查三次自然就记住了。
