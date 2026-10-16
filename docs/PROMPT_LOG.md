# PROMPT_LOG —— 本会话实际收到的核心提示词

本文件**逐步、如实**记录本会话真实收到的核心提示词，每段配 1–2 句说明。
**未发生的阶段不会在这里被标记为「完成」。**

> **过程与模型路由（如实记录）**
> - 前期过程：Codex 代用户操作 Claude Desktop Code；源码、测试及前期文档由该会话模型与 Superpowers 工作流完成。
> - 后续收尾：用户授权 Codex 接手最终文档、PDF、打包与发布；收尾记录单列，不伪装成 Claude 会话提示词。
> - 模型路由：界面 **DeepSeek V4 Pro**，发送兼容别名 `claude-opus-4-8`，
>   **DeepSeek Gateway 路由**（`https://api.deepseek.com/anthropic`）。
> - 本会话未读取任何 API Key，也不声称读取过真实供应商的内部身份。

---

## 当前交付状态（Codex 同步，2026-10-17）

- 源码阶段新增真实提交：843e621（建议契约/RED）、9b24804（后端）、986b087（前端）。此前提交保持不变，完整历史以git log为准。
- 最新完整后端147/147、原前端15/15、建议区模拟6/6通过；记录分别为advice-backend-external-final.txt、frontend-regression-with-advice.txt、advice-e2e-final-external.txt。
- 真实付费DeepSeek成功调用尚待用户私下提供运行时Key；mock不算真实成功。新增建议卡片截图展示未配置状态。
- 下文是历史Prompt与阶段状态的原记录，其中“未实现/待验收/79项”等描述保留当时语境，不代表当前状态。
- 沿用原会话编号，提示词33未收录，不据编号推断调用总数；不为补齐序号编造提示词。

## 索引（代表性阶段记录）

按 SDD / TDD / E2E 分类，指向正文「提示词 N」的全文记录：

| 类别 | 阶段 | 记录 | 意图 / 问题 / 纠偏 |
|---|---|---|---|
| SDD | 设计 | 提示词 2 | 设计复核发现三处实质缺口——Q 缺仅测 KP5 的题（32 画像不可区分）、EM 数值契约不可测、索引/真值隔离不清；锁定 24 题三份 I5+9 综合、可测 EM 契约、bit0↔KP1 |
| TDD | 算法 RED | 提示词 5 | 补强 RED，防「始终返回初始 g/s、history 平坦、converged=False」的伪实现；加一步 EM 手算 fixture 与后验边际一致性断言 |
| TDD | 算法 GREEN | 提示词 6 | 实现 `src/dina.py` 使 22 项通过；纯算法零依赖、对数域 logsumexp 稳定 |
| TDD | 后端 RED | 提示词 10 | 补强后端 RED：从 SQLite 读回 Q/X 重跑真 EM 逐题比对、X 完整 288 条、API 逐格一致，排除 seed 直接用造数真值题参 |
| TDD | 后端 GREEN | 提示词 12 | 外部 66 项 OK 后回归修复 `server.main`/HTTP 异常边界/超大 ID→400/JSON 非有限值 |
| E2E | 前端 RED | 提示词 13 | 前端 E2E 测试先行：`tests/browser_e2e.cjs`（7 组浏览器 + HTTP 静态 MIME/编码/路径穿越契约） |
| E2E | 前端 GREEN | 提示词 15 | 实现 `static/` 前端 + 题库 24 条题干修正（KP5 单技能给算术结果、KP3 不暗测 KP2） |

## 过程真实性更正

- **核心算法 / 后端 / 前端初始契约有真实测试先行**：git 历史呈现 `docs/schema → tests(RED) → feat(GREEN)`
  （如 65d020e 设计 → d03855c/b72928f 算法 RED → 38744d8 算法 GREEN；8198b90/2e72fdb 后端 RED → 5035f7f 后端 GREEN；
  3a21168 前端契约 → 758cc50 前端实现）。
- **个别 UI 回归是在 QA 修复过程中追加的回归测试，不是全程都先 RED**：提示词 16 的「旧数据归属清空」与
  「图谱节点长名外置」两处修复，实际是先改 `static/app.js`/`static/index.html`，**之后**才补 B8/B9 回归测试
  （证据 `docs/evidence/05-ui-regression-sequence.json`）。本文件不把这一局部过程美化成全程完美 TDD。

## 核心阶段提交与历史验收（保留原记录）

- 真实提交（9 个，本会话不写 `.git`，由外部编排执行）：
  `65d020e`（docs/schema）→ `d03855c`、`b72928f`（算法 RED）→ `38744d8`（算法 GREEN）→
  `8198b90`、`2e72fdb`（后端 RED）→ `5035f7f`（后端 GREEN）→ `3a21168`（前端契约 RED）→ `758cc50`（前端 GREEN）。
- 最终验证：Python 79 项 OK（`docs/validation/python-external-final.txt`）；前端 15 组通过
  （`docs/validation/frontend-external-final.txt`）；演示 EM 33 轮收敛（`docs/validation/demo-em-report.txt`）；
  桌面/390px 截图见 `docs/screenshots/`。

---

## 阶段 0：环境核验 + 需求澄清 / 设计 / 契约（进行中）

### 提示词 1（任务契约与硬性要求，全文）

> 唯一项目目录是 /private/tmp/claude-homework-t2WpwB。请先用 pwd 核对；若不同立即停止，不读取或改动任何相邻项目。
> 环境已补齐，请先重新核验真实工具链，再开始下面的设计任务。刚才已经使用 Claude Desktop 自带 CLI 成功执行 plugin install superpowers@claude-plugins-official --scope user，本次是安装后的新 Code 会话。请真实调用可用的 superpowers:brainstorming 技能；若名称不同，按真实清单识别，而不要凭空假称使用。
> 模型路由说明：本地 Claude Desktop 配置的 Gateway 是 https://api.deepseek.com/anthropic；模型别名 claude-opus-4-8 由 DeepSeek 官方 Anthropic 兼容接口映射到 deepseek-v4-pro。系统里的 Claude 名称是兼容别名，不能据此推断请求去了 Anthropic。文档请如实写出“界面 DeepSeek V4 Pro，发送兼容别名 claude-opus-4-8，DeepSeek Gateway 路由”；不要读任何 API Key，也不要声称自己读取过真实供应商内部身份。
> 请使用已启用的 Superpowers brainstorming 工作流，和我从零完成“智能化认知诊断 MVP”算法实习作业。当前文件夹是独立的新项目；不要读取或复制相邻目录的旧代码。这一轮先做需求澄清、设计和契约，不要直接实现程序。
> 作业硬性要求：使用 Claude Code + DeepSeek V4 Pro + Superpowers；SQLite 存 Q 矩阵和 X 作答矩阵；5 个知识点、至少20道题、至少10名学生；简单有向无环前置知识图谱；DINA认知诊断/参数估计，给出每名学生每个知识点的掌握概率；极简中文Web界面可切换学生，展示雷达图、概率表和知识图谱。交付完整源码、README、算法说明、PRD/架构/ER图/API契约、至少5段真实阶段Prompt（每段配1-2句说明）、1到1.5页开发过程说明；Git历史须真实体现 docs/schema → tests(RED) → feat(GREEN) → E2E。可选LLM学习建议不阻碍核心验收。
> 已确定的偏好：Python标准库+SQLite+原生HTML/CSS/JS，尽量零运行依赖；12名可复现合成学生，明确演示局限；知识点为分数概念、通分、分数加减、分数乘除、应用题。DINA采用32种掌握画像、稳定的对数后验边际估计和EM题参校准，避免把答对率冒充掌握概率；小样本固定画像先验并约束guess/slip，解释这与经典IRT的关系。图谱用来解释学习顺序，不悄悄改变潜在空间。前端清晰、可访问、适配手机，所有图表由实际诊断数据生成。
> 工作约束：仅操作当前项目文件夹；不要访问API Key、剪贴板、密钥链或打印环境变量。不要推送远程仓库、发邮件、创建付费资源。不要伪造测试、Prompt、Git历史、插件使用或人工参与记录。文档应说明实际过程为 Codex 代用户操作 Claude Desktop Code，开发由本会话中的 DeepSeek V4 Pro 与 Superpowers 完成。子代理继承当前Pro主模型，不指定sonnet/haiku。先建立需求/设计、schema和接口文档，等待我批准后再按TDD推进。每个阶段保存真实命令及结果，并将本会话实际收到的核心提示词逐步记录到 docs/PROMPT_LOG.md；未发生的阶段不要提前写成完成。
> 请先确认 Superpowers 是否实际可用并触发相应技能；若不可用，明确说明并停止实现，不能假称已使用。现在开始设计。

说明：确立任务边界（仅当前目录）、模型路由口径、交付物清单、技术偏好与 TDD 顺序；明确本轮只做需求澄清/设计/契约、不实现程序，并要求真实触发 Superpowers。

### 澄清问答（阶段 0，经 AskUserQuestion 收集，均为用户真实选择）

- **Q1 前置关系**：知识图谱中「通分」是否作为「分数乘除」的前置？
  → 用户选择 **「通分只前置加减」**（乘除仅依赖分数概念）。
- **Q2 合成学生构造**：12 名学生按什么方式构造？
  → 用户选择 **「全部沿 DAG 单调」**（前置未掌握则后继必未掌握）。

说明：这两项决定直接改变 DAG 边、Q 矩阵合法性与合成真值画像集合（见设计规格）。

### 提示词 2（对已生成设计的审查纠偏，全文）

> 余额已补足，请恢复同一项目。先修正SDD契约，本轮不要实现程序，也不要写未来阶段已完成的记录。后续回复保持简洁，避免重复回放全部需求；独立复核只聚焦下面这些问题，子代理继续继承Pro模型。
> 对已生成设计的审查发现三处实质缺口，请按以下取舍纠正并同步全部相关文档：
> 1. 当前Q没有仅测KP5的题，全未掌握与“仅掌握KP5”的画像会产生相同理想作答，无法区分全部32种画像。固定已知先验时不据此笼统断言所有题参均不可识别，但应补齐测量覆盖。锁定24题：三份I5（前15题）+9道综合题；验证32种画像的理想反应向量各不相同。KP5明确为“应用题建模/列式”，独立测量题只考数量关系或列式、给出算术结果，避免实际同时考加减乘除却把Q标成单技能。保持已选DAG和“学生真值画像全部沿DAG单调”的造数取舍；图谱仍只解释学习顺序，不裁剪32种推断画像。
> 2. 锁定可测试的EM数值契约：固定均匀先验1/32，不拟合类比例；guess和slip分别限制在[0.02,0.35]，因此guess+slip<1；初始guess=0.2、slip=0.1；E步用对数域logsumexp；M步对期望计数作精确区间截断，零有效分母时保留旧值。max_iter=200、tol=1e-8；说明具体停止准则，max_iter耗尽不能标为converged；最后似然必须以最终返回题参重算，历史包含初始及最终似然，允许小的浮点误差但不可实质下降。DDL中的CHECK同步这些边界和正向性，而非允许0/1端点。算法内核支持较小K的确定性手算测试，演示默认K=5。
> 3. 锁定索引与真值隔离：Q是题×知识点，X是学生×题；题和知识点使用稳定ID排序；位0对应KP1，掌握概率数组与KP1..KP5顺序一致；Q长表缺省关系为0，禁止空知识需求题；fit(Q,X)只接Q/X及显式数值配置，绝不读取学生profile_id。合成真值只用于生成和验证。API与设计说明应说明从SQLite读Q/X进行校准及输出后验边际，而不是用真值生成掌握概率。
> 请修改PRD、架构、API、ER、schema及Superpowers设计规格，记录这条真实纠偏Prompt与说明。补充72小时阶段计划和合成小样本的限制；验收清单不要给未发生的测试/Git历史打完成勾。修正并复核一致后初始化本地Git，先提交真实docs/schema设计提交，不推远程。最后只给出设计差异摘要、实际commit ID和下一阶段测试范围，等待我的测试阶段指令。

说明：审查指出三处实质缺口并给出锁定取舍——①补齐仅测 KP5 的题以保证 32 画像可区分；
②锁定可测试的 EM 数值契约；③锁定索引约定与真值隔离。并要求补充 72h 计划、小样本限制，
且验收清单不得给未发生阶段打勾。

### 提示词 3（git 状态更新 + 三处措辞修正，全文）

> 本地仓库已由外部编排在你同一项目 /private/tmp/claude-homework-t2WpwB 成功执行 git init；无需继续诊断 .git 沙箱限制。之后本地 add/commit 可由我执行，文档和代码仍全部由 Claude Code 生成，PROMPT_LOG 如实记载。
> 设计主体已通过复核，仅需立即保存以下三处措辞修正，不需要重新做广泛设计审查：
> 1. docs/superpowers/specs/2026-10-16-cognitive-diagnosis-mvp-design.md §6.2 把均匀画像先验写为 1/2^K（本演示 K=5 时为 1/32），保证 K=1/K=2 测试不矛盾。
> 2. §6.4 收敛判断不能仅 delta<tol。先拒绝超出浮点容差的显著负对数似然增量，再把接近零的进展判为收敛；明确 max_iter 耗尽不等于收敛，最终参数、历史末项、重算似然一致。
> 3. §6.7 “技能缺失→高slip”不正确：未全部掌握题目所需技能时，答对概率为guess，答错为1-guess；全部掌握时才由slip决定答错概率。
> 同步任何有同样问题的设计文档，记录本条实际Prompt。只修正设计文档然后简短报告，等待我的测试阶段指令。不要再尝试 .git 写入，不实现应用代码，不访问凭据。

说明：确认 git init 已由外部编排完成（本会话不再写 .git）；给出三处精确措辞修正并限定只改设计文档。

### 提示词 4（进入算法 TDD 测试阶段，全文）

