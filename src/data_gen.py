"""合成数据生成（TDD RED 阶段：接口桩，逻辑未实现）。

按 docs/superpowers/specs/2026-10-16-cognitive-diagnosis-mvp-design.md §5 生成确定性
合成数据：
- 5 知识点 / 5 条前置边（DAG）/ 24 题（15 单技能 + 9 综合）/ 12 名学生。
- 24 题 = 三份 I5（每个 KP × 3，含仅测 KP5 的三道）+ 9 道综合题，保证 32 种画像的
  理想反应向量两两互异。
- 合成真值 profile_id 沿 DAG 单调（下闭集），只用于生成与验证；fit(Q, X, …) 绝不读取
  profile_id。
- 固定随机种子 → 可复现。
"""

# 规模常量
N_KNOWLEDGE_POINTS = 5
N_QUESTIONS = 24
N_STUDENTS = 12
N_PROFILES = 32
SEED = 20261016

# 知识点 (id, code, name, description)
KNOWLEDGE_POINTS = [
    (1, "KP1", "分数概念", ""),
    (2, "KP2", "通分", ""),
    (3, "KP3", "分数加减", ""),
    (4, "KP4", "分数乘除", ""),
    (5, "KP5", "应用题建模/列式", ""),
]

# 前置边（parent_id, child_id），共 5 条，构成 DAG
PREREQUISITES = [
    (1, 2),   # KP1 → KP2
    (1, 4),   # KP1 → KP4
    (2, 3),   # KP2 → KP3
    (3, 5),   # KP3 → KP5
    (4, 5),   # KP4 → KP5
]

# 合成真值画像（profile_id 位掩码，bit0=KP1 … bit4=KP5），沿 DAG 单调
STUDENT_PROFILES = [0, 1, 3, 3, 7, 7, 9, 11, 11, 15, 15, 31]


def build_q_matrix():
    """返回 Q 矩阵：形状 (24, 5)，0/1，行序 = Q1..Q24，列序 = KP1..KP5。"""
    raise NotImplementedError


def generate_students():
    """返回 12 名学生 (id, name, profile_id)；id 1..12，name 形如「学生01」。

    profile_id 为合成真值（仅生成/验证用），沿 DAG 单调（下闭集）。
    """
    raise NotImplementedError


def synthesize_item_params(q_matrix, seed=SEED):
    """按固定种子合成每题真实 guess/slip（区间 [0.02,0.35]，多知识点题 guess 更小）。

    返回 [(guess_j, slip_j), ...]，长度 = 题数。仅供抽样 X，不写入 item_param 表。
    """
    raise NotImplementedError


def generate_x(q_matrix, students, item_params, seed=SEED):
    """按 DINA 观测模型抽样作答矩阵 X。

    X[s][i] ~ Bernoulli((1-slip_i) 若 η=1 否则 guess_i)，η 为理想作答（And 门）。
    返回形状 (n_students, n_items) 的 0/1 矩阵。
    """
    raise NotImplementedError
