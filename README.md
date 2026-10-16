# 智能化认知诊断 MVP（DINA 认知诊断）

用 **DINA（Deterministic Inputs, Noisy "And" gate）认知诊断模型**，从学生作答估计
「每名学生 × 每个知识点」的**掌握概率**，并用一个极简中文 Web 界面讲清楚。

- **零运行依赖**：仅 Python 标准库 + SQLite + 原生 HTML/CSS/JS，无 CDN、无第三方库、无 API Key。
- 演示数据：**5 个知识点、24 道题（15 单技能 + 9 综合）、12 名学生、32 种掌握画像**。
- 核心价值：把**掌握概率**与**答对率**严格区分，前端图表全部由真实诊断数据生成。

> 所有数据为**合成小样本**（12 人 × 24 题），掌握概率是估计而非确定判定，仅供演示。

## 快速开始（演示流程）

以下命令均在**项目根目录**执行：

```bash
# 1) 建库（一次性、可复现；已存在则报错，--force 显式重建）
python3 -m src.seed diagnosis.db

# 2) 启动只读服务（默认 http://127.0.0.1:8000，端口可改）
python3 -m src.server diagnosis.db 8000
```

浏览器打开 <http://127.0.0.1:8000>，即可切换 12 名学生，查看雷达图、掌握概率对照表、
前置知识图谱与全体 12×5 矩阵。

> `src/seed.py`、`src/server.py` 同样支持直接脚本启动：`python3 src/seed.py diagnosis.db`、
> `python3 src/server.py diagnosis.db 8000`。服务端**只读**数据库，不写盘、不联网。

## 运行依赖

| 类别 | 依赖 | 说明 |
|---|---|---|
| **运行** | Python 3 标准库 + SQLite（`sqlite3`） | 零第三方运行依赖；已在 Python 3.13.10 验证 |
| **仅 QA** | Node.js ≥ 20（`package.json` engines；实测 24.19.0）+ Playwright 1.62.1 | 仅用于浏览器 E2E，见 `package.json` 的 `devDependencies`；应用运行不需要 |

不要求任何 API Key，也不访问网络/密钥。

## 测试

### Python 测试（标准库）

```bash
python3 -m unittest discover -s tests -v
```

全套 **79 项** unittest（算法内核 22 项 + schema/seed/API 数据链 + CLI 回归）外部验收通过，
见 `docs/validation/python-external-final.txt`。

### 浏览器 E2E（仅 QA，可选）

仅 QA 需要 Node.js（`package.json` engines 要求 **Node ≥ 20**，实测 Node 24.19.0）：

```bash
npm install                      # 安装仅 QA 的 devDependency（playwright 1.62.1）
npx playwright install chromium  # 准备 Chromium 浏览器
```

```bash
# 先起服务，再跑 Node 脚本（无 @playwright/test，用 Node 自带 assert）
E2E_BASE_URL=http://127.0.0.1:8000 node tests/browser_e2e.cjs
# 仅跑 HTTP 静态契约部分（不需要浏览器）：
E2E_BASE_URL=http://127.0.0.1:8000 node tests/browser_e2e.cjs --http-only
```

15 组前端验收（6 组 HTTP 静态 + 9 组浏览器）外部通过，见 `docs/validation/frontend-external-final.txt`；
桌面/390px 截图见 `docs/screenshots/desktop.png`、`docs/screenshots/mobile.png`。
应用运行不需要 Node、模型 API Key 或任何第三方库。

## 界面功能

- 12 名学生切换（键盘可达、可见焦点）。
- 雷达图（5 轴，值为真实掌握概率）+ 掌握概率/答对率**对照表**（答对率明确标注「对照」）。
- 前置知识图谱（5 节点 5 箭头，前置 → 后续，节点显示名称 + 百分比）。
- 全体 12×5 掌握概率矩阵（突出当前学生；移动端表格容器内横向滚动）。
- 中文加载/错误/重试；快速切换用 AbortController 防旧结果覆盖；390px 无横向溢出。

## 算法要点

- 潜在画像 α ∈ {0,1}^K，共 32 种；理想作答为 And 门（须掌握题目所需**全部**知识点）。
- 固定均匀先验 1/32；题参 guess/slip ∈ [0.02, 0.35]，EM 对数域 logsumexp 校准。
- 掌握概率 = 画像后验的逐技能边际；**不是**答对率，也不由合成真值 `profile_id` 生成。
- 详见 `docs/ALGORITHM.md`。

## 已知限制

- **合成小样本**：12 人 × 24 题，后验边际方差大，估计不精确。
- **画像单调强假设**只约束**造数**，不裁剪模型推断（模型仍允许 32 画像）。
- **固定均匀先验**：短题列（信息少）的后验更接近先验。
- **guess/slip 硬区间 [0.02, 0.35]**：小样本正则化，可能低估极端题参。
- **作答为独立 Bernoulli 噪声**：无真实学生异质性、无缺失值，恢复精度不外推真实课堂。
- 可选加分项「LLM 学习建议」**未实现**（不影响核心验收）。

## 交付物

| 文档 | 说明 |
|---|---|
| [docs/PRD.md](docs/PRD.md) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/ER.md](docs/ER.md) · [docs/API_CONTRACT.md](docs/API_CONTRACT.md) · [docs/schema.sql](docs/schema.sql) | 需求/架构/ER/接口/模式 |
| [docs/ALGORITHM.md](docs/ALGORITHM.md) | DINA 算法说明与实测验证 |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) · [docs/DEVELOPMENT.pdf](docs/DEVELOPMENT.pdf) | 开发过程说明（1–1.5 页；PDF 由外部编排排版生成） |
| [docs/TOOLCHAIN.md](docs/TOOLCHAIN.md) | 工具链与模型路由如实说明 |
| [docs/PROMPT_LOG.md](docs/PROMPT_LOG.md) | 阶段真实 Prompt 全文 + 索引 |
| [docs/validation/](docs/validation/) | 各阶段 RED/GREEN 原始命令、退出码、输出 |
| [docs/evidence/](docs/evidence/) | 脱敏工具链证据（插件/技能调用/路由/UI 回归顺序） |
| [docs/screenshots/](docs/screenshots/) | 桌面与 390px 移动截图 |

## 目录结构

```
src/    db.py data_gen.py dina.py seed.py server.py   # 纯标准库实现
static/ index.html style.css app.js                    # 原生前端（零依赖）
tests/  test_dina.py test_schema.py test_seed.py test_api.py test_cli.py browser_e2e.cjs
docs/   设计/契约/算法/开发说明/证据/验证
```

> GitHub 私有仓库：[https://github.com/jiangdeliang495-hue/cognitive-diagnosis-claude](https://github.com/jiangdeliang495-hue/cognitive-diagnosis-claude)
> （私有仓库，评审需要仓库访问权限）。提交邮件**尚未发送**。