> 真实设计提交已由外部编排完成：65d020e docs: define cognitive diagnosis requirements schema and contracts。请记录这一真实状态。
> 设计已获批准，进入算法 TDD 测试阶段；当前只写测试，不实现算法。先确认上一轮三处数学措辞已保存。请保持简洁，按阶段交付，不必复述需求或做长篇方案思考。
> 请真实调用 Superpowers 的 TDD 工作流，按已冻结的契约为 src/dina.py 设计有价值的 unittest 测试。必要时可用测试确定纯后验推断函数及fit函数的接口并补充接口说明，但不能先实现逻辑再反推测试。仅允许最小空包/接口桩，不允许先写DINA实现。
> 至少覆盖：K=1、guess=.2/slip=.1、均匀先验下，单题答对掌握后验9/11、答错1/9；多技能AND条件；知识边际概率而非MAP画像；画像位序与Q列对齐；后验归一化；长题列对数稳定性；非法Q/X及形状；不修改输入；EM似然在浮点容差内不下降；最终返回题参、历史末项和重算似然一致；约束边界；固定先验；max_iter耗尽不冒充收敛；确定性与适当的行/列置换不变性。测试不要求12名演示学生能精确恢复真实题参，也不要断言所有后验都极端接近0/1。
> 实际运行测试得到RED，并将原始命令、退出码和输出保存到docs/validation/algorithm-red.txt。RED应来自待实现接口/行为，而不是语法错误或缺少第三方依赖。记录这条真实Prompt及1-2句意图说明。由于Claude沙箱限制.git写入，完成测试后由外部编排创建真实test提交，你不要重复诊断或尝试绕过限制。不要修改数学断言来让未来实现更容易，不推远程。
> 完成后只报告测试范围、真实失败原因和commit ID，等待我的算法实现指令。

说明：批准设计、进入算法 TDD；要求真实调用 TDD 工作流、按冻结契约写测试并跑出 RED，RED 须来自未实现行为；.git 写入仍由外部编排。

### 提示词 5（补强 RED：防伪实现的两组数学检查，全文）

> 暂停上一条实现任务：接口仍是空桩。独立复核发现当前fit测试可被“始终返回初始g/s、history=[初始LL,初始LL]、converged=False”伪实现通过。先补强RED，只增加以下两组核心数学检查，不重做设计或其他测试：
> 1. 一个独立手算的一步EM fixture，明确期望计数及区间截断后题参，并断言max_iter=1实际更新参数且LL严格提高。可以用K=1、Q=[[1]]、X=[[1],[1],[1],[0]]：初始g=.2 s=.1；三次答对时掌握后验9/11，一次答错1/9；M步g=(3*2/11)/(3*2/11+8/9)=27/71，截断为.35；s=(1/9)/(3*9/11+1/9)=11/254。手算请核对后固化断言，不调用待实现fit作为预期值。初始LL=3log(.55)+log(.45)，一步应严格提高。
> 2. 返回FitResult.posterior_marginal必须与最终返回g/s重新调用posterior_marginal(Q,X,g,s)得到的概率逐项一致。
> 实际运行全部测试得到RED，保留原algorithm-red.txt，另存docs/validation/algorithm-red-strengthened.txt（命令/退出码/原始输出），记录此真实纠偏Prompt。只补测试，不实现算法；等待补强测试提交后继续实现。不要写.git，回复简短。

说明：防止「始终返回初始 g/s、history 平坦、converged=False」的伪实现通过 fit 测试；新增一步 EM 手算 fixture 与「后验边际须与最终题参重算逐项一致」两处硬断言。

### 提示词 6（实现 src/dina.py 使测试通过，全文）

> 真实RED测试提交已完成：d03855c test: specify DINA posterior and EM behavior in red（由外部编排提交）。请记录。
> 算法测试已完成真实RED并获批准，现在实现 src/dina.py 使现有测试通过。请真实应用 Superpowers TDD 工作流，先阅读现有测试和数值契约，按RED→GREEN→必要重构执行，不重新做需求分析。
> 仅实现纯算法：画像枚举bit0=KP1、Q多技能AND、固定均匀先验1/2^K、对数域归一化及边际、约束EM题参校准、验证输入、确定性。保持题参[.02,.35]，零有效分母保留旧值，负似然异常不判收敛，max_iter耗尽返回False，最终题参/后验/似然一致。不得为了通过测试删除/减弱手算断言或其他有效测试；若发现测试本身有数学错误先简短说明，不悄悄改。
> 真实运行全部算法unittest并保存命令/退出码/原始输出至docs/validation/algorithm-green.txt。补充必要算法接口说明、记录本条真实Prompt及1-2句意图，创建.gitignore排除.claude、缓存、生成DB、运行日志、系统文件。不要读凭据，不推远程，不尝试.git写入；完成后由外部编排创建真实feat提交。不要开始数据库/HTTP/前端。本阶段完成后报告测试总数和结果，等待后端阶段指令。

说明：批准进入 GREEN，实现纯算法使 22 个测试通过；限定只做算法、不改弱测试、不写 .git，并补齐 .gitignore 与接口说明。

### 提示词 7（fit 收敛异常须抛 ArithmeticError，全文）

> 22项测试已通过，核心公式独立复核通过。仅修复一个冻结契约缺口：src/dina.py的fit在delta < -1e-9时目前仍继续迭代，必须先抛ArithmeticError（说明EM似然显著下降），再判收敛，不能静默继续或伪称收敛。请加这一最小判断，不重构其它内容；复跑22项并更新algorithm-green.txt，记录本条真实Prompt。补记已存在的补强RED提交 b72928f。不要写.git，完成简短报告后等待后端阶段指令。

说明：冻结契约要求「显著负对数似然增量」先报错而非静默继续；本修复在 fit 内对 delta < -1e-9 抛 ArithmeticError，再判收敛。

### 提示词 8（进入后端 SQLite/seed/HTTP 的 TDD RED 阶段，全文）

> 这是同一作业的后端阶段新Code会话。唯一项目目录 /private/tmp/claude-homework-t2WpwB，请先pwd核对，只读写此项目，不读取或复制相邻项目。模型路由为界面DeepSeek V4 Pro、兼容别名claude-opus-4-8、DeepSeek Gateway；子代理继承Pro，不指定sonnet/haiku。官方Superpowers 7已安装启用，请真实加载test-driven-development，不重做已批准的brainstorming设计。不要读取API Key、剪贴板、密钥链、环境变量，不推送远程/发邮件/付费。文档如实写Codex代用户操作Claude Desktop Code。已有真实本地历史：65d020e设计、d03855c及b72928f算法RED、38744d8算法GREEN（22项通过）。.git写入受Claude沙箱限制，提交由外部编排执行，你无需尝试。先读docs/ARCHITECTURE.md、API_CONTRACT.md、schema.sql及必要设计部分，在现有代码上继续；不要覆盖PROMPT_LOG已有内容，只追加实际收到的Prompt及意图。
> 算法阶段已通过。现在进入SQLite/seed/HTTP的TDD RED阶段，只写契约澄清、测试和最小接口桩，不实现服务。继续Superpowers工作流，直接产出，不重复需求分析。所有文件仍只在 /private/tmp/claude-homework-t2WpwB；不读取相邻项目/凭据、不写.git、不推远程。
> 先在API/架构文档补清这些常规边界：Content-Type JSON只用于API，HTML/CSS/JS各自MIME；非GET API返回405 METHOD_NOT_ALLOWED；未知数字学生ID返回404，非正整数ID返回400；diagnosis.matrix为按student_id/kp_id升序的60行长表；correct_rate逐知识点以Q=1题目为分母，综合题计入每个涉及KP；JSON保留有限浮点数，不必截成展示百分比；seed默认拒绝覆盖已有库，可通过显式--force重建（测试临时库）；缺DB服务启动失败，不隐式建库。src/seed.py、server.py既支持python3 -m src.seed/server，也支持README所述直接脚本启动。服务默认127.0.0.1，测试支持临时DB/端口0，运行零依赖。
> 编写有价值的stdlib unittest：schema约束/FK/二元X/题参边界；确定性seed的5知识点24题12学生，Q=三份I5+9综合、画像理想反应32种互异、真值沿DAG但fit仅收Q/X；从SQLite按稳定ID读回Q/X与造数一致、diagnosis60条与用保存题参重算的边际一致；DAG无环；真实HTTP验证6个GET接口、数组排序/计数/概率范围、correct_rate重算、无profile_id、两名学生数据不同、GET前后DB hash不变、404/400/405、缺DB不建库。以临时文件fixture避免破坏任何已有库。静态资源MIME与路径穿越检查可在前端阶段加入，此轮不强迫不存在的页面变绿。
> 测试先于实现，运行得到真实RED（来自未实现行为，不是语法/第三方依赖问题），保存命令/退出码/原始输出到docs/validation/backend-red.txt。记录本条真实Prompt及意图。不要减弱已通过的算法测试；不要提前生成实现。完成后简报测试范围与真实失败原因，等待后端实现指令；由外部编排提交test历史。

说明：批准进入后端 SQLite/seed/HTTP 的 TDD 测试阶段；先补清 API/架构的常规边界（MIME/405/404/400/60 行长表/correct_rate 分母/浮点/seed 覆盖/缺库启动/双入口），再写 schema/seed/HTTP 测试与最小接口桩并跑出真实 RED；.git 写入仍由外部编排。

### 提示词 9（思考强度控件异常中断后的续跑指令，全文）

> 继续刚才因思考强度控件异常被中断的后端RED阶段；现在已恢复到已验证的Medium。你已经读完设计/代码并开始澄清架构文档，不需要重复读取或重新分析方案。按上一条任务直接完成：补清API边界，创建db/data_gen/seed/server最小空桩及有价值的SQLite/seed/真实HTTP unittest；不实现逻辑；运行得到真实RED，保存命令、退出码、完整输出于docs/validation/backend-red.txt；追加真实Prompt和说明。保持已有22项算法测试，不写.git。用中文简短报告，等待后端实现指令。

说明：思考强度控件异常中断后的续跑指令——确认已恢复 Medium、无需重读方案，直接完成后端 RED 阶段并如实记录。

### 提示词 10（补强后端 RED：三项核心数据链验证，全文）

> 后端RED已由外部编排真实提交为8198b90。只读复核未发现数学错误，但需补3项核心数据链验证，先补测试保持RED，不实现逻辑、不重复方案分析：
> 1. tests/test_seed.py用从SQLite读取的Q/X按冻结默认配置重新调用dina.fit，逐题比对落库guess/slip及diagnosis。已有“用保存g/s重算后验”不能排除seed直接使用造数真值题参，因此保留并新增真EM校准断言。
> 2. tests/test_api.py将mastery、diagnosis按student_id/kp_id逐格对照SQLite；items逐题对照SQLite展开的Q与g/s。仅范围/排序检查不能证明来自库，补数值一致性。
> 3. seed的X必须有12*24=288条完整(student_id,question_id)记录；缺失不能当作0掩盖。新增COUNT和完整pair集合断言。
> 实际运行全套测试仍RED，保留原backend-red.txt，另存docs/validation/backend-red-strengthened.txt（命令/退出码/原始输出）；记录此Prompt。不要改有效的算法断言，不写.git。完成后等待后端实现指令。

说明：确认 RED 提交 8198b90 无数学错误，要求补 3 项核心数据链验证——① 从 SQLite 读 Q/X 重跑真 EM 逐题比对落库题参与 diagnosis，排除 seed 直接用造数真值题参；② API 的 mastery/diagnosis/items 与 SQLite 逐格数值一致；③ X 必须 288 条完整记录、缺失不得当 0。

### 提示词 11（进入后端 GREEN：实现 SQLite/造数/seed/HTTP，全文）

> 后端测试已真实RED并提交，现在按Superpowers TDD实现SQLite/造数/seed/HTTP，保持现有测试有效。请直接实现，不再做需求脑暴或扩大范围。应用仍零运行依赖，仅Python标准库和SQLite，所有文件在当前项目。
> 按已冻结schema/API与测试实现src/db.py、data_gen.py、seed.py、server.py。24题=三份I5+9综合题，KP5单技能题只考数量关系/列式并给出算术结果；12名合成真值保持已选DAG单调。seed确定性、拒绝默认覆盖、--force明确重建；fit只接Q/X，不读真值；以EM最终g/s与后验写入SQLite，保留校准历史与收敛状态的可核验本地报告。HTTP连接mode=ro，6个JSON GET接口、稳定排序、相关题答对率独立重算、错误处理、127.0.0.1监听、正确JSON编码；实现静态安全路由以便下一轮接页面，但本轮不写前端。
> 运行全部Python unittest，使算法与后端一起GREEN；保存命令/退出码/原始输出到docs/validation/backend-green.txt。若发现测试实际错误先说明依据，不为通过而删减断言。更新简短算法文档docs/ALGORITHM.md（公式、EM约束、数据局限、实际验证）与PROMPT_LOG。本轮不写.git，由外部编排提交。结束只报告真实测试数和结果，等待前端/E2E阶段指令。

说明：批准进入后端 GREEN——按冻结 schema/API 与测试实现 db/data_gen/seed/server；seed 只写 EM 最终 g/s 与后验、保留可核验本地报告；HTTP 只读连接、6 个 JSON GET、独立重算答对率、静态安全路由；本轮不写前端。

### 提示词 12（外部验收结果 + 两组契约缺口的回归修复，全文）

