# ER 图与数据模型

> 完整 DDL 见 [schema.sql](schema.sql)。下表给出实体、关系与设计要点。

## 实体-关系图（Mermaid）

```mermaid
erDiagram
    KNOWLEDGE_POINT ||--o{ PREREQUISITE : "前置(parent/child)"
    KNOWLEDGE_POINT ||--o{ Q_MATRIX : "被考查"
    QUESTION        ||--o{ Q_MATRIX : "考查"
    STUDENT         ||--o{ X_MATRIX : "作答"
    QUESTION        ||--o{ X_MATRIX : "被作答"
    QUESTION        ||--|| ITEM_PARAM : "题参"
    STUDENT         ||--o{ DIAGNOSIS : "诊断结果"
    KNOWLEDGE_POINT ||--o{ DIAGNOSIS : "被诊断"

    KNOWLEDGE_POINT {
        int id PK
        text code UK
        text name
        text description
    }
    PREREQUISITE {
        int parent_id PK_FK
        int child_id PK_FK
    }
    QUESTION {
        int id PK
        text stem
    }
    Q_MATRIX {
        int question_id PK_FK
        int kp_id PK_FK
        int required
    }
    STUDENT {
        int id PK
        text name
        int profile_id
    }
    X_MATRIX {
        int student_id PK_FK
        int question_id PK_FK
        int is_correct
    }
    ITEM_PARAM {
        int question_id PK_FK
        real guess
        real slip
    }
    DIAGNOSIS {
        int student_id PK_FK
        int kp_id PK_FK
        real mastery_prob
    }
```

## 实体说明

| 表 | 含义 | 关键约束 |
|---|---|---|
| `knowledge_point` | 5 个知识点 | `code` 唯一（KP1..KP5） |
| `prerequisite` | 学习顺序边（DAG） | `(parent_id, child_id)` 主键；`parent≠child` |
| `question` | 24 道合成题 | 24 条互不相同的简短中文**合成演示题干**（仅演示，不评分、不做答题）；单技能题不暗测其它知识点 |
| `q_matrix` | Q 矩阵（题目 × 知识点） | `(question_id, kp_id)` 主键；每题 ≥1 项 `required=1` |
| `student` | 12 名学生 | `profile_id ∈ [0,31]` 合成真值，仅生成/验证用 |
| `x_matrix` | X 作答矩阵（学生 × 题目） | `(student_id, question_id)` 主键 |
| `item_param` | EM 校准的 guess/slip | `guess,slip ∈ [0.02,0.35]`（禁 0/1 端点） |
| `diagnosis` | DINA 掌握概率（后验边际） | `(student_id, kp_id)` 主键 |

## 关键设计决策

1. **Q / X 矩阵采用长表**：逻辑上分别等价于「题目 × 知识点」「学生 × 题目」两个 0/1
   矩阵。Q 长表**缺省为 0**（未出现的对视为 0），每道题至少一个 `required=1`。
2. **24 题 = 15 单技能 + 9 综合**：每个知识点各有 3 道单技能题（**含仅测 KP5 的三道**），
   保证 32 种画像的理想反应向量互不相同（见下）；9 道综合题体现非补偿「And 门」。
3. **`student.profile_id` 是合成真值，仅用于生成/验证**：让 E2E 能把估计掌握概率与真值
   对照、量化局限；它不参与估计、不经 API 暴露。
4. **`diagnosis.mastery_prob` 是连续概率而非 0/1**：来自 32 画像的对数后验边际化，
   由 `fit(Q, X)` 校准产出，与「答对率」严格区分，也不由真值生成。

## 数据不变量（加载器 / 测试强制）

- I1：题与知识点使用**稳定 ID 排序**；bit0 ↔ KP1，掌握概率数组顺序 = KP1..KP5。
- I2：Q 长表缺省为 0；**禁止空知识需求题**（每道题 ≥1 项 required=1）。
- I3：`fit(Q, X, …)` 只接 Q/X 与显式数值配置，**绝不读取 `profile_id`**。
- I4：`guess, slip ∈ [0.02, 0.35]`（DDL CHECK 同步），恒有 `guess + slip < 1`。

## 前置关系（DAG）

```
KP1 分数概念 ──→ KP2 通分 ──→ KP3 分数加减 ──┐
     │                                      ├──→ KP5 应用题
     └────────→ KP4 分数乘除 ────────────────┘
```

边集合（共 5 条）：`(KP1→KP2)、(KP1→KP4)、(KP2→KP3)、(KP3→KP5)、(KP4→KP5)`。
注意：**通分不是分数乘除的前置**（真实数学中乘除无需通分）；图谱只解释学习顺序，
不裁剪 32 种推断画像。

## Q 矩阵（24 题，行 = 所需知识点集合）

| 题型 | 题号 | 所需知识点 |
|---|---|---|
| 单技能（三份 I5，每个 KP × 3） | Q1/Q6/Q11 | {KP1} 分数概念 |
| | Q2/Q7/Q12 | {KP2} 通分 |
| | Q3/Q8/Q13 | {KP3} 分数加减 |
| | Q4/Q9/Q14 | {KP4} 分数乘除 |
| | Q5/Q10/Q15 | {KP5} 应用题建模/列式 |
| 综合（9 道） | Q16 | {KP2, KP3} |
| | Q17 | {KP1, KP3} |
| | Q18 | {KP1, KP4} |
| | Q19 | {KP3, KP5} |
| | Q20 | {KP4, KP5} |
| | Q21 | {KP2, KP3, KP5} |
| | Q22 | {KP1, KP2, KP3} |
| | Q23 | {KP1, KP3, KP4} |
| | Q24 | {KP3, KP4, KP5} |
