"""seed 编排：建库 → 合成 → 校准 → 落库（stdlib，零第三方依赖）。

- 默认拒绝覆盖已有库（FileExistsError）；force=True 时显式重建。
- 调用 dina.fit(Q, X) 只收 Q/X，绝不读取合成真值 profile_id。
- 以 EM 最终 guess/slip 与后验边际写入 item_param / diagnosis，并把校准历史与收敛
  状态写入可核验本地报告 `<db_path>.report.txt`。
- 支持 `python3 -m src.seed` 与 `python3 src/seed.py` 两种启动方式。
"""

import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import data_gen, db, dina

DEFAULT_DB_PATH = "diagnosis.db"

# 24 条互不相同的简短中文合成题干，索引 i 对应 Q(i+1)，逐条与冻结 Q 矩阵对应。
# 约定（仅演示题干，不做答题/自动评分）：
#   - 单技能 KP5（Q5/Q10/Q15）只考数量关系/列式，并给出算术结果，不要求再算分数运算。
#   - 单技能 KP3（Q3/Q8/Q13）不要求自行通分（同分母或直接给出等价结果），避免暗测 KP2。
#   - 综合题体现其对应的多个知识点需求。
_QUESTION_STEMS = [
    "把一块饼平均分成 4 份，取其中 3 份，用分数表示取出的部分。",           # Q1  KP1
    "把 1/2 和 1/3 化成同分母分数（公分母取 6）。",                        # Q2  KP2
    "同分母加法：3/7 + 2/7 = ？",                                          # Q3  KP3
    "分数乘法：2/3 × 3/4 = ？",                                            # Q4  KP4
    "一条彩带长 1 米，剪去 1/4 米，还剩多少米？请列式表示数量关系（结果已给 3/4 米）。",  # Q5  KP5
    "把一条线段平均分成 5 段，取其中 2 段，用分数表示。",                   # Q6  KP1
    "把 2/3 和 3/4 化成同分母分数（公分母取 12）。",                        # Q7  KP2
    "同分母减法：5/9 − 2/9 = ？",                                          # Q8  KP3
    "分数除法：4/5 ÷ 2/3 = ？",                                            # Q9  KP4
    "一本练习册已做 1/3，剩下的占全册几分之几？请列式表示数量关系（结果已给 2/3）。",  # Q10 KP5
    "写出 3/8 的分子与分母各是多少。",                                      # Q11 KP1
    "把 1/4 和 1/6 化成同分母分数（公分母取 12）。",                        # Q12 KP2
    "异分母加法：计算 1/2 + 1/4（已知 1/2 = 2/4）。",                       # Q13 KP3
    "分数乘法：3/8 × 4/9 = ？",                                            # Q14 KP4
    "一根绳子长 3/4 米，另一根比它短 1/4 米，另一根长多少米？请列式表示数量关系（结果已给 1/2 米）。",  # Q15 KP5
    "计算：1/3 + 1/4（需先通分再相加）。",                                  # Q16 KP2,KP3
    "把 1/5 与 3/5 合并，写出合并后的分数。",                               # Q17 KP1,KP3
    "3 个 1/6 是多少？用分数表示结果。",                                    # Q18 KP1,KP4
    "一根绳子长 5/6 米，剪去 1/6 米，还剩多少米？列式并计算。",             # Q19 KP3,KP5
    "每袋装 1/4 千克，3 袋共装多少千克？列式并计算。",                      # Q20 KP4,KP5
    "把长 1/2 米与 1/3 米的两段彩带接起来，总长多少？先通分，列式并计算。",  # Q21 KP2,KP3,KP5
    "计算：1/2 + 1/3，先通分再相加，结果用分数表示。",                       # Q22 KP1,KP2,KP3
    "先算 2/3 × 3/4，再加上 1/4，写出分数结果。",                           # Q23 KP1,KP3,KP4
    "一块布长 3/4 米，裁去 1/4 米，再把剩下的分成 2 等份，每份多少米？列式并计算。",  # Q24 KP3,KP4,KP5
]