> 外部编排已在沙箱外原样运行你的全套测试，真实结果：Ran66tests in2.604s、OK、EXIT_CODE=0。完整输出已复制到当前项目docs/validation/backend-external-initial.txt。请如实记录：不是通过修改Claude沙箱设置，而是Codex在已授权的外部验收环境运行同一脚本；无需你开启allowLocalBinding或再诊断端口权限。
> 提交前独立代码复核发现两组真实契约缺口，请按TDD先补必要测试得到RED再修复，不重做方案：
> 1. server.main默认用DEFAULT_DB_PATH但未定义；seed/server顶端from src在直接脚本运行时失败。两者应支持-m和直接脚本启动，定义与seed一致的默认DB路径；用argparse给清晰--help及参数说明，保留已支持位置DB路径、端口、--force的可用性，README稍后与实际一致。增加真实subprocess --help/临时DB启动验证，不能只测make_server而漏main。
> 2. HTTP请求边界缺少except，连接/查询异常会断连接，不返回500 INTERNAL JSON。把建连接也纳入异常边界，可靠关闭连接；服务错误返回安全中文JSON，不泄漏堆栈/路径。超大正整数字符串ID应按契约返回400（在API文档补整数存储范围），不触发sqlite OverflowError/断开。JSON按契约拒绝非有限值，HTTP/1.1契约应与protocol_version一致。添加最小边界回归测试。
> 保存新增回归的真实RED与修复后结果，保留原始backend-green.txt失败记录并注明其为Claude沙箱内结果。你仍可跑非HTTP检查；HTTP受限准确注明，外部编排将重跑全套。更新PROMPT_LOG，补记后端补强测试提交2e72fdb。不要写.git，不写前端。简短报告完成内容后等待前端/E2E阶段指令。

说明：告知外部编排已在沙箱外原样跑出 66 项 OK（非改沙箱设置），并要求按 TDD 修复两组契约缺口——① server.main 缺 DEFAULT_DB_PATH、直接脚本 `from src` 导入失败，改用 argparse 并补 subprocess 验证；② HTTP 请求边界缺异常处理/500 JSON、超大 ID 触发 sqlite OverflowError、非有限 JSON、HTTP/1.1 协议版本，补最小边界回归测试。

### 提示词 13（进入前端/E2E 测试先行阶段，全文）

> 这是同一作业的前端/E2E新会话。唯一目录/private/tmp/claude-homework-t2WpwB，先pwd核对，仅操作此项目，不读取相邻旧代码、API Key/剪贴板/密钥链，不打印环境变量，不推远程/邮件/付费。界面DeepSeek V4 Pro、兼容别名claude-opus-4-8经DeepSeek Gateway；子代理继承Pro。请真实加载已启用Superpowers test-driven-development，不重做已批准设计；所有应用实现和测试继续由Claude Code生成，Codex代操作/本地Git/外部QA，PROMPT_LOG只追加实际提示词。已有后端提交5035f7f，外部完整测试78项OK，证据docs/validation/backend-external-green.txt。先读必要的PRD/API契约与server静态路由，按需调用已有API。
> Python算法/后端已GREEN，现在进入浏览器E2E的测试先行阶段。只创建测试和前端验收说明，不写页面实现，不扩大业务范围。继续真实Superpowers TDD工作流。
> 已验证本机QA环境：Node /Users/jiangdeliang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node；playwright模块在 /Users/jiangdeliang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules；浏览器缓存 /Users/jiangdeliang/Documents/Codex/2026-10-15/files-mentioned-by-the-user-codex/work/pw-browsers；Chromium151已由外部编排成功启动。测试使用Node自带assert + require('playwright')，无需@playwright/test。脚本不要硬编码我的机器路径；通过NODE_PATH、PLAYWRIGHT_BROWSERS_PATH和E2E_BASE_URL等显式变量配置。可添加仅开发依赖的package.json，但应用运行仍零依赖。Claude沙箱若阻止浏览器的macOS进程注册，不要反复尝试突破；交给外部编排运行同一个测试并回填真实输出。
> 目标前端：中文认知诊断仪表盘；12人切换；当前学生雷达/5行概率对照表/5节点5边前置图；另展示全体12×5概率表以明确满足矩阵展现。图谱箭头前置→后续，节点同时显示名称/百分比，数据来自6个真实GET接口；合成小样本提示；相关题答对率明确仅作对照；可访问语义、可见焦点、中文加载/错误/重试；390px无页面横向溢出。不得把算法或内部实现细节塞满主要操作界面。
> 编写约7组有价值的真实浏览器检查：首屏加载/12名学生；所选学生数值与API逐项一致、SVG图形数据取自该学生；切换及快速切换无旧请求覆盖；图谱5节点5箭头正确；全体12×5表/API不泄露profile_id；模拟网络失败显示中文错误与重试并能恢复；手机布局与键盘选择。捕获未处理JS错误并失败。另补HTTP静态MIME/编码路径穿越测试。选择稳定语义或data-testid契约，不用脆弱坐标。可在首次E2E失败时截屏供诊断。
> 请写tests/browser_e2e.cjs并明确如何启动/关闭测试服务、返回非零失败码。先实际跑HTTP静态测试和可运行的E2E得到RED，保存docs/validation/frontend-red.txt和真实结果；若沙箱阻止浏览器，报告准确原因等待外部运行，不伪称页面验收成功。记录本条Prompt和意图。不写.git，完成后等待前端实现指令。

说明：批准进入浏览器 E2E 测试先行阶段；只写测试与前端验收说明、不写页面；用 Node assert + require('playwright') 写约 7 组浏览器检查 + HTTP 静态 MIME/编码/路径穿越测试，跑出真实 RED 并保存 frontend-red.txt。

### 提示词 14（余额恢复 + 独立复核发现的 7 组 E2E 测试缺陷纠偏，全文）

> 余额已恢复，继续同一项目。上轮tests/browser_e2e.cjs已写入后遇到402；网页仍未实现。外部编排已跑--http-only得到真实RED，记录在docs/validation/frontend-red-http-external.txt。先修复独立复核发现的E2E测试自身问题，不写页面，不重新分析需求，不重复环境核验：
> 1. B1 attached后立即数options有竞态。等待12个有效选项/可用选择器；B2/B4/B5/B7等待真实数据行/节点/数值完整后再断言。
> 2. B6主动route.abort会产生预期console.error net::ERR_FAILED，不能与未处理JS错误混为一谈。保留pageerror零容忍，只豁免被注入明确URL对应的预期网络错误。
> 3. 重试等待错误态不可见，而非必须DOM移除；同时等待学生3实际诊断数值更新。
> 4. 加载态检查不能用空catch吞掉断言。用可释放请求屏障固定加载状态，验证中文加载提示后释放。
> 5. B3竞态用确定时序：确认旧请求已发出/被拦截→切新学生→等新数据→释放旧请求→再次验证名称/表格/雷达/图谱，正确处理AbortController取消，不靠800/1200ms固定睡眠。
> 6. 雷达不能只查data-values，校验实际polygon/path几何随API值变化（可冻结data-testid=radar-polygon、data-center/data-radius等可核验几何契约）；marker-end须引用存在的marker；SVG <g>文本用textContent。
> 7. 全体矩阵验证60个唯一(student_id,kp_id)集合；手机检查5节点完整可见，键盘切换后等实际学生12数值。名称优先来自真实API避免硬编码不必要误杀。
> 记录上轮实际Prompt与本条纠偏意图，创建必要package.json只含QA devDependency playwright1.62.1，应用零运行依赖。测试脚本的环境变量仅明确读取自己的E2E配置，不打印或读取其它环境/凭据。更新前端契约文档。脚本语法检查和HTTP-only可跑，浏览器/端口若沙箱阻止交给外部编排。不要写.git，完成后等待前端实现指令。

说明：告知余额恢复并已由外部编排跑出 --http-only 真实 RED（frontend-red-http-external.txt）；给出 7 组对 E2E 测试自身的纠偏（竞态等待、注入网络错误豁免、重试等待、加载态请求屏障、B3 确定时序与 AbortController、雷达几何与 marker 引用、60 唯一对/手机完整可见/名称取自 API），并要求创建 package.json（playwright 1.62.1）、前端契约文档、更新 PROMPT_LOG、语法检查与 HTTP-only 可跑。

### 提示词 15（实现前端 static/ 与题库题干修正，全文）

> 浏览器/静态测试已真实RED并提交，现在实现static/index.html、style.css、app.js让E2E通过。继续Superpowers TDD，基于现有契约与测试直接实现，不扩展后端或加入LLM密钥。所有应用文件由你生成，不读取相邻旧项目。
> 做一个完整清晰的中文"学生认知诊断"界面：浅灰底、深靛蓝强调色、白色卡片、充足间距，系统中文字体，适配桌面和390px。顶部清晰标题/合成样本提示/12名学生选择；核心是雷达+掌握概率/相关题答对率对照表和前置知识图谱；另有全体12×5掌握概率矩阵，突出当前学生、移动端表格容器内滚动；简短可展开模型说明。不用CDN/外部字体/假数据。UI以展示学生诊断为主，不要展示开发过程、测试次数、接口路径等内部细节。
> 雷达和知识图谱都用真实SVG与当前API数据，知识图谱5节点5箭头，节点有名称+百分比，明确箭头"前置→后续"；不能仅以颜色传达状态。概率用百分比展示，答对率明确仅作对照。加载/错误/重试都中文且有status/alert语义；快速切换用AbortController或请求序号防旧结果覆盖；请求失败不能把旧学生数据当作当前显示；可见键盘焦点、关联label、图表文本替代。遵循已建立的E2E定位契约，不删除或减弱有价值的测试。
> 另有一个与已批准测量设计直接相关的题库质量修正：当前seed._question_stems重复输出类型短语，且_KP_TASK[5]写"列式并求算术结果"，与仅测KP5契约冲突。请把24题改成24条不同的简短中文合成题干，逐条与冻结Q对应；单技能KP5三题只判断数量关系/列式并给出算术结果，不要求再算加减乘除。单技能KP3题如需通分结果应直接给出，避免暗测KP2；综合题需体现对应的多个需求。数据规模、Q、X生成和数值估计逻辑保持冻结。此处是演示题干，不添加答题/自动评分功能；文档明确合成示例。
> 跑全部Python测试和真实浏览器E2E；若Claude沙箱阻止浏览器，准确报告并交由外部编排运行你写的脚本，不反复突破，也不伪称测试成功。保存真实命令/退出码/结果和桌面/手机截图位置；更新PROMPT_LOG，未通过项不得打勾。不要写.git、不推送。完成后简报，等待最终QA和交付文档指令。

说明：批准进入前端 GREEN——按已冻结契约实现 static/index.html、style.css、app.js 使 E2E 通过，并做题库题干质量修正（24 条互不相同、KP5 单技能给出算术结果、KP3 单技能不暗测 KP2）；按 TDD 先补题干测试再实现；跑全部 Python 测试与真实浏览器 E2E（沙箱限制部分交由外部编排）。

### 提示词 16（外部浏览器验收反馈 + 独立 UI 复核纠偏，全文）

> 外部真实浏览器验收已运行，结果12/13通过，唯一测试失败是B7：macOS Chromium下对select按End没有选中学生12。完整输出在docs/validation/frontend-external-initial.txt。请保留有效测试，不用selectOption替代键盘断言；为select显式处理Home/End（设置首/末选项并触发同一change加载逻辑），保持方向键/原生可访问性。
> 独立UI复核另有两项实际问题需要先补最小回归测试再修：
> 1. loadStudentDetail开始时仍显示上一学生的雷达/概率表/图谱；新学生失败后标题写新学生加载失败，图表却留旧值，归属错误。请求开始立即清空或隐藏旧的三块当前诊断，清旧错误，显示中文加载态；成功后才显示新数据；失败持续隐藏。仅当前请求能结束loading，旧请求Abort不能覆盖新请求状态。已加载的学生select应保持可切换（B3仍可并发切换），全体矩阵可以保留且每行标名正确。
> 2. 图谱KP5的白色完整长名称画在直径60的圆内，文字超圆后在白底不可读。把节点名称用深色放在圆外或分行，圆内只放百分比；完整名称在节点可见文本/可访问文本中保留，避免缩小字到不可读。雷达你已扩大viewBox并缩短标签，不要重复改未有问题处；截图确认桌面/390px长字均完整、无裁切。
> "关于本模型"补一段已约定的简短说明：固定均匀先验；推断保留32画像；DAG单调只用于造数；guess/slip[.02,.35]；独立Bernoulli合成噪声与小样本局限。放折叠说明中，不堆到主流程。
> 真实按RED→修复执行，保存必要回归输出和Prompt意图。浏览器/端口受沙箱阻止时不要反复尝试，由外部编排重跑。已存在前端测试提交3a21168，记录实际状态，不写.git。完成后用中文简短报告，等待最终QA和交付文档指令。

说明：告知外部浏览器验收 12/13（仅 B7 失败于 macOS Chromium 原生 select 不响应 End），并给出独立 UI 复核的两项问题（①切换/失败时旧诊断未清空导致归属错误；②图谱 KP5 白色长名溢出圆不可读），要求先补最小回归测试再修复（实际执行为先改实现、再追加 B8/B9 回归，见「过程真实性更正」），并补「关于本模型」约定说明；记录前端测试提交 3a21168。

### 提示词 17（基于实际桌面/390px 截图的两处小型可读性修正，全文）

> 补充来自实际桌面/390px截图的两个小型可读性修正（只调渲染/CSS，不改变数值、Q/X、接口或测试断言，不需要为低影响样式写镜像测试）：
> 1. 雷达标签与百分比目前分别放在R+26、R*prob+15处；概率接近1时同一轴上两段文字重叠。请把每轴名称和百分比作为固定外侧的两行排在一起，例如名称基线-5、百分比基线+11，留足viewBox边距，名称/数值约12/11px，不再随概率顶点位置放百分比。多边形顶点仍R*prob，几何契约不变。
> 2. 手机全体矩阵首列被压到"学/生/05"多行，行高异常。给学生首列white-space:nowrap与合理最小宽度（约80–90px），表格仍只在自身容器内横向滚动，页面无溢出。可使首列粘附但不是必需；不要缩小字体。
> 此前09b的旧数据归属、节点长名称和模型说明修复继续保留。不要因此扩大布局或加新功能。外部编排将统一重跑13组浏览器与全部Python测试。记录本条实际Prompt及意图，完成后等待最终QA和交付文档指令，不写.git。

