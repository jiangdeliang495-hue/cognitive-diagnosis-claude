# 智能化认知诊断 MVP

用 DINA 认知诊断模型从学生作答估计「每名学生 × 每个知识点」的掌握概率，提供中文图表与可选的 DeepSeek 学习建议。

- Python 标准库 + SQLite + 原生 HTML/CSS/JS，零第三方运行依赖、无 CDN。
- 合成数据：5 个知识点、24 道题（15 单技能 + 9 综合）、12 名学生、288 条作答。
- 核心诊断离线可用，不需要 API Key。可选建议仅在点击生成时调用外部付费 API。

> 这是合成小样本演示。掌握概率是模型估计，答对率仅作对照，二者不能混用。

## 快速开始

在项目根目录执行，使用带 SQLite 的 Python 3：

```bash
python3 -m src.seed diagnosis.db
python3 -m src.server diagnosis.db 8000
```

浏览器打开 <http://127.0.0.1:8000>，可切换 12 名学生，查看雷达图、概率对照表、前置知识图谱与 12×5 矩阵。建库固定种子、可复现；已有同名数据库会被拒绝，仅显式 `--force` 才重建。服务启动不会隐式建库，服务期间以只读方式访问数据库。

两个入口也支持直接脚本启动，例如 `python3 src/server.py diagnosis.db 8000`。默认仅监听本机，不应当作带用户认证的公网教学系统部署。

## 可选：生成 AI 学习建议

先停止已有服务，再启动隐藏输入模式：

```bash
python3 -m src.server diagnosis.db 8000 --prompt-key
```

在终端提示处私下输入自己的 DeepSeek API Key 并按回车；输入不回显，仅保留在当前服务进程中，不写入项目文件。服务也支持从已安全配置的环境变量 `DEEPSEEK_API_KEY` 获取密钥。不要把密钥放进浏览器、聊天、仓库或含明文密钥的命令历史。

刷新网页，选择学生并点击「生成学习建议」。该操作可能产生 API 费用；首屏、刷新、切换学生和免费状态查询不会自动生成，失败也不会自动重试。没有密钥时明确提示「未配置」，核心诊断仍可使用；状态网络失败显示独立错误，其「重试」只重新查询状态。

建议由固定的 `deepseek-v4-pro` 生成，开启 thinking、`reasoning_effort=max`、JSON 模式、`max_tokens=8192`。服务重读当前合成学生的已存掌握概率、答对率和前置关系，关闭只读连接后调用官方 HTTPS 接口；不发送真值或其他学生，不重跑 EM，不修改数据库或掌握概率。输出包含学习重点、原因、练习行动及检查方法，经结构校验后用纯文本显示。

供应商余额不足、限流、超时或无效输出均显示错误，不用规则建议冒充模型成功。TLS 证书验证始终开启；请使用具有有效 CA 信任链的 Python 环境。若本机出现证书链错误，先修复所用 Python 的证书配置，不要关闭验证。网络空闲超时为 60 秒，读取块间检查 120 秒截止，这不保证整个请求严格在 120 秒内返回。

**验收边界：**实现与模拟供应商测试已通过；尚未配置本次演示的运行时密钥，未完成真实付费 DeepSeek 成功调用。模拟测试和开发工具调用不能替代这项验收。

## 测试与证据

```bash
python3 -m unittest discover -s tests -v
```

完整后端 **147/147** 通过，含原核心 79 项回归，见 `docs/validation/advice-backend-external-final.txt`。原核心基线输出保留在 `docs/validation/python-external-final.txt`。

浏览器 QA 需要 Node.js ≥20 与 Playwright 1.62.1；应用运行不需要 Node：

```bash
npm install
npx playwright install chromium
# 另一个终端保持上述本地服务运行
E2E_BASE_URL=http://127.0.0.1:8000 node tests/browser_e2e.cjs
E2E_BASE_URL=http://127.0.0.1:8000 node tests/advice_e2e.cjs
```

原前端 **15/15** 通过（6 HTTP + 9 浏览器），建议区 **6/6** 通过，记录分别为 `frontend-regression-with-advice.txt`、`advice-e2e-final-external.txt`。建议 E2E 使用模拟付费路由，兜底中止未接管的建议 POST，不消耗真实模型额度。覆盖手动调用、重复点击、A→B→A 竞态、错误与状态恢复、文本注入、键盘及 390px 长词布局。截图见 `docs/screenshots/`；新增建议卡片截图展示真实的未配置状态。

## 算法与局限

- DINA 枚举 32 种掌握画像，用 And 门表示题目要求的全部知识点。
- 固定均匀先验；对数域 logsumexp 后验与约束 EM 校准 guess/slip，题参限制在 [0.02,0.35]。
- 掌握概率是画像后验的逐技能边际，不使用造数真值 `profile_id`。演示 EM 33 轮收敛。
- 图谱解释学习顺序，不改变潜在空间；LLM 解释已存诊断，不重新估计能力。
- 12 人 × 24 题是小样本；固定先验、题参硬区间、独立 Bernoulli 噪声与无缺失值都是简化。造数的前置单调假设不约束推断空间，结果不能外推为真实课堂的诊断准确性。

详见 [算法说明](docs/ALGORITHM.md) 与 [建议契约](docs/LLM_SUGGESTIONS.md)。

## 交付物与开发分工

| 路径 | 内容 |
|---|---|
| `src/`、`static/`、`tests/` | 标准库后端、原生前端、可复现测试 |
| `docs/PRD.md`、`ARCHITECTURE.md`、`ER.md`、`schema.sql` | 需求、架构、数据设计 |
| `docs/API_CONTRACT.md`、`FRONTEND_CONTRACT.md`、`LLM_SUGGESTIONS.md` | 接口与可执行验收契约 |
| `docs/DEVELOPMENT.md`、`DEVELOPMENT.pdf` | 开发过程说明 |
| `docs/PROMPT_LOG.md`、`TOOLCHAIN.md`、`evidence/`、`validation/` | 真实提示词、工具链、过程与测试证据 |
| `docs/SUBMISSION_DRAFT.md` | 未发送的提交邮件草稿 |

源码、测试及前期文档在 Claude Code 中通过配置的 DeepSeek 生成，实际使用 Superpowers。Codex 负责独立复核、外部 QA、Git 编排，并在用户授权后接手本轮文档收尾、PDF 排版与打包。本次建议功能开发的 Max 界面证据已保留；不声称旧阶段全程 Max，也不虚构用户手写或手测。

公开仓库：[cognitive-diagnosis-claude](https://github.com/jiangdeliang495-hue/cognitive-diagnosis-claude)。提交邮件尚未发送。