def run(db_path, *, force=False, seed=None):
    """建库并写入全部数据，返回 db_path。

    - db_path 已存在且 force=False → FileExistsError。
    - seed：合成随机种子（None 使用 data_gen.SEED）。
    """
    if os.path.exists(db_path) and not force:
        raise FileExistsError("数据库已存在：%s（用 --force 重建）" % db_path)
    if force and os.path.exists(db_path):
        os.remove(db_path)

    parent = os.path.dirname(os.path.abspath(db_path))
    if parent:
        os.makedirs(parent, exist_ok=True)

    seed_val = data_gen.SEED if seed is None else seed

    q = data_gen.build_q_matrix()
    students = data_gen.generate_students()
    true_params = data_gen.synthesize_item_params(q, seed_val)
    x = data_gen.generate_x(q, students, true_params, seed_val)

    fit_result = dina.fit(q, x)

    conn = db.connect(db_path)
    try:
        db.init_schema(conn)
        _write_static(conn, q)
        _write_students(conn, students)
        _write_x(conn, x)
        _write_fit(conn, fit_result)
        conn.commit()
    finally:
        conn.close()

    _write_report(db_path, fit_result)
    return db_path


def _question_stems(q):
    # 冻结的 24 条题干与 Q 矩阵逐条对应（索引 i 对应 Q(i+1)）。
    assert len(q) == len(_QUESTION_STEMS), "题干数量必须与题数一致"
    return list(_QUESTION_STEMS)


def _write_static(conn, q):
    conn.executemany(
        "INSERT INTO knowledge_point(id, code, name, description) VALUES (?,?,?,?)",
        data_gen.KNOWLEDGE_POINTS)
    conn.executemany(
        "INSERT INTO prerequisite(parent_id, child_id) VALUES (?,?)",
        data_gen.PREREQUISITES)
    stems = _question_stems(q)
    conn.executemany(
        "INSERT INTO question(id, stem) VALUES (?,?)",
        [(i + 1, stems[i]) for i in range(len(q))])
    # Q 长表缺省为 0：仅写 required=1 的行。
    rows = [(qid + 1, kp + 1, 1)
            for qid, qrow in enumerate(q)
            for kp, req in enumerate(qrow) if req == 1]
    conn.executemany(
        "INSERT INTO q_matrix(question_id, kp_id, required) VALUES (?,?,?)", rows)


def _write_students(conn, students):
    conn.executemany(
        "INSERT INTO student(id, name, profile_id) VALUES (?,?,?)", students)


def _write_x(conn, x):
    rows = [(sid + 1, qid + 1, c)
            for sid, xrow in enumerate(x)
            for qid, c in enumerate(xrow)]
    conn.executemany(
        "INSERT INTO x_matrix(student_id, question_id, is_correct) VALUES (?,?,?)",
        rows)


def _write_fit(conn, fit_result):
    conn.executemany(
        "INSERT INTO item_param(question_id, guess, slip) VALUES (?,?,?)",
        [(qid + 1, g, s)
         for qid, (g, s) in enumerate(zip(fit_result.guess, fit_result.slip))])
    conn.executemany(
        "INSERT INTO diagnosis(student_id, kp_id, mastery_prob) VALUES (?,?,?)",
        [(sid + 1, kp + 1, prob)
         for sid, marg in enumerate(fit_result.posterior_marginal)
         for kp, prob in enumerate(marg)])


def _write_report(db_path, fit_result):
    lines = [
        "DINA EM 校准报告（可核验）",
        "converged: %s" % fit_result.converged,
        "iterations: %d" % (len(fit_result.loglik_history) - 1),
        "loglik_history: %s" % repr(list(fit_result.loglik_history)),
        "",
    ]
    with open(db_path + ".report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        prog="src.seed",
        description="生成认知诊断演示数据库（合成数据 + DINA EM 校准）。")
    parser.add_argument("db_path", nargs="?", default=DEFAULT_DB_PATH,
                        help="SQLite 数据库路径（默认 %(default)s）")
    parser.add_argument("--force", action="store_true",
                        help="已存在时强制重建（覆盖）")
    args = parser.parse_args(argv)
    run(args.db_path, force=args.force)
    print("已生成数据库：%s" % args.db_path)


if __name__ == "__main__":
    main()