说明：基于实际桌面/390px 截图的两处低影响样式修正——① 雷达每轴名称与百分比改为固定外侧两行（名称基线 R+21、百分比基线 R+37，约 12/11px，百分比不再随概率顶点定位），多边形顶点仍 R×prob、几何契约不变；② 手机全体矩阵首列加 `white-space:nowrap` 与 `min-width:90px`，避免「学/生/05」多行，表格仍在容器内滚动。不改数值/Q/X/接口/测试断言，不写镜像测试。

### 提示词 18（外部 79/15 全绿后，截图复查发现两处样式未生效的精确修正，全文）

> 外部真实验收现在79项Python通过、15组前端通过，记录分别为docs/validation/python-external-final.txt、frontend-external-final.txt。但截图复查发现09c的两个样式修正尚未真正生效，原因已确定，只需下面两个精确最小修正，不再分析方案，不写新测试，不改任何数值/多边形几何/数据契约：
> 1. index.html全体矩阵table只有data-testid，没有id；style.css的#all-students-table所有规则因此无效。给该table添加id="all-students-table"，保持data-testid，现有nowrap/min-width90等CSS即可生效。
> 2. 雷达现在namePt=vertex(k,R+21)、valPt=vertex(k,R+37)，这仍是沿半径错位，在左右轴上文字仍重叠。请改为每轴共用一个外侧锚点lp=vertex(k,R+32)，名称和百分比用完全相同的x=lp[0]；名称y=lp[1]-5，百分比y=lp[1]+11（固定垂直16px两行），字体12/11，text-anchor middle。不是两个不同半径的点。保持340viewBox、R/cx/cy、valuePts不变。
> 记录此Prompt/实际79与15通过结果和意图，语法检查即可，截图和浏览器复核由外部编排做。不要派子代理/重做需求/TDD，不写.git。完成后等待交付文档指令。

说明：外部真实验收 79 项 Python、15 组前端全绿；截图复查确认上一轮两处样式修正未真正生效的根因——① 全体矩阵 `<table>` 只有 `data-testid` 没有 `id`，使 `#all-students-table` 的 CSS 全部无效；② 雷达名称/百分比仍是两个不同半径的错位点，左右轴仍重叠。按最小修正：给 table 补 `id`；雷达每轴共用同一锚点 `lp=vertex(k,R+32)`，名称 `y=lp.y-5`、百分比 `y=lp.y+11`（相同 x、middle、12/11px）。不改数值/多边形几何/数据契约，不写新测试。

### 提示词 19（最终 QA 完成，进入交付文档阶段，全文）

> 最终桌面和390px截图已人工查看通过，文件为docs/screenshots/desktop.png与mobile.png，可用于README演示。
> 最终实测已就绪：79项Python unittest全部通过（docs/validation/python-external-final.txt）；15组前端验收全部通过（6组HTTP+9组浏览器，frontend-external-final.txt；最终样式修正后已复跑并更新同一记录）。演示EM报告demo-em-report.txt显示33轮收敛。安全工具链证据已由外部编排提取到docs/evidence/，仅包含脱敏配置确认、插件安装/真实Skill调用、UI回归修改顺序元数据；不要访问原始诊断包/用户配置/转录。接下来本轮只做文档，不派子代理、不重演设计/TDD、不重读整个长Prompt日志；范围读必要部分后直接完成。
> 最终QA已完成，准备交付文档。请只依据当前项目、真实Git历史和docs/validation的实际结果完成最终文档，不编造未发生的步骤、测试、LLM调用或人工工作。应用实现不再扩大范围。
> 1. README.md：中文，5知识点24题12学生，演示流程、Python版本/零运行依赖、实际可运行的建库/服务启动/端口/--force命令、Python测试与可选Node浏览器测试步骤；依赖区分运行和仅QA；说明合成小样本/固定先验/题参边界/已知限制/LLM建议加分项未实现；不要要求应用API Key。GitHub/Gitee同步按用户要求暂缓，本地源码/真实历史已就绪，不写虚构仓库链接或声称已提交邮件。
> 2. docs/TOOLCHAIN.md：如实写Claude Desktop Code+界面DeepSeek V4 Pro+兼容别名claude-opus-4-8+DeepSeek Gateway路由+Superpowers7实际Skill调用；Codex代操作、编排本地Git与外部QA；代码/测试由Claude本会话生成，Git写入和本地端口/浏览器限制由外部验收处理，非伪装成Claude沙箱内运行。引用项目内现有脱敏证据，不读取凭据、原始诊断包或完整转录。
> 3. PROMPT_LOG：保留已有真实记录，新增最终Prompt及意图；加一个按SDD/TDD/E2E分类的代表性5–8条索引，指向实际全文记录，每条1–2句解释意图/问题/如何纠偏。不得把未发送草稿当成实际Prompt，也不要覆盖/删掉失败历史。补录真实提交与验证结果，不虚构时间。过程真实性更正：docs/evidence/05-ui-regression-sequence.json显示09b阶段先修改static/app.js再补B8/B9回归，不能写成所有UI纠偏都先RED。请纠正PROMPT_LOG中对应“先补回归再修”等不符实际的说明（保留真实Prompt原文），说明核心算法/后端与前端初始契约有真实测试先行，个别UI回归在QA修复过程中追加。不要把这一局部过程美化成全程完美TDD。
> 4. docs/DEVELOPMENT.md：正文约1400–1700汉字，便于排成1–1.5页。写业务→技术拆解，2–3个真实协同问题（Q缺KP5测量覆盖、弱测试允许不执行EM的伪实现、Claude Git/HTTP沙箱和外部验证等），如何定位与纠偏，以及对算法工程与AI提效的理解。保持中立真实分工，不冒称提交者手写/手测过哪些工作，不要写空泛赞美。
> 5. 算法说明需贴合实际实现：E步在对数域归一化，_marginalize对已归一化的画像后验概率求和得到边际，不声称该函数又执行logsumexp；先验影响短题列后验，不笼统保证“极端后验一定偏保守”。同步设计规格中的同类措辞。同步PRD已发生阶段状态和72小时时间盒（这是计划，不编造收到作业的准确时刻）；更新算法说明的真实演示校准结果与小样本局限。尚未实现/未验证的项如实标注。交付检查表链接全部必要文件。
> 6. 文档图：ARCHITECTURE应有Mermaid flowchart（当前只有ASCII）；ER.md的PK_FK不是官方键语法，改为逗号分隔的PK, FK。官方依据：https://mermaid.js.org/syntax/entityRelationshipDiagram.html#attribute-keys-and-comments 。确保图与8张表/真实调用流一致，避免用新功能扩需求。
> 7. 准备提交邮件草稿docs/SUBMISSION_DRAFT.md（含姓名/仓库链接待填写，不编造），仅草稿、不发送、不推远程。所有Markdown链接可移植，不依赖当前机器绝对路径。
> 完成后只报告交付清单及真实仍待事项。不写.git；外部编排会排版开发说明PDF、做最终打包和清洁环境冒烟验收。

说明：最终 QA 已就绪（79 项 Python + 15 组前端全绿、桌面/390px 截图由 Codex 查看通过、EM 33 轮收敛），本轮只做交付文档（README/TOOLCHAIN/DEVELOPMENT/SUBMISSION_DRAFT、PROMPT_LOG 索引与真实性更正、算法说明与设计规格措辞对齐、ARCHITECTURE Mermaid、ER 键语法、PRD 状态与 72h 时间盒）；依据真实 git 历史与 docs/validation 结果，不编造未发生步骤；GitHub/Gitee 同步暂缓、不写虚构链接、不推远程。

### 提示词 20（独立最终复核的精确文档修正，全文）

> 用户明确要求最高思考，当前Claude界面已核实Max，请保持Max，不切中等。继续同一项目/private/tmp/claude-homework-t2WpwB，本轮只修最终文档/忽略规则，不改业务实现，不调用子模型或新建广泛审查，不读凭据，不写.git，不推送/邮件。
> 独立最终复核只有以下精确修正：
> 1. docs/DEVELOPMENT.md末段"需求、审查与纠偏决策由提交者用户给出"不准确。用户提出/授权任务并确认需求取舍；Codex及审查代理负责技术拆解、独立复核、纠偏提示与操作编排；Claude Code会话中配置的DeepSeek模型生成代码/测试/文档。不要把Codex做的技术审查归到用户。截图实际由Codex查看，不写"人工查看"。docs/PROMPT_LOG.md约264行"用户补足余额并直接给出审查意见"改为"用户补足余额，Codex转达独立审查意见"，保留真实Prompt原文及真实的DAG选择记录。
> 2. DEVELOPMENT末尾"不声称任何AI调用到达某个真实供应商"过度泛化，与配置路由证据口径不一致。改为说明：模型路由依据已验证配置与DeepSeek官方兼容别名映射，模型自称本身不作为独立身份证明。TOOLCHAIN的"开发端Claude本会话模型"明确指Claude Code中配置的DeepSeek模型，避免误指Anthropic模型。
> 3. README补在项目根目录操作，Python测试标题改"Python测试（标准库）"，不是"运行必需"。仅QA需Node>=20（包engines已核实），实测Node24.19.0；先npm install，再npx playwright install chromium，然后给现有E2E命令。应用运行仍不需要Node、模型API Key或第三方库。交付表中的主要文档用可移植相对Markdown链接；开发过程说明同时链接docs/DEVELOPMENT.md与即将由外部编排排版的docs/DEVELOPMENT.pdf。
> 4. docs/PRD.md约84行仍有"极端后验偏保守"保证，改为短题列受先验影响、不拟合类比例，与ALGORITHM一致。
> 5. .gitignore补*.db.report.txt，忽略默认建库生成的运行报告，不能忽略docs/validation下的历史txt证据。
> 记录本条真实Prompt与意图；不夸大为全程Max，之前已发生阶段保持历史记录。篇幅保持可排1–1.5页。完成后简短报告，等待外部编排生成PDF、提交文档、打包和清洁目录启动验收。

说明：独立最终复核给出 5 项精确文档/规则修正——① 分工表述（技术审查归 Codex 及审查代理而非用户；截图由 Codex 查看；PROMPT_LOG 改「Codex 转达独立审查意见」，保留真实 Prompt 与 DAG 取舍记录）；② 路由口径（「不声称到达真实供应商」改为「路由依据已验证配置与 DeepSeek 官方兼容别名映射，模型自称不作为独立身份证明」，TOOLCHAIN 明确开发端是 Claude Code 中配置的 DeepSeek 模型）；③ README 根目录操作说明、Python 测试标题、QA 的 Node ≥20 与安装步骤、交付表可移植相对链接 + DEVELOPMENT.pdf；④ PRD 先验措辞与 ALGORITHM 一致；⑤ .gitignore 补 `*.db.report.txt`。本轮按要求保持 Max 思考，但**不夸大为全程 Max**——此前各阶段按其当时的历史记录（如提示词 9 记录的 Medium 恢复）如实保留。

### 提示词 21（最后一处非引文事实归属修正，全文）

> 最后一处只改非引文中的事实归属：docs/PROMPT_LOG.md 第254行附近"截图人工通过"应改为"截图由 Codex 查看通过"。独立复核已确认其余最终修正均到位。不要改原始历史 Prompt 引文，不修改业务代码/测试，不操作 Git/推送/邮件；如实记录本提示。继续保持 Max。完成后简短告知。

说明：独立复核确认其余最终修正均到位，仅剩提示词 19 说明（非引文）中「截图人工通过」一处事实归属；已改为「截图由 Codex 查看通过」，原始历史 Prompt 引文保持不动。

### 提示词 22（用户授权推送 GitHub，仅改发布元数据，全文）

> 用户现在明确要求把完成的项目推送到 GitHub，并已完成账号授权。外部编排 Codex 已实际创建私有仓库 https://github.com/jiangdeliang495-hue/cognitive-diagnosis-claude ，配置最终交付目录的 origin，接下来由 Codex 执行并验证推送。你保持 Max，只在当前临时项目修改发布元数据：
> 1. README.md 末尾移除“远程同步暂缓”的当前状态，改为真实 GitHub 仓库 Markdown 链接，并说明这是私有仓库，评审需要仓库访问权限；邮件仍未发送。不要提前声称推送验证完成。
> 2. docs/SUBMISSION_DRAFT.md 标题只保留“仅草稿，未发送”；说明姓名待填、仓库链接已填；正文仓库替换为上述真实链接；末尾去掉“不推远程”以及“仓库链接待填写”等旧状态，保留未发送、姓名待填写以及评审需访问私有仓库的说明。
> 3. docs/PROMPT_LOG.md 保留全部历史 Prompt 原文和当时暂缓同步的真实记录，追加本次真实 Prompt（22）及说明：用户现已授权上传；私有仓库已创建；实际推送和远程验证由 Codex 进行。不要编造完成状态、邀请评审或发送邮件。
> 不改业务代码、测试、其他文档或PDF；不读凭据、不操作Git、不访问GitHub。完成后列出改动文件。

说明：用户已授权上传 GitHub；Codex 已实际创建私有仓库 `https://github.com/jiangdeliang495-hue/cognitive-diagnosis-claude` 并配置 origin，**实际推送与远程验证由 Codex 执行**。本会话只更新发布元数据（README 仓库链接与私有说明、SUBMISSION_DRAFT 状态、本日志），不编造推送完成状态、未邀请评审、未发送邮件；历史「暂缓同步」记录保留在原文中。

### 提示词 23（用户纠正为公开仓库，同步发布元数据，全文）

