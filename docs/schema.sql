-- ============================================================================
-- 智能化认知诊断 MVP —— SQLite 模式定义（单一事实来源）
-- ----------------------------------------------------------------------------
-- 说明：
--   1. 本文件是数据模式的唯一权威定义；src/db.py 在运行时按同一定义建库，
--      确保「文档 = 代码」一致。
--   2. Q 矩阵与 X 作答矩阵以长表（incidence）形式落库：这是它们在关系模型中的
--      规范化表达，逻辑上分别等价于「题目 × 知识点」「学生 × 题目」两个 0/1 矩阵。
--   3. diagnosis 表存 DINA 后验边际的「掌握概率」（∈ [0,1]），由 seed 阶段对 Q/X
--      校准后写入，服务端只读。它来自 32 种潜在画像的对数后验边际化，绝不是答对率，
--      也不是由合成真值直接生成。
--   4. student.profile_id（0..31 位掩码）是**合成真值**，仅用于生成与验证（E2E），
--      绝不参与估计，也不经 API 暴露。
--   5. 位索引约定：bit0 对应 KP1（分数概念），依此类推 bit4 对应 KP5（应用题）；
--      掌握概率数组、Q 行向量、画像位掩码一律按 KP1..KP5 顺序对齐。
--
-- 数据不变量（由加载器/测试强制，见 tests 阶段）：
--   - Q 长表「缺省为 0」：未出现的 (题, 知识点) 对视为 required=0。
--   - 禁止空知识需求题：每道题必须在 q_matrix 中至少有一行 required=1。
--   - guess / slip ∈ [0.02, 0.35]，故恒有 guess + slip < 1（0.35 + 0.35 = 0.70）。
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 知识点（5 个：分数概念 / 通分 / 分数加减 / 分数乘除 / 应用题）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS knowledge_point (
    id          INTEGER PRIMARY KEY,
    code        TEXT    NOT NULL UNIQUE,      -- KP1..KP5
    name        TEXT    NOT NULL,             -- 中文名
    description TEXT    NOT NULL DEFAULT ''
);

-- ----------------------------------------------------------------------------
-- 前置关系（简单有向无环图 DAG，边 = 学习顺序）
--   概念(KP1) → 通分(KP2) → 加减(KP3) → 应用题(KP5)
--   概念(KP1) → 乘除(KP4) → 应用题(KP5)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prerequisite (
    parent_id INTEGER NOT NULL REFERENCES knowledge_point(id),
    child_id  INTEGER NOT NULL REFERENCES knowledge_point(id),
    PRIMARY KEY (parent_id, child_id),
    CHECK (parent_id <> child_id)
);

-- ----------------------------------------------------------------------------
-- 题目（24 道合成题）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS question (
    id   INTEGER PRIMARY KEY,
    stem TEXT NOT NULL                          -- 合成题干简述
);

-- ----------------------------------------------------------------------------
-- Q 矩阵（题目 × 知识点，长表；required=1 表示该题需要掌握该知识点）
--   缺省为 0：未出现的 (题, 知识点) 对视为 required=0；每道题至少一项 required=1。
--
--   24 题 = 15 道单技能题（三份 I5，每个知识点各 3 道）+ 9 道综合题：
--     单技能：KP1 {Q1,Q6,Q11}  KP2 {Q2,Q7,Q12}  KP3 {Q3,Q8,Q13}
--             KP4 {Q4,Q9,Q14}  KP5 {Q5,Q10,Q15}
--     综合：  Q16 {KP2,KP3}      Q17 {KP1,KP3}      Q18 {KP1,KP4}
--             Q19 {KP3,KP5}      Q20 {KP4,KP5}      Q21 {KP2,KP3,KP5}
--             Q22 {KP1,KP2,KP3}  Q23 {KP1,KP3,KP4}  Q24 {KP3,KP4,KP5}
--   KP5 = 应用题建模/列式：单技能 KP5 题只考数量关系/列式并给出算术结果，
--   不把实际需要的分数加减乘除悄悄标成单技能。
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS q_matrix (
    question_id INTEGER NOT NULL REFERENCES question(id),
    kp_id       INTEGER NOT NULL REFERENCES knowledge_point(id),
    required    INTEGER NOT NULL DEFAULT 1 CHECK (required IN (0, 1)),
    PRIMARY KEY (question_id, kp_id)
);

-- ----------------------------------------------------------------------------
-- 学生（12 名；profile_id = 合成真值画像位掩码，仅用于生成/验证）
--   位 0..4 依次对应 KP1..KP5；如 0b01111(=15) 表示掌握前四、未掌握应用题
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS student (
    id         INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    profile_id INTEGER NOT NULL CHECK (profile_id BETWEEN 0 AND 31)
);

-- ----------------------------------------------------------------------------
-- X 作答矩阵（学生 × 题目，长表；is_correct ∈ {0,1}）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS x_matrix (
    student_id  INTEGER NOT NULL REFERENCES student(id),
    question_id INTEGER NOT NULL REFERENCES question(id),
    is_correct  INTEGER NOT NULL CHECK (is_correct IN (0, 1)),
    PRIMARY KEY (student_id, question_id)
);

-- ----------------------------------------------------------------------------
-- 题参（EM 校准结果：guess / slip）
--   guess = P(答对 | 未掌握全部所需知识点)
--   slip  = P(答错 | 已掌握全部所需知识点)
--   约束与 EM 数值契约一致：[0.02, 0.35]，禁止 0/1 端点；恒有 guess + slip < 1。
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS item_param (
    question_id INTEGER PRIMARY KEY REFERENCES question(id),
    guess       REAL NOT NULL CHECK (guess >= 0.02 AND guess <= 0.35),
    slip        REAL NOT NULL CHECK (slip  >= 0.02 AND slip  <= 0.35)
);

-- ----------------------------------------------------------------------------
-- 诊断结果（每名学生 × 每个知识点的掌握概率，DINA 对数后验边际）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS diagnosis (
    student_id   INTEGER NOT NULL REFERENCES student(id),
    kp_id        INTEGER NOT NULL REFERENCES knowledge_point(id),
    mastery_prob REAL    NOT NULL CHECK (mastery_prob >= 0.0 AND mastery_prob <= 1.0),
    PRIMARY KEY (student_id, kp_id)
);
