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

_KP_TASK = {
    1: "分数概念：理解意义与表示",
    2: "通分：异分母通分",
    3: "分数加减：同分母/通分后加减",
    4: "分数乘除：乘法与除法运算",
    5: "应用题：数量关系列式并求算术结果",
}
_KP_SHORT = {
    1: "分数概念", 2: "通分", 3: "分数加减", 4: "分数乘除", 5: "应用题建模/列式",
}


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
    stems = []
    for row in q:
        kps = [k + 1 for k in range(len(row)) if row[k] == 1]
        if len(kps) == 1:
            stems.append(_KP_TASK[kps[0]])
        else:
            stems.append("综合：" + "、".join(_KP_SHORT[k] for k in kps))
    return stems


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