> 用户明确纠正：“公开啊我要提交啊”。Codex 已将最终仓库 https://github.com/jiangdeliang495-hue/cognitive-diagnosis-claude 改为公开。继续保持 Max，仅更新当前项目的发布元数据：
> 1. README.md 末尾改为“GitHub 公开仓库”的真实 Markdown 链接，移除“私有仓库，评审需要访问权限”等过时说明，保留邮件未发送。
> 2. docs/SUBMISSION_DRAFT.md 改为公开仓库、可直接访问，去掉评审需私有访问权限的说明；姓名仍待填写，邮件仍未发送。
> 3. docs/PROMPT_LOG.md 保留提示词22及所有历史原文中当时私有状态，追加本次真实提示词23和说明：用户要求公开以提交，Codex修改可见性，当前元数据同步公开状态。不要改业务代码/测试/PDF，不操作Git/GitHub，不读凭据，不编造邮件发送。
> 完成后列出改动文件。

说明：用户纠正要求仓库**公开**以便提交；Codex 已将仓库可见性改为公开。本会话仅把发布元数据（README、SUBMISSION_DRAFT、本日志）同步为公开状态；提示词 22 及其它历史原文中「私有」表述按当时事实保留；未改业务代码/测试/PDF，未操作 Git/GitHub，未读凭据，未编造邮件发送。

### 提示词 24（加分项「LLM 学习建议」：SDD 契约 + RED 测试，全文）

> 用户要求把加分项"利用LLM根据诊断结果生成个性化学习建议"完整做完，并继续保持最高思考。你当前Claude Code必须保持Max；运行时DeepSeek建议也默认最高reasoning_effort=max。本地临时项目 /private/tmp/claude-homework-t2WpwB 已由Codex逐文件核对并对齐真实公开Git基线8b45164；原79项Python与15组前端均曾外部通过。后续源码/测试/文档仍由你生成，Git提交、外部socket/浏览器验收和最终推送由Codex编排，不在沙箱伪称通过。
> 先真实调用已启用的Superpowers test-driven-development工作流。本轮只做SDD契约和RED测试，不实现src/static；完成后停止，等独立审查与实际RED记录后再实现。不要反复问用户设计选择，按下列已确认方案写文档和有意义的失败测试。
> 锁定功能：
> 1. 页面新增"AI学习建议"区，只有当前学生详情加载成功且用户点击"生成学习建议"才发POST；首屏/切学生/刷新不自动计费，不自动重试。独立loading/error/retry，避免影响已有诊断；生成中禁用防连点。切学生立即清空建议并abort旧等待，响应检查学生ID+请求序号，绝不把旧学生建议显示给新学生。模型输出全部textContent/DOM安全渲染，不能innerHTML。失败可手动重试；真实配置缺失明确提示，绝不伪造规则建议为LLM成功。
> 2. GET /api/llm/status 只返回configured/provider/model/reasoning_effort等非敏感状态。唯一付费接口 POST /api/students/{id}/advice，JSON请求体严格{}；浏览器不能提交概率/prompt/key/model/baseURL。服务端按ID重新读取当前学生的已存DINA掌握概率、独立答对率、5知识点与前置边，关闭只读SQLite连接后再调用。绝不读取profile_id/其他学生资料，也不重跑EM或改数据库。核心6个GET仍无外网、不需要密钥。
> 3. 仅从服务端环境DEEPSEEK_API_KEY读取运行时密钥，缺失503 LLM_NOT_CONFIGURED，密钥不进浏览器/HTML/JSON/日志/仓库。严禁读取Claude配置、Keychain、旧剪贴板或任何已有密钥。追加src.server的--prompt-key选项（标准库getpass隐藏输入；仅进当前进程环境，不存盘），方便用户在本机私下配置。原CLI调用和原79测试保持兼容。
> 4. DeepSeek官方已核实：固定HTTPS地址 https://api.deepseek.com/chat/completions；真实model=deepseek-v4-pro；Bearer认证；thinking={type:enabled}、reasoning_effort=max；response_format={type:json_object}；stream=false；max_tokens=8192以给最高思考保留预算。不要设置temperature假称控制思考。只使用最终choices[0].message.content，不返回reasoning_content。请求/响应字节有上限，网络有明确超时，不自动重试。注意urlopen(timeout)只是socket空闲超时，不要冒称绝对总deadline；若实现120秒整体响应截止须真的有测试和不会堆积失控线程的设计。固定供应商地址并禁止重定向，防Authorization被转发。
> 5. Prompt要求中文，掌握概率是模型估计且与答对率区分，考虑薄弱知识和前置关系，给具体练习动作与检查方法，不编造学生经历/测验结果，说明合成小样本局限。结构化advice={summary:string, priorities:[{kp_id:int,reason:string,actions:[string],check:string}]}；1~3项不同且存在的kp_id，行动1~3条，文本有长度/类型/非空限制。JSON mode不替代应用校验；空content/截断finish_reason/畸形或超长JSON/未知或重复技能ID必须拒绝。最终响应由服务器封装student_id,source=llm,provider=deepseek,model,reasoning_effort=max,advice（有实际request id/usage可脱敏保留）。
> 6. 路由先精确匹配advice，避免被学生详情的宽泛前缀误判。非法ID400/不存在404；advice非POST以及原GET的POST仍405；只接受小体积application/json、拒绝chunked/重复或歧义Content-Length/非{}请求体；异源Origin、Origin:null、不可信Host拒绝且不调用供应商，无宽泛CORS；无Origin的本机JSON客户端允许。并发付费请求限制，忙/上游429返回可手动重试状态。供应商401/402/5xx、URLError、timeout、损坏/超长响应均有明确中文错误及合适HTTP码，不能回显上游body/异常repr/key。
> 本轮交付：docs/LLM_SUGGESTIONS.md写冻结契约、模块接口和实现计划，更新API契约以容纳新接口但不声称已完成；tests/test_advice.py(纯逻辑+mock transport)、tests/test_advice_api.py(mock供应商真实本机HTTP)、tests/advice_e2e.cjs(mock路由的交互契约)。测试要验证具体学生快照、两学生prompt不同、无真值/其他学生/密钥泄漏；不合法请求零外网调用；各类上游失败与结构校验；DB前后不变；新UI成功/失败/缺配置/防双击/防学生竞态/XSS/390px/键盘。真实付费API验收单独进行，mock不算真实DeepSeek调用。源码尚未实现时运行能运行的RED，HTTP/浏览器受沙箱限制如实列出外部命令。记录本次Prompt全文、意图和Superpowers真实调用，不读凭据、不操作Git/推送/邮件。完成后等待审查，不提前写实现。

说明：批准加分项「LLM 学习建议」并锁定完整方案（UI 计费时机/防竞态/XSS、GET /api/llm/status 与唯一付费 POST /api/students/{id}/advice、仅环境 DEEPSEEK_API_KEY + --prompt-key、DeepSeek 官方参数锁定与安全边界、中文提示词与结构化 advice 校验、路由/Origin/Host/并发/错误映射）。本轮只做 SDD 契约与 RED 测试（docs/LLM_SUGGESTIONS.md + API_CONTRACT 增补 + tests/test_advice.py / test_advice_api.py / tests/advice_e2e.cjs），不实现 src/static，完成后停等审查。本轮已通过 Skill 工具**真实调用 superpowers:test-driven-development**（返回已加载、指令不变）。

### 提示词 25（独立审查第一轮：RED 测试自身缺陷纠偏，全文）

> 独立审查已读新SDD和RED测试，以下必须在实现前修正。仍保持Max、本轮仍只改契约/测试，不提前写实现；在PROMPT_LOG如实记录本次纠偏。
> 1. test_advice_api.py的共享transport.calls必须每个测试独立reset/新建，或使用每次调用数增量和本测试切片。unittest默认按字母排序，先前测试会污染后续success/status/prompt_differs的绝对次数断言；不能把错误测试当成正确RED。
> 2. 当前deadline测试只证明monotonic()+120传入自定义mock；忽略deadline、默认transport无限read()的伪实现仍可通过。请在契约暴露默认transport可测试接口，并写默认网络层行为测试：受控分块/保活空行+假时钟让整体deadline真实超期，验证中断且关闭响应资源；socket空闲timeout不能代替总截止。设计可选择单个受控读取线程/限流门禁，但不能无界线程堆积或声称未测的截止保证。覆盖真实urllib HTTPError、http.client.HTTPException/IncompleteRead等损坏响应，确保脱敏。
> 3. 禁重定向不能以“opener.handlers中完全没有HTTPRedirectHandler类型”当契约。正确的NoRedirect(HTTPRedirectHandler)子类也会被这种实现细节断言误杀。请改成行为测试：模拟302 Location到异源，断言没有第二次请求、更不转发Authorization，并返回安全的上游错误。
> 4. 区分客户端请求体上限（{}，4KiB足够）与供应商完整prompt JSON上限（中文诊断+系统约束可能超过4KiB，建议16KiB），不要混用MAX_REQUEST_BYTES误拒正常生成。边界须在文档与测试保持一致。
> 完成全部原定RED文件后，实际运行能够执行的单元测试；不要将socket沙箱失败算为正确RED，不要编造测试通过。完成后停止等待外部RED记录和复核，不实现src/static。

说明：独立审查第一轮纠偏——① test_advice_api 共享 transport.calls 按测试清零防字母序污染；② 契约暴露 default_transport 可测试接口并补默认网络层行为测试（假时钟+受控分块让整体 120s 截止真实超期、中断并关闭响应、socket 空闲超时仅作轮询粒度、单线程循环无线程堆积、真实 urllib HTTPError 与 HTTPException/IncompleteRead 损坏响应脱敏）；③ 禁重定向改为行为测试（302 异源 Location 不二次请求、不转发 Authorization、安全错误），删去 opener handler 类型内省；④ 区分 MAX_REQUEST_BYTES=4KiB（客户端 {}）与 MAX_PROMPT_BYTES=16KiB（供应商完整 JSON）。

### 提示词 26（独立审查第二轮：后端正例/框架字节与前端时序补强，全文）

> 补充独立审查反馈，仍保持Max、仍只强化RED测试/契约，不提前实现。请与上一条纠偏一起处理并记录真实Prompt。
> 后端必要补强：
> 1. 必须有带正确同源Origin（包含实际测试端口）的成功POST正例；否则“拒绝所有Origin”的伪实现也会全绿，浏览器反而不能用。再测同hostname异端口、恶意后缀域名拒绝且零供应商调用。
> 2. raw framing已有chunked/重复同值CL，再补冲突CL与TE+CL；Host使用真实绑定端口，避免被Host拒绝掩盖framing检查。
> 3. 完整build_prompt→build_request验证正常中文诊断能通过provider16KiB限制。第二份内容不同的合法上游响应必须原样映射到规范化advice，防硬编码fixture；独立临时库修改诊断后核对新prompt，校验实际答对率/前置边，而非只含KP名字。不要污染其它测试。
> 4. 补空/错类型choices、message、content；仅finish_reason=stop成功；布尔型kp_id拒绝；模型JSON未知字段明确剥离或拒绝，不能原样带出。
> 前端tests/advice_e2e.cjs必要修正：
> 5. C4故意mock HTTP502时Chromium会产生预期的资源console.error，不能把它当实现失败。仅豁免该测试明确注入的URL/status，仍保留所有pageerror与非预期console.error检查。
> 6. C2点击后立即断言posts.length有异步route竞态，须等待精确请求被捕获，再断言只一次。C3先确认学生1请求已进入挂起gate，才切学生2；用可控的响应/渲染条件断言，不用随意sleep200ms冒充竞态已测。
> 完成原定全部RED后停止等待实际外部RED运行和审查；不要把测试自身缺陷或环境socket权限失败当成业务正确RED。

说明：独立审查第二轮补强——① 同源 Origin（含实际端口）成功正例 + 同 hostname 异端口/恶意后缀域名拒绝且零供应商调用；② raw framing 补冲突 CL 与 TE+CL，Host 用真实绑定端口；③ 完整 build_prompt→build_request 通过 16KiB 上限、第二份不同合法上游内容原样映射（防硬编码 fixture）、独立临时库改 diagnosis 后核对真实新值/实际答对率/5 条前置边（不污染其它测试）；④ 空/错类型 choices/message/content、仅 finish_reason=stop、布尔 kp_id 拒绝、未知字段剥离；⑤ C4 预期 502 console.error 仅按注入 URL/status 豁免；⑥ C2 等待精确捕获后断言、C3 先确认进入挂起 gate 再切学生、不用随意 sleep 冒充竞态已测。

### 提示词 27（独立审查第三轮：前端 RED 最后一组补强，全文）

> 前端RED最后一组独立审查补强，请在实现前并入测试，保持Max且仍不实现业务：
> 1. C2要核对真实POST方法、JSON Content-Type和请求体{}，等预期summary/reason/actions/check文本实际出现；各文本字段都注入字面HTML并验证不会执行。
> 2. C3增加A→B→A且最早A最后返回的可控竞态，区分同学生ID的旧请求；用明确gate信号，不用固定sleep作为完成判据。
> 3. C4统计请求：失败后只有一次、点击手动重试才恰好第二次；未配置C5验证不可见而非必须DOM节点不存在，允许隐藏空容器。补未配置→配置状态改true后刷新→仅手动一次生成。
> 4. C6用真实Tab/Enter或Space触发按钮，不能focus后鼠标click冒充键盘验收；390px加合法长度的连续英文长词检查换行。
> 5. 默认mock掉所有付费POST，遗漏的POST直接abort并判失败，避免测试意外打真实API。继续严格检查pageerror，只对明确注入的失败URL/status豁免预期资源console.error。
> 记录本次Prompt；本轮只完善契约与RED，完成后停止等待Codex实际外部RED及审查，不提前实现。

