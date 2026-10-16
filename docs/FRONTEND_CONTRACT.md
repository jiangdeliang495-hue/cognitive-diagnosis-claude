# 前端契约（可执行验收契约）

本文档冻结浏览器 E2E 依赖的 DOM 契约。可执行版本见 `tests/browser_e2e.cjs`；
二者不一致时以测试为准。**前端实现必须遵循此契约**，测试才会通过。

> 原则：用稳定语义 + `data-testid`，不用脆弱坐标。数值一致性以 `data-value`
> 携带 API 原始浮点值（`parseFloat` 后按 1e-9 容差比对），不依赖展示格式。
> 学生 / 知识点名称一律取自真实 GET 接口，测试不硬编码。

## 1. 页面骨架

- `<meta name="viewport" content="width=device-width, initial-scale=1">`（移动端适配）。
- 文档 `<title>` 含「认知诊断」。
- `[data-testid="limitations"]` 元素含「合成」与「小样本」（明示合成小样本局限）。
- `[data-testid="loading"]` 加载态，可见文本含「加载」。初始加载与切换学生时均显示；
  切换学生时须**先清空当前诊断**（雷达/概率表/图谱）再显示加载，成功才渲染新数据，
  失败保持清空并显示错误（不把旧学生数据当作当前显示）。
- `[data-testid="error"]` 错误态，`role="alert"`，中文提示。
- `[data-testid="retry"]` 重试 `<button>`，文本「重试」；点击后重发失败的请求。

## 2. 学生切换

- `<select data-testid="student-select">`，须有 `<label for="student-select">` 关联。
- 12 个 `<option>`：`value` = 学生 `id`（1..12），文本 = 学生 `name`（学生01..学生12）。
- 默认选中第一个学生（`id=1`）。
- 键盘可达：聚焦后有可见焦点指示（`outline` 或 `box-shadow` 非 `none`）；
  `Home`/`End`/方向键可改变选中学生。macOS Chromium 原生 `<select>` 不响应
  `Home`/`End`，须显式 `keydown` 处理（设首/末选项并触发同一 `change` 加载），
  方向键保持原生行为。

## 3. 当前学生

- `[data-testid="current-student"]` 展示当前选中学生名称。

## 4. 雷达图（5 轴 SVG）

- `<svg data-testid="radar-chart" role="img" aria-label="…">`，`aria-label` 非空。
- 属性契约（供几何交叉验证）：
  - `data-values="p1,p2,p3,p4,p5"`：5 个原始掌握概率，KP1..KP5 顺序。
  - `data-center="cx,cy"`：雷达中心坐标。
  - `data-radius="R"`：最大半径（对应概率 1.0）。
- `<polygon data-testid="radar-polygon" points="x1,y1 … x5,y5">`：5 个顶点，KP1..KP5 顺序；
  第 i 个顶点距中心 `hypot(x-cx, y-cy) ≈ R × p_i`（测试以 0.5px 容差验证形状随值缩放）。

## 5. 掌握概率表

- `<table data-testid="mastery-table">`，5 行 `<tr data-testid="mastery-row" data-kp-id="1..5">`。
- 表头（或表内说明）须含「答对率」与「对照」——答对率**仅作对照，不是掌握概率**。
- 每行：
  - 知识点名（来自 API `mastery[].name`）。
  - 掌握概率单元格 `[data-testid="mastery-value"]`，`data-value` = 原始概率。
  - 答对率单元格 `[data-testid="correct-rate-value"]`，`data-value` = 原始答对率。

## 6. 知识图谱（5 节点 5 有向边）

- `<svg data-testid="knowledge-graph" role="img">`。
- 5 节点：`[data-testid="graph-node" data-kp-id="1..5" data-value="原始概率"]`；
  圆内放 `[data-testid="graph-node-value"]`（白色百分比），圆外下方放
  `[data-testid="graph-node-name"]`（深色完整名称）；可见/可访问文本含知识点名与百分比（`%`）。
- 5 有向边（前置→后续）：`[data-testid="graph-edge" data-parent="p" data-child="c"
  marker-end="url(#id)"]`，`marker-end` 必须引用 SVG 内**实际存在**的 `<marker>`（箭头）。
- 节点/边集合与 `GET /api/graph` 一致（5 边：1→2、1→4、2→3、3→5、4→5）。

## 7. 全体 12×5 概率表

- `<table data-testid="all-students-table">`，60 个单元格
  `[data-testid="matrix-cell" data-student-id data-kp-id data-value]`，
  覆盖 60 个唯一的 `(student_id, kp_id)` 对，逐格等于 `GET /api/diagnosis`。

## 8. 数据隔离与安全

- 页面任何位置不得出现 `profile_id`（HTML 属性、文本均不可）。
- 静态路由为白名单（`/`、`/index.html`、`/style.css`、`/app.js`）；
  MIME 各按 `text/html`、`text/css`、`text/javascript`，均 `charset=utf-8`；
  路径穿越与未知静态路径一律 404 JSON，不落到文件系统。

## 9. 数值格式

- JSON 保留有限浮点数（如 `0.9333333`），前端自行格式化为展示百分比；
  `data-value` 仍携带原始值供验收比对，不做截断/四舍五入到展示值。
