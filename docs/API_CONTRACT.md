# API 契约

- 协议：HTTP/1.1。核心 GET 与模型状态 GET 离线只读；建议 POST 只读数据库，但会请求外部付费服务。
- 编码：UTF-8；`Content-Type: application/json; charset=utf-8`。
- `application/json` **仅用于 `/api/*`**；静态资源按扩展名各给 MIME：
  `.html`→`text/html`、`.css`→`text/css`、`.js`→`text/javascript`（均 `charset=utf-8`）。
- 地址：`http://127.0.0.1:8000`（演示默认端口，可配置）。
- 错误格式（统一）：

```json
{ "error": { "code": "NOT_FOUND", "message": "学生不存在" } }
```

| HTTP | code | 场景 |
|---|---|---|
| 404 | `NOT_FOUND` | 资源不存在 |
| 400 | `BAD_REQUEST` | 参数非法（含非正整数 ID） |
| 405 | `METHOD_NOT_ALLOWED` | 核心 GET 接口收到非 GET 请求，或建议路径使用非 POST 方法 |
| 500 | `INTERNAL` | 未预期异常 |

---

## 真值隔离（贯穿所有接口）

所有「掌握概率」均来自 **`fit(Q, X, …)` 对 SQLite 中 Q/X 矩阵校准后的对数后验边际**
（`diagnosis` 表），**不是**由合成真值 `profile_id` 生成。`profile_id` 只用于生成与
E2E 验证，**不经任何 API 暴露**。前端能拿到的只有估计掌握概率与答对率对照。

---

## 1. GET /api/meta

元信息 + 知识点 + 前置边。

```json
{
  "name": "智能化认知诊断 MVP",
  "knowledge_points": [
    { "id": 1, "code": "KP1", "name": "分数概念", "description": "…" }
  ],
  "prerequisites": [
    { "parent": 1, "child": 2 }
  ],
  "student_count": 12,
  "question_count": 24,
  "profile_count": 32
}
```

## 2. GET /api/students

学生列表（仅 id 与名称，**不含真值 profile_id**）。

```json
{ "students": [ { "id": 1, "name": "学生01" } ] }
```

## 3. GET /api/students/{id}

单名学生诊断结果。`mastery` 为 DINA 掌握概率（对数后验边际）；`correct_rate` 为答对率，
**仅作对照，前端须明确标注它不是掌握概率**。二者顺序均按 KP1..KP5 对齐。

- `id` 须为**正整数**：非正整数（`0`、负数、非数字）→ `400 BAD_REQUEST`；
  正整数但超出 SQLite INTEGER 存储范围（> 9223372036854775807，即 2^63−1）→ `400 BAD_REQUEST`；
  范围内的正整数但不存在 → `404 NOT_FOUND`。
- `correct_rate` 逐知识点以「Q 矩阵中 `required=1` 的题」为分母；综合题计入其涉及的
  每个知识点（同一道综合题会进入多个知识点的分母）。

```json
{
  "student": { "id": 3, "name": "学生03" },
  "mastery": [
    { "kp_id": 1, "code": "KP1", "name": "分数概念", "prob": 0.93 }
  ],
  "correct_rate": [
    { "kp_id": 1, "code": "KP1", "name": "分数概念", "rate": 0.80 }
  ]
}
```

## 4. GET /api/graph

静态知识图谱结构（节点 + 前置边）。前端将其与 `/api/students/{id}` 的 `mastery` 合并，
按学生掌握概率给节点着色。

```json
{
  "nodes": [ { "id": 1, "code": "KP1", "name": "分数概念" } ],
  "edges": [ { "parent": 1, "child": 2 } ]
}
```

## 5. GET /api/items

Q 矩阵（长表展开为 0/1 向量，顺序 KP1..KP5）与 EM 校准题参，供校验/透明展示。

```json
{
  "items": [
    {
      "question_id": 5,
      "stem": "应用题建模/列式",
      "q": [0, 0, 0, 0, 1],
      "guess": 0.20,
      "slip": 0.10
    }
  ]
}
```

