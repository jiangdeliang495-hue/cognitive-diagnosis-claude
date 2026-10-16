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

说明：告知外部浏览器验收 12/13（仅 B7 失败于 macOS Chromium 原生 select 不响应 End），并给出独立 UI 复核的两项问题（①切换/失败时旧诊断未清空导致归属错误；②图谱 KP5 白色长名溢出圆不可读），要求先补最小回归测试再按 TDD 修复，并补「关于本模型」约定说明；记录前端测试提交 3a21168。

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
