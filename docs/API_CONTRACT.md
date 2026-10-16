# API 契约

- 协议：HTTP/1.1，`GET` 只读。
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
| 405 | `METHOD_NOT_ALLOWED` | 非 `GET` 的 `/api/*` 请求 |
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
  正整数但不存在 → `404 NOT_FOUND`。
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

---

## 契约要点

- `mastery.prob` ∈ [0,1]，来自 32 画像对数后验边际；`correct_rate` 独立返回，UI 上必须分开呈现。
- 所有图表数据均由上述接口提供，前端不内置任何「掌握概率」常量。
- 服务端只读数据库，接口无副作用；真值 profile_id 不外泄。
- JSON 保留**有限浮点数**（如 `0.9333333`），不做展示百分比的截断/四舍五入；前端自行格式化。