## 6. GET /api/diagnosis

全体诊断矩阵（学生 × 知识点 概率），便于一次性导出。
`matrix` 为 60 行（12 学生 × 5 知识点）长表，按 `(student_id ASC, kp_id ASC)` 排序。

```json
{
  "matrix": [
    { "student_id": 1, "kp_id": 1, "prob": 0.02 }
  ]
}
```

## 7. 静态资源

| 路径 | 说明 |
|---|---|
| `GET /` | `static/index.html` |
| `GET /style.css` | 样式 |
| `GET /app.js` | 前端逻辑（拉取上述接口、渲染 SVG 雷达图与图谱） |

## 8. LLM 学习建议（已实现）

> 详见 [LLM_SUGGESTIONS.md](LLM_SUGGESTIONS.md)。后端与建议区模拟测试已通过；真实付费成功调用尚待运行时密钥配置。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/llm/status` | 非付费状态：`configured/provider/model/reasoning_effort`，无密钥内容、无外网 |
| POST | `/api/students/{id}/advice` | **唯一付费接口**：请求体严格 `{}`；服务端按 ID 重读该生已存 DINA 掌握概率与独立答对率、5 知识点与前置边（只读连接关闭后调用供应商），绝不读 `profile_id`/其他学生、不重跑 EM、不改库；成功返回服务器封装的 `{student_id, source:"llm", provider, model, reasoning_effort, request_id, advice}` |

- 密钥仅来自服务端环境 `DEEPSEEK_API_KEY`（缺失 → 503 `LLM_NOT_CONFIGURED`），不进浏览器/日志/仓库；
  `python3 -m src.server … --prompt-key` 用 `getpass` 隐藏输入、仅写当前进程环境。
- 供应商固定 `https://api.deepseek.com/chat/completions`，`model=deepseek-v4-pro`，Bearer，
  `thinking={type:enabled}`、`reasoning_effort=max`、`response_format={type:json_object}`、
  `stream=false`、`max_tokens=8192`，不设 temperature，禁止重定向，不自动重试；
  只取 `choices[0].message.content`。
- 安全：只接受小体积 `application/json` 且严格 `{}`；拒绝 chunked/重复或歧义 Content-Length；
  异源 Origin/`Origin:null`/不可信 Host 拒绝且不调用供应商；无宽泛 CORS；错误不回显上游 body/密钥。
- 错误码：400 `BAD_REQUEST` / 404 `NOT_FOUND` / 405 / 413 `REQUEST_TOO_LARGE` /
  403 `ORIGIN_FORBIDDEN`/`HOST_FORBIDDEN` / 429 `BUSY` / 503 `LLM_NOT_CONFIGURED`/`LLM_RATE_LIMITED` /
  502 `LLM_UNAUTHORIZED`/`LLM_PAYMENT_REQUIRED`/`LLM_UPSTREAM_ERROR`/`NETWORK`/`BAD_RESPONSE` /
  504 `TIMEOUT`（均中文提示）。
- 前端建议区（data-testid：advice-section/generate-advice/advice-config-missing/advice-loading/
  advice-error/advice-retry/advice-content）：只有点击才 POST；生成中禁连点；切学生清空并 abort；
  响应校验学生 ID+序号；textContent 安全渲染。

---

## 契约要点

- `mastery.prob` ∈ [0,1]，来自 32 画像对数后验边际；`correct_rate` 独立返回，UI 上必须分开呈现。
- 所有图表数据均由上述接口提供，前端不内置任何「掌握概率」常量。
- 服务端只读数据库；核心 GET 无外网，建议 POST 有外部调用及潜在费用，不声称全部接口无副作用。真值 profile_id 不外泄。
- JSON 保留**有限浮点数**（如 `0.9333333`），不做展示百分比的截断/四舍五入；前端自行格式化。

文档同步：本轮由 Codex 对照已实现代码及外部测试记录整理。