说明：独立审查第三轮（前端 RED 最后一组）——① C2 核对真实 POST 方法/JSON Content-Type/严格 {}，等 summary/reason/actions/check 文本实际出现，各字段注入字面 HTML 并验证不执行；② C3 增 A→B→A 且最早 A 最后返回的同学生 ID 旧请求竞态，用明确 gate 信号；③ C4 失败恰好一次、手动重试恰好第二次，C5 以可见性（允许隐藏空容器）断言并补「未配置→已配置→刷新→仅手动一次生成」；④ C6 真实 Tab 遍历 + Space/Enter 键盘激活，390px 合法长度连续英文长词换行检查；⑤ 兜底 mock 所有付费 POST，漏网即 abort 并判失败防真实 API，pageerror 严格、仅豁免明确注入 URL/status 的预期 console.error。

### 提示词 28（余额补足 + 网络 RED 契约最后一轮纠偏，全文）

> 用户已补足Claude当前DeepSeek账户余额，明确要求继续Max开发。刚才两次402是真实阻塞，须如实记入Prompt日志，不伪造已完成。请从上次未完成的RED契约/测试修正继续，全部此前审查反馈保留，不重头设计。Codex已实际外部运行初始RED，记录docs/validation/advice-red-external-initial.txt：85 tests，7 errors（含setUpClass/import/尚未实现的llm参数），只是初始失败记录，不是最终契约验收。仍只完成测试/文档，不实现src/static，完成后停止等待Codex提交RED阶段再发实现指令。
> 未处理的最后一次反馈全文如下：
> 最后聚焦网络RED契约，修完即停止等外部RED，不再扩大范围、不实现业务，保持Max：
> 1. DefaultTransportTests多处deadline=9999.0却没注入假clock，真实monotonic可能早已超过9999，正确实现会误超时。统一用受控clock或time.monotonic()+余量，确保测试自身有效。
> 2. 不能用HTTPResponse.read(n)模拟真实保活：它内部可能连续多次底层读，持续空行可让一次调用跨越deadline。默认传输与fake响应应明确使用read1/单次有界读取，并在块之间检查monotonic，测试fake.read()可直接报错以防退回无限聚合读取。
> 3. socket.timeout后真实HTTPResponse缓冲对象可能已不可继续读，不应把它当安全轮询而catch后继续。socket空闲超时应立即安全关闭并返回TIMEOUT；用正常read1分块+假clock单独测读取截止。
> 4. 为避免过度承诺，文档如实限定120s为“响应读取截止检查”，连接/代理/TLS阶段受socket超时约束，不声称整次请求严格120s墙钟上限；保持单读取线程、无额外失控线程。这是澄清契约，不需要复杂后台线程体系。
> 5. 当前302测试给FakeOpener直接抛HTTPError，仍不能证明真实build_opener禁跳转。请在test_advice_api.py用仅本地临时HTTP服务器返回302、独立目标记录请求，实际调用build_opener().open，断言302未跟随、目标零调用且假Bearer未转发。纯单元fake异常映射测试可保留。受沙箱socket限制时如实等待外部执行，不能声称已在沙箱跑通。
> 记录本次纠偏后完成全部RED文件并停止；所有实现仍等下一轮授权。

说明：告知两次 402 为真实余额阻塞（如实记录，不伪造已完成），余额已补足并继续 Max；Codex 已外部运行初始 RED（`docs/validation/advice-red-external-initial.txt`：85 tests、7 errors，仅初始失败记录）。网络 RED 契约最后一轮纠偏——① 所有 default_transport 测试注入受控时钟（真实 monotonic 可能超 9999，测试自身不得误超时）；② 传输改用 read1 单次有界读取、块之间检查时钟，fake.read() 直接报错防退回聚合读取；③ socket.timeout 立即关闭并 TIMEOUT（不 catch 后轮询），读取截止用正常 read1 分块 + 假时钟单独测；④ 120s 如实限定为「响应读取截止检查」，连接/代理/TLS 只受 socket 超时约束；⑤ 新增本地 302 服务器 + 独立目标服务器的真实 build_opener 行为测试（外部执行，沙箱不声称跑通）。

### 提示词 29（LLM 建议后端 GREEN 实现指令，全文）

> RED阶段已由Codex真实外部执行并提交。保持Max，现进入GREEN实现：本轮只完成后端src/advice.py、src/server.py及--prompt-key，不修改static（前端另一步），不操作Git/推送/邮件、不读任何真实密钥/Claude配置/Keychain。
> 实际记录：docs/validation/advice-red-external-final.txt 新模块与llm注入参数缺失，7 tests/8 errors；浏览器RED正由外部在旧版页面运行，付费路由全mock，结束记录由Codex写入。不要把7当作所有测试方法数（模块缺失阻止发现）。原79项已有外部通过证据。
> 先修一个确定的测试自身遗漏：tests/test_advice.py引用http.client.IncompleteRead和HTTPException却没import http.client，补import并如实记入日志，不通过删测试解决。然后严格按已冻结docs/LLM_SUGGESTIONS.md实现后端，覆盖全部新纯单元/集成测试并保持原回归。不允许返回硬编码建议、规则结果冒充LLM或仅满足结构的伪网络层。
> 关键要求复述：固定真实deepseek-v4-pro、thinking enabled/reasoning_effort=max/max_tokens8192、JSON mode、只最终content；服务端env DEEPSEEK_API_KEY或--prompt-key(getpass隐藏输入只进当前进程、不存盘)，缺失503；GET状态不泄漏key；POST advice只接受{}、先校验真实Host/Origin/HTTP framing并限制并发，再从只读SQLite读取实时诊断快照（无profile_id、无其他学生），关闭连接后才发请求；不重跑EM、不改库。
> 网络传输严格read1单次有界读，仅读取环节检查120s截止，不夸称严格整次墙钟时限；socket空闲超时立即关闭返回TIMEOUT；连接/TLS受socket超时约束；响应finally关闭、禁重定向、无自动重试、输入/输出字节受限、异常/上游body不回显。严格结构校验并剥离未知字段；来源/学生ID由服务端封装。
> 默认transport、真实302不跟随与假Bearer不转发已由测试定义。路由advice先精确匹配，原6GET的非GET仍405；同源Origin成功必须可用；原CLI兼容，--prompt-key仅显式启用才询问，终端输入不可打印。必要实现内联小函数可自行选择，保持标准库零运行依赖。
> 沙箱里能跑的单元测试真实运行并保存GREEN记录；HTTP/socket/浏览器受限如实交外部Codex运行，不将权限失败算业务失败或伪造通过。若发现测试自身确定错误，最小修正并记录原因，不能为了实现方便降低契约。完成后列出改动和真实结果，停止等外部后端验收；不要开始前端和最终文档。

说明：批准进入后端 GREEN——只实现 src/advice.py、src/server.py 与 --prompt-key，不碰 static；先补 test_advice.py 缺 `import http.client` 的确定测试遗漏（如实记录），再按冻结契约实现：真实供应商参数锁定、env/--prompt-key 密钥、状态非敏感、POST 严格 {} 与 framing/Host/Origin/并发顺序、只读快照（无 profile_id/其他学生、关连接后调用、不重跑 EM 不改库）、read1 有界读取/读取截止/socket 超时立即 TIMEOUT/禁重定向/无自动重试/字节受限/不回显、结构校验剥离未知字段、服务端封装来源；沙箱可跑部分真实运行并保存 GREEN 记录。

### 提示词 30（后端独立审查两处确定边界缺口，先 RED 再修，全文）

> 后端独立审查已对真实HTTPResponse做内存模拟（无网络）确认两个确定边界缺口。保持Max，在本轮后端完成前先补真实失败回归再修复，记录RED/GREEN，不转前端：
> 1. default_transport仅在read1阶段捕获HTTPException，opener.open(req)若抛http.client.BadStatusLine/LineTooLong等HTTPException，会越过call_provider的URLError/OSError捕获落成500。open阶段也应安全映射502 BAD_RESPONSE（固定中文、不得暴露repr/body），并加覆盖open阶段真实HTTPException的测试。
> 2. 真正http.client.HTTPResponse.read1在提前EOF时不一定抛IncompleteRead。已验证Content-Length声明比实际完整JSON多10字节，当前返回200且会被当成功JSON接受（response.length还剩10）。请用HTTPResponse+内存BytesIO/假socket构造真实响应的RED，读取结束必须验证已知Content-Length/剩余长度完整，否则BAD_RESPONSE并关闭；不能只用会主动抛异常的FakeResponse冒充此覆盖。无Content-Length的正常响应仍须支持。
> 其余主路径复核未见阻塞：TLS验证保留、禁重定向、max/8192请求参数、最终content结构校验和key隔离均正确。另宿主默认python3缺少CA，匿名DeepSeek TLS失败；Codex bundled Python已无key请求HTTP401验证TLS可用，真实演示会用该可信运行时，禁止关闭证书校验或读取Keychain。无需因此改运行依赖。
> 完成后端与相应单元GREEN后停止，真实HTTP由Codex外部跑；不要写前端/最终交付文档，不操作Git/推送/邮件，不读真实key。

说明：后端独立审查对真实 HTTPResponse 内存模拟确认两处确定边界缺口——① open 阶段 HTTPException（BadStatusLine/LineTooLong，非 OSError/URLError）未捕获会落成 500；② read1 提前 EOF 不抛 IncompleteRead，Content-Length 声明多 10 字节时不完整响应会被当成功 JSON 接受。按 TDD 先补真实失败回归（真实 HTTPResponse + 内存 BytesIO/假 socket）再修复：open 阶段补 HTTPException → 502 BAD_RESPONSE；读取结束验证 resp.length 剩余长度（无 CL 响应仍支持）。其余主路径（TLS 验证/禁重定向/max 8192/结构校验/key 隔离）复核通过；宿主默认 python3 缺 CA，真实演示用 Codex bundled 可信运行时，禁止关闭证书校验或读 Keychain。

### 提示词 31（外部首轮完整后端回归：两处测试自身命名错误修正，全文）

> 外部首次完整后端回归真实结果已落盘docs/validation/advice-backend-external-initial.txt：Ran 144 tests，142通过、2 errors，均为新增测试自身确定命名错误：
> test_advice_upstream_error_mapping_and_no_leak（约439行）和test_advice_network_and_timeout_mapping（约471行）把局部变量http赋为预期HTTP整数，随后又调用http.client.HTTPConnection，导致AttributeError:'int' object has no attribute 'client'。请最小改名expected_http/http_status，保留原有状态码/脱敏断言，不删除或降低测试，日志如实记为测试修正而非业务失败。
> 继续完成上一条真实HTTPResponse的两处TDD修复后补此错误；纯单元可在沙箱跑，完整HTTP由Codex再执行。保持Max，不开始前端/最终文档，不读真实密钥、不操作Git/推送/邮件。完成后端全部修正后停止等验收。

说明：外部首次完整后端回归 144 tests、142 通过、2 errors，均为新增测试自身命名错误——两个测试把局部变量 `http` 赋为预期 HTTP 整数，遮蔽模块名导致 `http.client.HTTPConnection` 报 `AttributeError`。最小改名 `http → expected_http`（保留全部状态码/脱敏断言，不删不降），如实记为测试修正而非业务失败；上一轮两处真实 HTTPResponse 边界修复保持 GREEN。

### 提示词 32（LLM 建议前端实现指令，全文）

> 保持Max，后端已完成外部完整GREEN验收（真实结果由Codex存docs/validation/advice-backend-external-final.txt）。现进入前端实现阶段，仅改static/index.html、app.js、style.css及必要真实日志；不改DINA、数据库、后端契约，不操作Git/推送/邮件，不读真实Key。
> 先阅读冻结docs/LLM_SUGGESTIONS.md与tests/advice_e2e.cjs。该文件的C1-C6已在旧版真实浏览器外部RED：0通过/6失败，全部因未实现建议区/按钮/配置提示；记录docs/validation/advice-e2e-red-external.txt，不是浏览器权限错误。保持原15组前端回归。
> 实现"AI学习建议"卡片：只有当前学生详情成功后才读取GET /api/llm/status并启用对应UI，配置缺失显示简短中文"未配置"说明，不暴露env/key等实现细节；真实生成按钮仅点击才POST /api/students/{id}/advice，JSON{}，生成中禁用；单独loading/error/retry，不影响现有诊断；失败后不自动重试，只有手动重试才第二次请求。
> 切学生立即清空旧建议并abort旧等待；当前学生ID+请求序号双校验，A→B→A时最早A的旧响应不能覆盖新A；状态请求/详情加载也防旧响应启用错学生按钮。缺配置后服务重启/刷新状态可恢复。建议summary、每个priority的知识点名称、reason、actions、check全部用DOM/textContent安全渲染，模型字符串不允许innerHTML（包括恶意HTML字面文本）。展示清楚AI来源DeepSeek V4 Pro与最高思考，提示是基于合成诊断的学习建议，不改掌握概率本身。
> 可访问性：native button、关联标题、独立状态aria-live和错误role=alert，真实Tab+Space/Enter可操作；390px长英文词正常换行、无页面横向溢出；沿用现有简洁中文卡片视觉，不加大框架或依赖、无CDN。
> 严守已有data-testid，具体以测试契约为准。新建议UI不能复用全局loading/error/retry导致旧测试混淆。基础诊断失败时禁用生成并清空建议，不能拿上一学生数据生成。
> 运行能运行的静态/语法检查，浏览器受沙箱限制则交Codex外部运行，不伪造GREEN。若发现确定测试自身错误仅最小修正并如实记录，不能删失败断言或降低契约。完成后停止等外部前端验收，最后README/PRD/架构/开发说明/LLM文档和PDF在验收结果齐全后再统一同步，不提前声称真实DeepSeek调用已成功（真实Key尚未配置，所有目前测试均mock）。

