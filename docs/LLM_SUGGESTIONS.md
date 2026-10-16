# LLM 学习建议（加分项）—— SDD 冻结契约与实现计划

> 状态：**契约已冻结，实现未开始**。本文与 tests/test_advice.py、tests/test_advice_api.py、
> tests/advice_e2e.cjs 共同构成该功能的 RED 契约；实现须使三者全部转绿。
> 真实付费 API 验收单独进行（见 §8），mock 不算真实 DeepSeek 调用。

## 1. 功能边界

- 页面新增「AI 学习建议」区。**只有**当前学生详情加载成功**且用户点击「生成学习建议」才发
  POST；首屏/切学生/刷新**不自动计费、不自动重试**。
- 建议有独立 loading/error/retry，不影响已有诊断区；生成中按钮禁用防连点。
- 切学生**立即清空**建议并 abort 旧等待；响应校验学生 ID + 请求序号，**绝不**把旧学生建议
  显示给新学生。模型输出全部 textContent/DOM 安全渲染，**禁用 innerHTML**。
- 失败可手动重试；真实配置缺失时明确中文提示，**绝不伪造规则建议为 LLM 成功**。

## 2. 服务端接口（新增，全部只读 DB / 不重跑 EM / 不改库）

### GET /api/llm/status（非付费、无外网、无密钥内容）

```json
{ "configured": false, "provider": null, "model": null, "reasoning_effort": null }
```

或（已配置时）：

```json
{ "configured": true, "provider": "deepseek", "model": "deepseek-v4-pro", "reasoning_effort": "max" }
```

### POST /api/students/{id}/advice（唯一付费接口）

- 请求：`Content-Type: application/json`，请求体**严格 `{}`**（无任何键、无嵌套）；
  浏览器不能提交概率/prompt/key/model/baseURL。
- 服务端按 ID 从**只读 SQLite** 重读该生已存 `diagnosis.mastery_prob`、独立重算 `correct_rate`、
  5 知识点与前置边，**关闭只读连接后**才调用供应商；绝不读 `profile_id`/其他学生资料。
- 成功 200（服务器封装）：

```json
{
  "student_id": 3, "source": "llm", "provider": "deepseek",
  "model": "deepseek-v4-pro", "reasoning_effort": "max",
  "request_id": null,
  "advice": {
    "summary": "本周重点：…",
    "priorities": [
      { "kp_id": 2, "reason": "…", "actions": ["…", "…"], "check": "…" }
    ]
  }
}
```

（`request_id` 取供应商响应 `id`，可脱敏保留；usage 不回传前端。）

- 错误统一 `{ "error": { "code", "message" } }`，映射如下（message 中文，**绝不回显上游
  body/异常 repr/密钥**）：

| HTTP | code | 场景 |
|---|---|---|
| 400 | BAD_REQUEST | 非法 ID；请求体非严格 `{}`；Content-Type 非 application/json |
| 404 | NOT_FOUND | ID 不存在 |
| 405 | METHOD_NOT_ALLOWED | advice 非 POST（原 6 个 GET 的 POST 仍 405） |
| 413 | REQUEST_TOO_LARGE | 客户端请求体超过 MAX_REQUEST_BYTES=4096 字节 |
| 403 | ORIGIN_FORBIDDEN | 异源 Origin / `Origin: null`（不调用供应商） |
| 403 | HOST_FORBIDDEN | 不可信 Host（不调用供应商） |
| 429 | BUSY | 并发付费请求超上限（MAX_CONCURRENT_ADVICE=1），可手动重试 |
| 503 | LLM_NOT_CONFIGURED | 未配置密钥 |
| 502 | LLM_UNAUTHORIZED | 上游 401 |
| 502 | LLM_PAYMENT_REQUIRED | 上游 402 |
| 503 | LLM_RATE_LIMITED | 上游 429，可手动重试 |
| 502 | LLM_UPSTREAM_ERROR | 上游 3xx（重定向，**绝不跟随**）或 5xx |
| 502 | NETWORK | URLError/OSError |
| 502 | BAD_RESPONSE | 空 content/截断/损坏响应（HTTPException/IncompleteRead）/畸形或超长 JSON/未知或重复技能 ID/响应超字节上限 |
| 504 | TIMEOUT | 整体截止超时（含 socket 空闲超时触发的轮询超期） |
| 500 | INTERNAL | 提示词序列化超过 MAX_PROMPT_BYTES 内部上限（理论上不应发生） |

