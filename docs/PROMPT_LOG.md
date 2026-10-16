# PROMPT_LOG —— 本会话实际收到的核心提示词

本文件**逐步、如实**记录本会话真实收到的核心提示词，每段配 1–2 句说明。
**未发生的阶段不会在这里被标记为「完成」。**

> **过程与模型路由（如实记录）**
> - 实际过程：Codex 代用户操作 Claude Desktop Code；开发由本会话中的模型与
>   Superpowers 工作流完成。
> - 模型路由：界面 **DeepSeek V4 Pro**，发送兼容别名 `claude-opus-4-8`，
>   **DeepSeek Gateway 路由**（`https://api.deepseek.com/anthropic`）。
> - 本会话未读取任何 API Key，也不声称读取过真实供应商的内部身份。

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

### 环境核验（阶段 0，真实命令结果）

- `pwd` → `/private/tmp/claude-homework-t2WpwB`（与要求一致）
- `python3 --version` → `Python 3.13.10`
- `python3 -c "import sqlite3; print(sqlite3.sqlite_version)"` → `3.50.4`
- `git --version` → `git version 2.50.1 (Apple Git-155)`
- 技能清单含 `superpowers:brainstorming`，已通过 Skill 工具真实触发并加载其工作流。
- 首次 builder 复核子代理因 API `402 Insufficient Balance` 提前终止（未产出结论），
  随后用户补足余额并直接给出审查意见（提示词 2）。

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

## 阶段 5：E2E —— 未开始