说明：批准进入前端 GREEN——仅改 static/index.html、app.js、style.css 与真实日志；后端外部完整 GREEN 已落盘（advice-backend-external-final.txt）。按冻结 UI 契约实现「AI 学习建议」卡片：详情成功后才读状态、仅点击才付费 POST、生成中禁用、独立 loading/error/retry、手动重试、切学生清空+abort+学生 ID/序号双校验、状态请求防旧响应、textContent 安全渲染、DeepSeek V4 Pro 来源提示、native button/aria-live/alert、390px 长词换行；不伪造浏览器 GREEN（沙箱限制交 Codex 外部运行）。

### 提示词 34（前端外部验收通过后，独立复核发现状态错误误报的精确修复，全文）

> 保持 DeepSeek V4 Pro Max。外部前端验收结果：docs/validation/advice-e2e-green-external.txt 为 C1-C6 6/6；docs/validation/frontend-regression-with-advice.txt 为原15/15。独立只读复核发现一处明确业务错误：static/app.js loadAdviceStatus catch 将网络异常、HTTP500、非法JSON统一显示为“未配置模型服务密钥”，已配置服务短暂失败也会误导用户。请做最小修复。
> 先在既有 tests/advice_e2e.cjs C5 中补充状态查询失败→独立中文错误→手动只重试GET状态→配置成功启用按钮的断言；状态失败不能显示“未配置”，不能发付费POST；包括切学生后旧状态失败不得污染新学生。保持6组的其他断言与原15回归。外部QA稍后执行，不谎称沙箱浏览器通过。
> 实现明确状态错误与手动重试（可使用现有独立advice-error/advice-retry并区分重试状态/生成模式，或独立按钮，以最小可靠实现为准）。只有成功GET且configured===false才缺配置；网络失败/HTTP失败/非法JSON显示“无法获取模型配置状态，请重试”。状态重试只GET，不POST，成功后仍必须点击生成才付费。切换清空，状态序号与学生双校验保持，生成失败的手动重试原行为保持。适量更新LLM契约及真实PROMPT_LOG，不更新最终验收/README，不操作Git、真实Key、推送、邮件。完成后停下等外部再验收。

说明：外部前端验收 C1–C6 6/6、原 15/15 全绿后，独立只读复核发现一处明确业务错误——loadAdviceStatus 的 catch 把网络异常/HTTP500/非法 JSON 一律显示为「未配置」，已配置服务的短暂失败会误导用户。最小修复：先在既有 C5 补状态失败→独立中文错误→仅 GET 重试→恢复后仍须点击生成、以及切学生旧状态失败不污染新学生的断言；实现「只有成功 GET 且 configured===false 才判未配置」、状态失败显示「无法获取模型配置状态，请重试」、advice-retry 按模式区分（状态重试只 GET / 生成重试 POST）；不更新最终验收/README。

### 提示词 35（外部 5/6 仅 C5 迟到 console 误判，测试 fixture 最小修正，全文）

> 保持Max。外部复跑记录 docs/validation/advice-e2e-status-fix-external.txt：5/6，仅C5末尾严格console检查失败，文本“Failed to load resource: the server responded with a status of 500 (Internal Server Error)”。C5所有业务断言已经走完，失败是故意注入500的console事件晚到而clearExpectFail提前清空的测试异步竞态。不要改业务、不要删断言或全局忽略资源错误。
> 请最小修正tests/advice_e2e.cjs预期失败资源过滤：只允许该case明确注入的失败请求URL与确切已知5xx状态的console资源错误，依据consoleMessage.location().url匹配；考虑该故意失败console可能晚于UI状态出现，保留该case已注入记录直至page关闭，而不是提前clear导致迟到日志误判。其他URL、其他console.error、所有pageerror继续零容忍。若location缺失不能泛化豁免。C4原502也保持严格作用域。保留C1-C6全部业务断言，如实记录是测试fixture修正、外部5/6。不要声称本轮真实API成功、不操作Git、不读Key。完成停下等外部。

说明：外部复跑 5/6（`docs/validation/advice-e2e-status-fix-external.txt`），仅 C5 末尾严格 console 检查失败——故意注入的 500 的 console 事件晚于 UI 状态出现，而 `clearExpectFail` 提前清空导致迟到日志误判；C5 全部业务断言已走完。最小修正（仅测试 fixture，不改业务、不删断言、不全局忽略资源错误）：预期失败豁免改为按 console 消息 `location().url` 与该 case 明确注入 URL 精确匹配 + 确切 5xx 状态；注入记录保留至页面关闭（移除提前 clear），`location` 缺失不泛化豁免；C4 的 502 同样严格作用域；C1–C6 全部业务断言保留。

### 环境核验（阶段 0，真实命令结果）

- `pwd` → `/private/tmp/claude-homework-t2WpwB`（与要求一致）
- `python3 --version` → `Python 3.13.10`
- `python3 -c "import sqlite3; print(sqlite3.sqlite_version)"` → `3.50.4`
- `git --version` → `git version 2.50.1 (Apple Git-155)`
- 技能清单含 `superpowers:brainstorming`，已通过 Skill 工具真实触发并加载其工作流。
- 首次 builder 复核子代理因 API `402 Insufficient Balance` 提前终止（未产出结论），
  随后用户补足余额，Codex 转达独立审查意见（提示词 2）。

---

## 阶段 1：docs/schema（进行中，本轮）

> 产物：PRD、ARCHITECTURE、ER、schema.sql、API_CONTRACT、设计规格、本 PROMPT_LOG。
> 依据提示词 1 + 提示词 2 纠偏后定稿。
>
> 真实命令与结果（阶段 1）：
> - 聚焦一致性复核子代理（继承 Pro 模型）→ 返回 `consistent`（三处修正一致）。
> - `git init` → 失败：`/private/tmp/claude-homework-t2WpwB/.git: Operation not permitted`。
>   定位：`mkdir .wtestdir` 成功、`mkdir .git` 报 EPERM，确认是沙箱对 `.git` 路径的写拦截。
>   因此本会话无法在项目内创建 git 仓库/提交；**未产生任何伪造的 commit ID**。
> - 随后由外部编排在同一项目成功执行 `git init`（本会话不再尝试 .git 写入）；后续 add/commit
>   由外部编排/用户执行，文档与代码仍全部由本会话生成。
> - 外部编排已完成真实设计提交：`65d020e docs: define cognitive diagnosis requirements schema and contracts`。

## 阶段 2：tests（RED）—— RED 已复现

> 真实命令与结果：
> - `python3 -m unittest discover -s tests -v` → `Ran 20 tests ... FAILED (errors=20)`，`EXIT_CODE=1`。
> - 20 个测试全部因 `src/dina.py` 接口桩抛 `NotImplementedError` 而 RED（来自待实现行为，非语法/导入错误）。
> - 原始命令、退出码与输出已存 `docs/validation/algorithm-red.txt`。
> - 本会话不写 `.git`；test 提交由外部编排创建。
> - 补强（提示词 5）：新增两步 EM 手算断言与后验边际一致性断言；`python3 -m unittest discover -s tests -v`
>   → `Ran 22 tests ... FAILED (errors=22)`，`EXIT_CODE=1`；原始输出存 `docs/validation/algorithm-red-strengthened.txt`（保留原 algorithm-red.txt）。
> - 外部编排已完成真实 test 提交：`d03855c test: specify DINA posterior and EM behavior in red`。
> - 外部编排已完成补强 RED 提交：`b72928f`（新增两步 EM 手算与后验边际一致性断言）。

## 阶段 3：feat（GREEN）—— 纯算法已实现，22/22 通过

> 真实命令与结果：
> - `python3 -m unittest discover -s tests -v` → `Ran 22 tests ... OK`，`EXIT_CODE=0`。
> - 原始命令、退出码与输出已存 `docs/validation/algorithm-green.txt`。
> - 实现 `src/dina.py`（纯算法，零依赖）；本会话不写 `.git`；feat 提交由外部编排创建。
> - 尚未开始数据库/HTTP/前端。

## 阶段 4：后端 tests（RED）—— SQLite / seed / HTTP

> 真实命令与结果：
> - `python3 -m unittest discover -s tests -v` → `Ran 48 tests ... FAILED (errors=26)`，`EXIT_CODE=1`。
> - 22 项算法测试保持通过；26 个错误全部来自 db/data_gen/seed/server 接口桩的
>   `NotImplementedError`（待实现行为，非语法/导入错误）。原始命令、退出码与输出已存
>   `docs/validation/backend-red.txt`。
> - 本会话不写 `.git`；test 提交由外部编排创建。
> - 外部编排已完成真实 RED 提交：`8198b90`。
> - 补强（提示词 10）：新增 5 项核心数据链断言（真 EM 重校准逐题比对、X 288 条完整性、
>   API 数值逐格对照）；`python3 -m unittest discover -s tests -v`
>   → `Ran 50 tests ... FAILED (errors=28)`，`EXIT_CODE=1`；原始输出另存
>   `docs/validation/backend-red-strengthened.txt`（保留原 backend-red.txt）。

## 阶段 5：后端 feat（GREEN）—— SQLite / seed / HTTP 已实现

> 真实命令与结果：
> - `python3 -m unittest discover -s tests -v` → `Ran 50 tests ... FAILED (errors=1)`，`EXIT_CODE=1`。
> - 50 项（算法 22 + schema 6 + data_gen 12 + seed 10）全部通过；唯一错误是 test_api 的
>   `setUpClass` 因**沙箱禁用本机端口绑定**（`socket.bind` → `PermissionError: Operation not permitted`）
>   而无法绑定 `127.0.0.1`，并非代码缺陷。
> - 16 个 HTTP 测试需 `sandbox.network.allowLocalBinding: true` 才能运行；其 6 个接口的查询逻辑
>   已另经「不绑定端口的直连校验」逐项验证通过（对照 SQLite 逐格一致）。
> - 实现 `src/db.py`、`src/data_gen.py`、`src/seed.py`、`src/server.py`，新增 `docs/ALGORITHM.md`。
> - 本会话不写 `.git`；feat 提交由外部编排创建。
> - 修复一处实现缺陷：`_items` 曾以 `dict()` 直接消费 3 列行（应为 `{qid:(g,s)}`），直连校验发现并已改正。
> - 外部编排已在**沙箱外**原样运行全套测试：`Ran 66 tests in 2.604s ... OK`，`EXIT_CODE=0`；
>   原始输出存 `docs/validation/backend-external-initial.txt`。这是 Codex 在已授权的外部验收
>   环境运行同一脚本，**不是**修改 Claude 沙箱设置。
> - 外部编排已完成后端补强测试提交：`2e72fdb`。
> - 回归修复（提示词 12）：补 12 项回归测试（CLI 的 `--help`/直接脚本/临时 DB 启动、
>   ID 边界解析、HTTP/1.1、超大 ID→400），RED 存 `docs/validation/backend-red-regression.txt`；
>   修复 `DEFAULT_DB_PATH` 缺失、直接脚本 `from src` 引导、argparse `--help`、HTTP 异常边界、
>   ID int64 越界→400、`allow_nan=False`、`protocol_version="HTTP/1.1"`。
>   修复后沙箱内 `Ran 60 tests ... FAILED (errors=2)`（仅剩 2 个沙箱 EPERM 端口绑定，非代码缺陷），
>   存 `docs/validation/backend-green-fixed.txt`；原始 `backend-green.txt` 保留并注明为沙箱内结果。

## 阶段 6：E2E —— RED 已提交，前端 GREEN 已实现（待外部浏览器验收）