- 路由先**精确匹配** `/api/students/{id}/advice`，避免被学生详情的宽泛前缀误判。
- 只接受小体积 application/json；拒绝 chunked、重复/**冲突** Content-Length、TE+CL 并存、
  非 `{}` 请求体（framing 检查先于一切，不因 Host/Origin 检查而掩盖）。
- Origin 规则（冻结）：无 Origin → 允许（本机 JSON 客户端）；带 Origin → 必须是**同源**
  `http://{127.0.0.1|localhost|::1}:<实际绑定端口>`（成功正例，见 test_advice_api）；同 hostname
  **异端口**、恶意后缀域名（如 `127.0.0.1.evil.example`）、任何异源 → 403 且**零供应商调用**。
- Host 规则（冻结）：hostname ∈ {127.0.0.1, localhost, ::1} 为可信（端口不校验）；其余 403。
- 无宽泛 CORS（成功响应不带 Access-Control-Allow-Origin）。
- 请求前后 DB 文件 hash 不变；核心 6 个 GET 仍无外网、不需要密钥。

## 3. 密钥（冻结）

- 运行时密钥**仅**来自服务端环境变量 `DEEPSEEK_API_KEY`；缺失/空串 → 503 LLM_NOT_CONFIGURED。
- 密钥不进浏览器/HTML/JSON/日志/仓库；**严禁**读取 Claude 配置、Keychain、旧剪贴板或任何已有密钥。
- 新增 `python3 -m src.server [db] [port] --prompt-key`：标准库 `getpass` 隐藏输入，仅写入当前
  进程环境（`os.environ`），不存盘；原位置参数/`--host` 与原 79 项测试保持兼容。

## 4. 供应商（已核实，冻结）

- 固定 HTTPS 地址 `https://api.deepseek.com/chat/completions`；`model=deepseek-v4-pro`；
  Bearer 认证；`thinking={"type":"enabled"}`、`reasoning_effort="max"`；
  `response_format={"type":"json_object"}`；`stream=false`；`max_tokens=8192`（为最高思考留预算）。
  **不设 temperature**（不假称控制思考）。
- 只取 `choices[0].message.content`，**不返回 reasoning_content**。
- 字节上限**两个独立常量，不混用**：
  - `MAX_REQUEST_BYTES = 4096`：**客户端 POST 请求体**上限（严格 `{}`，4 KiB 足够）。
  - `MAX_PROMPT_BYTES = 16384`：**供应商完整请求 JSON**上限（中文诊断 + 系统约束可能超过
    4 KiB，留 16 KiB）；超出 → 500 INTERNAL（见 §2）。
  - `MAX_RESPONSE_BYTES = 1 MiB`：供应商响应上限。
- 网络超时**两级**（如实限定，不过度承诺）：
  - `SOCKET_TIMEOUT=60s`：socket 空闲超时（`urlopen(timeout)` 语义），**连接/代理/TLS 阶段只受
    该超时约束**；响应读取中 `read1` 抛 `socket.timeout`（真实 HTTPResponse 缓冲对象可能已
    不可继续读）→ **立即安全关闭响应并返回 TIMEOUT**，绝不 catch 后继续轮询。
  - `OVERALL_DEADLINE=120s`：**响应读取截止检查**——每次有界读取之前检查单调时钟，超期 →
    关闭响应并抛 DeadlineError。**不声称**整次请求严格 120s 墙钟上限。
- **默认传输为单线程读取循环**：用 `read1(amt)` 做**单次有界读取**（禁止聚合 `read()`，
  防一次调用内部连续底层读跨过截止），块之间检查单调时钟；**不创建任何额外线程**
  （因此不存在线程堆积）；任何路径 `finally` 关闭响应资源。
- 损坏响应：`read1` 抛 `http.client.HTTPException`/`IncompleteRead`/`ValueError` → 关闭响应
  并映射 502 BAD_RESPONSE（脱敏）。
- **不自动重试**。固定供应商地址并**禁止重定向**：302 Location 指向异源时**绝不发起第二次
  请求**（因此绝不转发 Authorization），映射 502 LLM_UPSTREAM_ERROR；该策略为**行为契约**，
  由测试验证（见 tests/test_advice.py 与 tests/test_advice_api.py），不以 opener handler
  类型内省作为契约。

## 5. 提示词与建议结构（冻结）

- 中文提示词必须：说明掌握概率是**模型估计**且与答对率区分；关注薄弱知识与前置关系；
  给出具体练习动作与检查方法；**不编造**学生经历/测验结果；说明合成小样本局限。
- 掌握概率与答对率均以 3 位小数（如 `0.933`）进入提示词；每条前置边以
  `KP<parent>→KP<child>`（如 `KP1→KP2`）形式列出；两个学生的提示词必然不同。
- 输出结构：

```json
{
  "summary": "string",
  "priorities": [
    { "kp_id": 1, "reason": "string", "actions": ["string"], "check": "string" }
  ]
}
```

- `priorities` 1~3 项，`kp_id` 为**存在且互异**的知识点 ID；**布尔型 kp_id 必须拒绝**
  （Python `bool` 是 `int` 子类，须显式排除）；`actions` 1~3 条。
- 文本长度（`len()` 字符）：summary ≤ 300、reason ≤ 200、每 action ≤ 200、check ≤ 200；
  全部非空（去首尾空白后）。
- **未知字段必须剥离**：规范化输出仅含固定键（顶层 `summary`/`priorities`，优先级项
  `kp_id`/`reason`/`actions`/`check`），模型 JSON 的其它字段不得原样带出。
- JSON mode **不替代应用校验**：空 content、`finish_reason` 非 `"stop"`（含 `length` 截断、
  缺失、`content_filter`）、choices/message/content 缺失或错类型、畸形或超长 JSON、
  未知或重复技能 ID 一律拒绝（502 BAD_RESPONSE）。

## 6. 模块接口（冻结，src/advice.py，纯标准库）

```python
MODEL = "deepseek-v4-pro"
PROVIDER_URL = "https://api.deepseek.com/chat/completions"
REASONING_EFFORT = "max"
MAX_REQUEST_BYTES = 4096        # 客户端 POST 请求体上限（严格 {}，4 KiB 足够）
MAX_PROMPT_BYTES = 16384        # 供应商完整请求 JSON 上限（中文诊断 + 约束，16 KiB）
MAX_RESPONSE_BYTES = 1_048_576  # 供应商响应上限（1 MiB）
MAX_CONCURRENT_ADVICE = 1
SOCKET_TIMEOUT = 60.0           # socket 空闲超时（仅轮询粒度，非整体截止）
OVERALL_DEADLINE = 120.0        # 整体响应截止
MAX_SUMMARY_LEN = 300
MAX_REASON_LEN = 200
MAX_ACTION_LEN = 200
MAX_CHECK_LEN = 200

class AdviceError(Exception):
    """code ∈ {BAD_ADVICE, BAD_REQUEST, REQUEST_TOO_LARGE, INTERNAL,
               LLM_UNAUTHORIZED, LLM_PAYMENT_REQUIRED, LLM_RATE_LIMITED,
               LLM_UPSTREAM_ERROR, TIMEOUT, NETWORK, BAD_RESPONSE}"""
    def __init__(self, code: str, message: str): ...

class DeadlineError(Exception):
    """整体响应截止触发（default_transport 内部使用）。"""

def check_request_json(body: bytes) -> None
    # 严格 {}（允许首尾空白）；> MAX_REQUEST_BYTES → REQUEST_TOO_LARGE；其余畸形 → BAD_REQUEST

def build_prompt(mastery, correct_rate, kps, edges) -> str
    # mastery / correct_rate: [(kp_id, name, value), ...]（KP1..KP5 顺序）
    # kps: [(id, name)]；edges: [(parent, child)]

def parse_advice(content: str, known_kp_ids) -> dict
    # 校验并返回规范化 dict；违反 §5 → AdviceError("BAD_ADVICE", 中文)

def build_llm_payload(prompt: str) -> dict
    # model/thinking/reasoning_effort/response_format/stream/max_tokens 锁定，无 temperature

def build_request(api_key: str, prompt: str) -> tuple[str, dict, bytes]
    # (PROVIDER_URL, {"Authorization": "Bearer <key>", "Content-Type": "application/json"}, body)
    # 序列化后 body 超过 MAX_PROMPT_BYTES → AdviceError("INTERNAL", ...)

def build_opener() -> urllib.request.OpenerDirector
    # 生产 opener：以 NoRedirect(HTTPRedirectHandler) 子类禁用重定向（实现方式，不作契约；
    # 302 不跟随、不转发 Authorization 由行为测试保证）

def default_transport(url, data, headers, socket_timeout, deadline,
                      *, opener=None, clock=time.monotonic, chunk=65536) -> tuple
    # 默认网络层（单线程，不创建线程；只做单次有界 read1，禁止聚合 read）：
    #   每次 read1 前检查 clock() >= deadline → 关闭响应并抛 DeadlineError（读取截止检查）；
    #   read1 抛 socket.timeout → 立即关闭响应并抛 AdviceError("TIMEOUT")（不继续轮询）；
    #   read1 抛 http.client.HTTPException / IncompleteRead / ValueError → 关闭响应
    #     并抛 AdviceError("BAD_RESPONSE", 脱敏中文)；
    #   opener.open 抛 urllib.error.HTTPError（含 302/3xx）→ 按状态映射，关闭其 fp，
    #     不回显响应体/Location；URLError/OSError → NETWORK；socket.timeout → TIMEOUT；
    #   任何路径 finally 关闭响应资源；opener=None 时用 build_opener()。

def call_provider(transport, api_key, prompt, *, overall_deadline=OVERALL_DEADLINE) -> tuple
    # transport(url, data, headers, socket_timeout, deadline) -> (status:int, headers:dict, body:bytes)
    # 可抛 socket.timeout / DeadlineError / URLError / OSError / AdviceError
    # 返回 (content:str, finish_reason:str|None, request_id:str|None, usage:dict|None)
    # 失败抛 AdviceError（见 §2 错误映射的模块层部分）；不自动重试

def status_payload(api_key) -> dict
    # 空/None → 全部 None；否则 {"configured": True, "provider": "deepseek", "model": MODEL,
    # "reasoning_effort": "max"}；不含密钥
```

服务端注入（冻结）：`server.make_server(db_path, *, host="127.0.0.1", port=0, llm=None)`

- `llm=None`：自动读环境 `DEEPSEEK_API_KEY`（空串=未配置），transport 用默认（build_opener）。
- `llm={"key": str, "transport": callable}`：显式配置（测试注入 mock transport）。
- `llm={"key": None}`：显式未配置。
- 原调用（不传 llm）与原 79 项测试完全兼容。

## 7. UI 契约（冻结 data-testid）

| testid | 语义 |
|---|---|
| `advice-section` | AI 学习建议区（当前学生） |
| `generate-advice` | 「生成学习建议」按钮（configured=true 才显示；生成中 disabled） |
| `advice-config-missing` | 未配置提示（中文，含「未配置」） |
| `advice-loading` | 独立加载态（文本含「生成」或「建议」） |
| `advice-error` | 独立错误，role="alert" |
| `advice-retry` | 重试按钮（文本「重试」） |
| `advice-content` | 建议内容（仅 textContent 渲染；含 summary 与 priorities 文本） |

行为：学生详情成功后 GET `/api/llm/status`（非付费）；`configured=false` → 显示
config-missing、不显示按钮、不可能发 POST；点击才 POST；切学生清空建议并 abort 旧等待；
渲染全部用 textContent/DOM API，禁 innerHTML。
E2E 备注：
- **兜底安全网**：先注册 catch-all 路由，任何未被具体 mock 接管的付费 POST 一律 abort 并判违规，
  绝不意外打到真实 API；具体 mock 后注册者优先。
- C4 故意 mock 502 会产生 Chromium 的预期资源 console.error，测试用 `expectFail(url)` 显式豁免
  该注入 URL 的失败，其余 pageerror 与非预期 console.error 仍零容忍。
- C2/C3 用等待「请求已被捕获/已进入挂起 gate/已落定」的确定时序，不用固定 sleep 冒充竞态已测；
  C3 含 A→B→A 且最早 A 最后返回的同学生 ID 旧请求竞态（按请求序号丢弃）。
- C6 用真实 Tab 遍历 + Space/Enter 键盘激活按钮，不用 focus+鼠标 click 冒充键盘验收；
  合法长度连续英文长词必须换行，390px 无横向溢出。
- 未配置/清空状态允许「隐藏的空容器」实现，断言以可见性为准而非 DOM 节点存在性。

## 8. 测试与实现计划

1. **RED（本轮）**：tests/test_advice.py（纯逻辑 + mock transport）、tests/test_advice_api.py
   （mock 供应商 + 真实本机 HTTP）、tests/advice_e2e.cjs（mock 路由交互契约）。当前 src/advice.py
   不存在 → 收集即 RED；HTTP/浏览器受沙箱限制，外部命令见 PROMPT_LOG 阶段 7。
2. **GREEN（下轮）**：实现 src/advice.py + server 集成 + `--prompt-key` + static 建议区，
   使三份测试转绿；原 79 项 Python 与 15 组前端回归不回归。
3. **真实付费验收（单独进行）**：配置真实 DEEPSEEK_API_KEY 后对 1~2 名学生做人工点击验收，
   核对建议内容合理性与计费行为；mock 测试不算真实 DeepSeek 调用。