> 产物：`tests/browser_e2e.cjs`（浏览器 E2E + HTTP 静态契约测试）、`package.json`
> （仅 QA devDependency playwright 1.62.1）、`docs/FRONTEND_CONTRACT.md`（前端契约）、
> `static/index.html`、`static/style.css`、`static/app.js`（前端实现）。
>
> **RED（真实，已由外部编排提交）**
> - 网页未实现时，外部编排原样运行 HTTP 静态部分：
>   `E2E_BASE_URL=http://127.0.0.1:8765 node tests/browser_e2e.cjs --http-only`
>   → `3 通过 / 3 失败`，`EXIT_CODE=1`；原始输出存 `docs/validation/frontend-red-http-external.txt`
>   （3 项静态 MIME 测试 RED 于 404，路径穿越 / 白名单 / API-MIME 3 项通过）。
> - 独立复核发现的 7 组 E2E 测试自身缺陷已按提示词 14 逐条修复。
>
> **GREEN（本会话实现，沙箱内可核验部分）**
> - 实现 `static/index.html`（语义骨架：viewport、标题、label 关联、loading/error/retry、
>   局限提示、可展开模型说明）、`static/style.css`（浅灰底 / 深靛蓝 / 白卡片 / 系统中文字体 /
>   390px 响应式 / 矩阵容器内滚动 / 可见焦点）、`static/app.js`（AbortController 防陈旧覆盖、
>   中文加载/错误/重试、雷达与图谱 SVG、12×5 矩阵、突出当前学生）。
> - 题库题干修正：`src/seed.py` 用冻结的 `_QUESTION_STEMS`（24 条互不相同）替换重复短语；
>   KP5 单技能只考列式并给出算术结果，KP3 单技能不要求自行通分。数据规模/Q/X/估计逻辑冻结。
> - 按 TDD 先补 `tests/test_seed.py::test_question_stems_distinct_descriptive_and_isolated`
>   （RED：`14 != 24`）再实现（GREEN）。全套测试总数变为 **79**（外部编排可全部跑绿）。
> - 沙箱内真实结果（存 `docs/validation/frontend-green-sandbox.txt`）：
>   `python3 -m unittest discover -s tests -v` → `Ran 61 tests ... FAILED (errors=2)`，`EXIT_CODE=1`；
>   59 项全部通过，仅 2 个 HTTP 绑定测试因沙箱 `socket.bind → PermissionError: Operation not permitted`
>   而报错（test_api.setUpClass 与 test_cli 端口绑定，非代码缺陷）。`node --check static/app.js`
>   与 `node --check tests/browser_e2e.cjs` 均通过。
>
> **浏览器 E2E（外部已运行 12/13，修复后待重跑）**
> - 沙箱禁用本机端口绑定（`socket.bind` EPERM），本会话无法起服务运行浏览器 E2E。
> - 外部编排首次真实运行（存 `docs/validation/frontend-external-initial.txt`）：
>   `12 通过 / 1 失败`（HTTP 静态 6/6 + B1–B6 全过）；唯一失败 B7「键盘 End 应选中学生 12」——
>   macOS Chromium 原生 `<select>` 不响应 `End`。
> - 按提示词 16 修复：① app.js 为 select 显式 `keydown` 处理 `Home`/`End`（设首/末选项并触发
>   同一 `change` 加载），方向键保持原生；② 切换学生请求开始即清空旧诊断 + 显示中文加载态、
>   成功才渲染新数据、失败保持清空并显示错误（仅当前请求可结束 loading，旧 Abort 不覆盖）；
>   ③ 图谱节点名称改深色置于圆外下方、圆内只放白色百分比；④ 「关于本模型」补固定均匀先验 /
>   32 画像 / DAG 单调只用于造数 / guess,slip∈[.02,.35] / 独立 Bernoulli 噪声与小样本局限。
> - 补回归测试：B6 增「失败后旧诊断清空」断言；新增 B8（切换先清空+加载，成功后再显示新数据）、
>   B9（图谱节点名称深色在圆外、百分比白色在圆内）；runner 改为按 `viewport` 分组跑桌面/移动。
> - `node --check static/app.js` 与 `node --check tests/browser_e2e.cjs` 均通过（沙箱内）。
> - 外部编排重跑后**全绿**：Python `Ran 79 tests ... OK`（存
>   `docs/validation/python-external-final.txt`）；前端 `15 通过 / 0 失败`（存
>   `docs/validation/frontend-external-final.txt`），`EXIT_CODE=0`。
> - 截图复查发现提示词 17 两处样式修正未真正生效，按提示词 18 最小修正：① 全体矩阵
>   `<table>` 补 `id="all-students-table"`（此前仅 `data-testid`，`#all-students-table` CSS 全部无效）；
>   ② 雷达每轴共用同一锚点 `lp=vertex(k,R+32)`，名称 `y=lp.y-5`、百分比 `y=lp.y+11`（相同 x、
>   12/11px，text-anchor middle），保持 340 viewBox、R/cx/cy、valuePts 不变。
> - `node --check static/app.js` 通过；最终截图与浏览器复核交由外部编排核验后，本阶段方可勾选通过。

## 阶段 7：LLM 学习建议（已实现，模拟验收通过；以下保留过程记录）

> 产物：`docs/LLM_SUGGESTIONS.md`（冻结契约/模块接口/实现计划）、`docs/API_CONTRACT.md` §8
> （新接口契约，标注实现未开始）、`tests/test_advice.py`（纯逻辑 + mock transport）、
> `tests/test_advice_api.py`（mock 供应商 + 真实本机 HTTP）、`tests/advice_e2e.cjs`
> （mock 路由 UI 交互契约）。
>
> 真实命令与结果：
> - 本轮通过 Skill 工具**真实调用 `superpowers:test-driven-development`**（返回已加载）。
> - 独立审查三轮纠偏（提示词 25/26/27）已全部并入契约与 RED：共享 transport 调用清零、
>   default_transport 可测试接口与假时钟整体截止/损坏响应/资源关闭行为测试、302 行为测试（不二次
>   请求/不转发 Authorization）、MAX_REQUEST_BYTES=4KiB 与 MAX_PROMPT_BYTES=16KiB 分离、同源 Origin
>   成功正例与恶意后缀拒绝、冲突 CL/TE+CL raw framing、独立临时库改 diagnosis 核对真实新值/实际
>   答对率/前置边、第二份合法内容原样映射、布尔 kp_id/未知字段剥离/仅 finish_reason=stop、
>   E2E 兜底安全网/预期 502 豁免/确定 gate 时序/A→B→A 竞态/真实 Tab+Space 键盘/长英文换行。
> - `python3 -m unittest tests.test_advice -v` → `ImportError: cannot import name 'advice'`，
>   `EXIT_CODE=1`；`python3 -m unittest discover -s tests -v` → `Ran 67 tests ... FAILED (errors=9)`，
>   `EXIT_CODE=1`。9 个错误中 7 个来自待实现功能（test_advice 模块缺失、`make_server` 尚无 `llm`
>   注入参数的 TypeError），另 2 个为沙箱 `socket.bind` EPERM（test_api/test_cli，历史既有）；
>   其余 58 项全部通过（原 79 项外部绿色基线不受影响）。原始输出存 `docs/validation/advice-red.txt`。
> - `node --check tests/advice_e2e.cjs` → 语法通过（SYNTAX_OK）。
> - HTTP/浏览器受沙箱限制，RED 与后续验收的外部命令（由 Codex 编排）：
>   ```
>   python3 -m unittest tests.test_advice_api -v
>   python3 -m src.seed /tmp/cdiag-e2e.db && python3 -m src.server /tmp/cdiag-e2e.db 8000 &
>   NODE_PATH=<含 playwright 的 node_modules> PLAYWRIGHT_BROWSERS_PATH=<pw-browsers> \
>     E2E_BASE_URL=http://127.0.0.1:8000 node tests/advice_e2e.cjs
>   ```
> - 真实付费 API 验收单独进行（配置真实 DEEPSEEK_API_KEY 后人工点击 1~2 名学生）；mock 测试
>   不算真实 DeepSeek 调用。
> - **过程如实记录**：提示词 25–27 之后出现两次真实 402（账户余额不足）中断，余额由用户补足后
>   继续；本轮未伪造任何已完成状态。
> - 第四轮纠偏（提示词 28，网络 RED 契约）：default_transport 测试全部注入受控时钟（真实
>   monotonic 可能超过裸 9999，测试自身不得误超时）；传输用 `read1` 单次有界读取、块之间检查
>   时钟，fake.read() 直接报错防退回聚合读取；`read1` 抛 socket.timeout → 立即安全关闭并返回
>   TIMEOUT（不 catch 后轮询）；读取截止用正常 read1 分块 + 假时钟单独测试；120s 如实限定为
>   「响应读取截止检查」（连接/代理/TLS 只受 socket 超时约束），保持单读取线程；
>   新增真实 build_opener 禁跳转行为测试（本地 302 服务器 + 独立目标服务器，目标零调用、
>   Bearer 不转发；需端口绑定，沙箱外执行，不声称沙箱已跑通）。
> - Codex 已外部运行初始 RED 并记录 `docs/validation/advice-red-external-initial.txt`
>   （85 tests、7 errors，含 setUpClass/import/尚未实现的 llm 参数）——只是**初始失败记录**，
>   不是最终契约验收。
> - 测试自身遗漏修正（提示词 29）：`tests/test_advice.py` 引用 `http.client.IncompleteRead`/
>   `HTTPException` 但未 `import http.client`，已补导入（不删测试），如实记录。
> - **后端 GREEN（本会话实现，沙箱内可核验部分）**：实现 `src/advice.py`（纯标准库：严格 {} 校验、
>   中文提示词、结构校验剥离未知字段、供应商载荷锁定、NoRedirect opener、read1 单次有界读取、
>   读取截止检查、socket 空闲超时立即 TIMEOUT、损坏响应脱敏、call_provider 只取最终 content/
>   仅 finish_reason=stop、status_payload 非敏感）与 `src/server.py` 集成（`make_server(llm=…)` 注入、
>   GET `/api/llm/status`、POST `/api/students/{id}/advice` 先精确匹配、framing→Host→Origin→ID→
>   请求体→配置→并发门禁（共享 Lock，BUSY 429）→只读快照（关连接后调用，无 profile_id/其它学生，
>   不重跑 EM 不改库）→服务器封装，`--prompt-key` 用 getpass 仅写当前进程环境）。
> - 沙箱内真实结果（存 `docs/validation/advice-green-sandbox.txt`）：`tests.test_advice` **40/40 OK**；
>   全套 `Ran 107 tests ... FAILED (errors=9)`，9 个错误**全部**为沙箱 `socket.bind`
>   `PermissionError: Operation not permitted`（HTTP/socket 测试需端口绑定），**零业务失败**、
>   未伪造通过；HTTP/socket 部分交 Codex 沙箱外运行同一测试并回填真实结果。
> - 边界回归（提示词 30）：先补两条真实失败回归并跑出 RED（存
>   `docs/validation/advice-boundary-red.txt`：open 阶段 `BadStatusLine` 逃逸为 ERROR；
>   提前 EOF 不完整响应被当成功 FAIL），再修复（open 阶段补 HTTPException→502 BAD_RESPONSE；
>   读取结束验证 `resp.length` 剩余长度，无 CL 响应仍支持），修复后
>   `DefaultTransportTests` 11/11 OK、`tests.test_advice` **43/43 OK**；全套沙箱内
>   `Ran 110 tests ... FAILED (errors=9)`，9 个错误仍全部为沙箱 socket.bind EPERM（HTTP/socket
>   交 Codex 沙箱外运行），零业务失败（记录已追加到 `docs/validation/advice-green-sandbox.txt`）。
> - 测试自身命名错误修正（提示词 31）：两个测试局部变量 `http` 遮蔽模块名，最小改名
>   `expected_http`（保留全部断言，不删不降），如实记为测试修正而非业务失败；外部首轮结果
>   `docs/validation/advice-backend-external-initial.txt`（144 tests、142 通过、2 errors 均为该命名错误）。
> - 修正后沙箱内：`tests.test_advice` 43/43 OK；全套 `Ran 110 tests ... FAILED (errors=9)`，
>   9 个错误仍全部为沙箱 socket.bind EPERM（HTTP/socket 由 Codex 沙箱外再执行），零业务失败
>   （记录追加于 `docs/validation/advice-green-sandbox.txt`）。
> - **前端 GREEN（本会话实现，沙箱内可核验部分）**：static/index.html 新增「AI 学习建议」卡片
>   （advice-section/generate-advice/advice-config-missing/advice-loading/advice-error/advice-retry/
>   advice-content，全部独立不复用全局 testid）；app.js 实现 clearAdviceUI/loadAdviceStatus/generateAdvice/
>   renderAdvice——详情成功后才读 GET /api/llm/status、仅点击才付费 POST（体严格 {}、生成中禁用）、
>   独立 loading/error/retry 且失败不自动重试、切学生立即清空并 abort 旧等待、学生 ID+请求序号双校验
>   （A→B→A 最早 A 旧响应不覆盖新 A）、状态请求序号防错学生按钮、诊断失败清空建议并禁用生成、
>   模型字符串全部 textContent 渲染禁 innerHTML、来源标注 DeepSeek V4 Pro；style.css 增按钮/未配置/
>   建议内容样式与 overflow-wrap 长词换行。
> - 沙箱内自检：`node --check static/app.js` SYNTAX_OK；HTML/JS data-testid 契约自检 OK；
>   Python 43 项纯单元 OK、全套 110 项仅 9 个既有沙箱 EPERM（不受前端影响）。
> - 浏览器 E2E 受沙箱限制，交 Codex 外部运行同一测试并回填真实结果；C1–C6 旧版外部 RED 记录
>   `docs/validation/advice-e2e-red-external.txt`（0 通过/6 失败，均为未实现建议区，非浏览器权限错误）。
> - **不提前声称真实 DeepSeek 调用已成功**（真实 Key 尚未配置，所有目前测试均 mock）。
> - 状态错误误报修复（提示词 34）：C5 补「状态查询失败→独立中文错误→仅 GET 手动重试→恢复后
>   按钮启用且仍须点击生成；切学生后旧状态失败不污染新学生」断言（外部 QA 稍后执行，不谎称
>   沙箱浏览器通过）；app.js 修复——只有成功 GET 且 `configured===false` 才显示「未配置」，
>   网络/HTTP 失败/非法 JSON 显示「无法获取模型配置状态，请重试」，advice-retry 按模式区分
>   （状态重试只 GET 绝不 POST；生成重试原行为），状态序号与学生双校验、切换清空保持。
> - 外部前端验收已落盘：`docs/validation/advice-e2e-green-external.txt`（C1–C6 6/6）、
>   `docs/validation/frontend-regression-with-advice.txt`（原 15/15）。
> - 沙箱内自检：app.js / advice_e2e.cjs 语法通过；Python 43 项纯单元 OK。
> - 本轮不读凭据、不操作 Git/推送/邮件；**已停止，等待外部再验收**，README/PRD/架构/开发说明/
>   LLM 文档与 PDF 待验收结果齐全后再统一同步。

## 阶段 8：外部验收与 Codex 文档收尾（非 Claude 提示词）

- 提示词35后，最终外部建议浏览器验收6/6通过，记录为advice-e2e-final-external.txt；故意注入500迟到日志的5/6失败记录未删除。
- 开发工具于2026-10-17本地时间06:18:40再次返回402（Insufficient Balance）。源码与测试已完成并保存；该开发工具错误不当作应用业务测试结果。
- 用户随后授权Codex接手收尾。Codex直接更新README、需求/架构/接口/前端/建议/算法/工具链说明、开发过程说明与提交草稿，完成PDF排版及交付编排；未将这些编辑转交Claude，不记作DeepSeek新生成。
- 本轮不重写既有历史Prompt，不伪造用户手写/手测或未发生的真实调用。原始RED文字记录保留；advice-status-fixture-failure.png是后续C5测试fixture失败截图，原初始RED截图曾被后续运行覆盖，不将该图冒充初始未实现截图。
- 真实建议的Key需用户私下配置，不能读取Claude凭据或在聊天里索要；缺配置的核心诊断仍可运行。GitHub公开同步已授权，邮件只为草稿。
