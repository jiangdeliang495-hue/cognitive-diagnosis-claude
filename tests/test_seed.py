"""src/data_gen.py 与 src/seed.py 的 TDD 测试（RED：契约先行，实现未完成）。

覆盖：
- 确定性合成：5 知识点 / 24 题（15 单技能 + 9 综合）/ 12 学生。
- Q 矩阵冻结结构（三份 I5 + 9 综合），32 画像理想反应向量两两互异。
- 合成真值 profile_id 沿 DAG 单调；DAG 无环。
- seed 落库后按稳定 ID 读回 Q/X 与造数一致；diagnosis 60 条与重算边际一致。
- seed 确定性、默认拒绝覆盖、--force 重建。
"""

import os
import shutil
import sqlite3
import tempfile
import unittest

from src import data_gen, dina, seed


N_KP = 5
N_ITEMS = 24
N_STUDENTS = 12

# 冻结 Q 矩阵（行 Q1..Q24，列 KP1..KP5），独立于实现手写。
EXPECTED_Q = [
    [1, 0, 0, 0, 0],  # Q1  {KP1}
    [0, 1, 0, 0, 0],  # Q2  {KP2}
    [0, 0, 1, 0, 0],  # Q3  {KP3}
    [0, 0, 0, 1, 0],  # Q4  {KP4}
    [0, 0, 0, 0, 1],  # Q5  {KP5}
    [1, 0, 0, 0, 0],  # Q6
    [0, 1, 0, 0, 0],  # Q7
    [0, 0, 1, 0, 0],  # Q8
    [0, 0, 0, 1, 0],  # Q9
    [0, 0, 0, 0, 1],  # Q10
    [1, 0, 0, 0, 0],  # Q11
    [0, 1, 0, 0, 0],  # Q12
    [0, 0, 1, 0, 0],  # Q13
    [0, 0, 0, 1, 0],  # Q14
    [0, 0, 0, 0, 1],  # Q15
    [0, 1, 1, 0, 0],  # Q16 {KP2,KP3}
    [1, 0, 1, 0, 0],  # Q17 {KP1,KP3}
    [1, 0, 0, 1, 0],  # Q18 {KP1,KP4}
    [0, 0, 1, 0, 1],  # Q19 {KP3,KP5}
    [0, 0, 0, 1, 1],  # Q20 {KP4,KP5}
    [0, 1, 1, 0, 1],  # Q21 {KP2,KP3,KP5}
    [1, 1, 1, 0, 0],  # Q22 {KP1,KP2,KP3}
    [1, 0, 1, 1, 0],  # Q23 {KP1,KP3,KP4}
    [0, 0, 1, 1, 1],  # Q24 {KP3,KP4,KP5}
]

EXPECTED_PROFILES = [0, 1, 3, 3, 7, 7, 9, 11, 11, 15, 15, 31]

EXPECTED_EDGES = [(1, 2), (1, 4), (2, 3), (3, 5), (4, 5)]


def _load_q(conn):
    rows = conn.execute("SELECT question_id, kp_id, required FROM q_matrix").fetchall()
    q = [[0] * N_KP for _ in range(N_ITEMS)]
    for qid, kid, req in rows:
        q[qid - 1][kid - 1] = req
    return q


def _load_x(conn):
    rows = conn.execute(
        "SELECT student_id, question_id, is_correct FROM x_matrix"
    ).fetchall()
    x = [[0] * N_ITEMS for _ in range(N_STUDENTS)]
    for sid, qid, corr in rows:
        x[sid - 1][qid - 1] = corr
    return x


def _load_item_params(conn):
    rows = conn.execute(
        "SELECT question_id, guess, slip FROM item_param ORDER BY question_id"
    ).fetchall()
    return [r[1] for r in rows], [r[2] for r in rows]


class DataGenTests(unittest.TestCase):
    def test_q_matrix_matches_frozen_contract(self):
        self.assertEqual(data_gen.build_q_matrix(), EXPECTED_Q)

    def test_q_shape_and_binary(self):
        q = data_gen.build_q_matrix()
        self.assertEqual(len(q), N_ITEMS)
        for row in q:
            self.assertEqual(len(row), N_KP)
            for v in row:
                self.assertIn(v, (0, 1))

    def test_q_three_i5_plus_nine_composite(self):
        q = data_gen.build_q_matrix()
        single = [row for row in q if sum(row) == 1]
        composite = [row for row in q if sum(row) >= 2]
        self.assertEqual(len(single), 15)
        self.assertEqual(len(composite), 9)
        for k in range(N_KP):
            self.assertEqual(sum(1 for row in single if row[k] == 1), 3)

    def test_no_empty_requirement_question(self):
        for row in data_gen.build_q_matrix():
            self.assertGreater(sum(row), 0)

    def test_32_profiles_ideal_response_distinct(self):
        q = data_gen.build_q_matrix()
        seen = set()
        for profile in range(32):
            vec = tuple(
                1 if all((profile >> k) & 1 for k in range(N_KP) if q[i][k] == 1) else 0
                for i in range(N_ITEMS)
            )
            seen.add(vec)
        self.assertEqual(len(seen), 32)

    def test_students_profiles_frozen(self):
        profiles = [p for (_, _, p) in data_gen.generate_students()]
        self.assertEqual(profiles, EXPECTED_PROFILES)

    def test_students_ids_and_names(self):
        students = data_gen.generate_students()
        self.assertEqual(len(students), N_STUDENTS)
        for i, (sid, name, profile) in enumerate(students):
            self.assertEqual(sid, i + 1)
            self.assertTrue(name)
            self.assertTrue(0 <= profile <= 31)

    def test_profiles_downward_closed_along_dag(self):
        students = data_gen.generate_students()
        for (_, _, profile) in students:
            for (parent, child) in data_gen.PREREQUISITES:
                if (profile >> (child - 1)) & 1:
                    self.assertTrue((profile >> (parent - 1)) & 1,
                                    "profile=%d 违反边 %d→%d" % (profile, parent, child))

    def test_prerequisites_frozen_and_acyclic(self):
        self.assertEqual(sorted(data_gen.PREREQUISITES), sorted(EXPECTED_EDGES))
        edges = list(data_gen.PREREQUISITES)
        nodes = set()
        for a, b in edges:
            nodes.add(a)
            nodes.add(b)
        indeg = {n: 0 for n in nodes}
        adj = {n: [] for n in nodes}
        for a, b in edges:
            adj[a].append(b)
            indeg[b] += 1
        queue = [n for n in nodes if indeg[n] == 0]
        seen = 0
        while queue:
            n = queue.pop()
            seen += 1
            for m in adj[n]:
                indeg[m] -= 1
                if indeg[m] == 0:
                    queue.append(m)
        self.assertEqual(seen, len(nodes))

    def test_generation_deterministic(self):
        q1 = data_gen.build_q_matrix()
        s1 = data_gen.generate_students()
        p1 = data_gen.synthesize_item_params(q1)
        x1 = data_gen.generate_x(q1, s1, p1)

        q2 = data_gen.build_q_matrix()
        s2 = data_gen.generate_students()
        p2 = data_gen.synthesize_item_params(q2)
        x2 = data_gen.generate_x(q2, s2, p2)

        self.assertEqual(q1, q2)
        self.assertEqual(s1, s2)
        self.assertEqual(p1, p2)
        self.assertEqual(x1, x2)

    def test_x_shape_and_binary(self):
        q = data_gen.build_q_matrix()
        s = data_gen.generate_students()
        p = data_gen.synthesize_item_params(q)
        x = data_gen.generate_x(q, s, p)
        self.assertEqual(len(x), N_STUDENTS)
        for row in x:
            self.assertEqual(len(row), N_ITEMS)
            for v in row:
                self.assertIn(v, (0, 1))

    def test_synthesized_item_params_in_bounds(self):
        q = data_gen.build_q_matrix()
        p = data_gen.synthesize_item_params(q)
        self.assertEqual(len(p), N_ITEMS)
        for g, s in p:
            self.assertTrue(0.02 <= g <= 0.35)
            self.assertTrue(0.02 <= s <= 0.35)


class SeedTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="cdiag-seed-")
        self.db_path = os.path.join(self.tmpdir, "diagnosis.db")
        self.addCleanup(shutil.rmtree, self.tmpdir, True)

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def test_seed_creates_expected_counts(self):
        seed.run(self.db_path)
        conn = self._conn()
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM knowledge_point").fetchone()[0], N_KP)
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM question").fetchone()[0], N_ITEMS)
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM student").fetchone()[0], N_STUDENTS)
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM prerequisite").fetchone()[0], 5)
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM diagnosis").fetchone()[0], 60)
        conn.close()

    def test_seed_q_x_match_generation(self):
        seed.run(self.db_path)
        conn = self._conn()
        q_db = _load_q(conn)
        x_db = _load_x(conn)
        conn.close()

        q = data_gen.build_q_matrix()
        students = data_gen.generate_students()
        p = data_gen.synthesize_item_params(q)
        x = data_gen.generate_x(q, students, p)

        self.assertEqual(q_db, q)
        self.assertEqual(x_db, x)

    def test_question_stems_distinct_descriptive_and_isolated(self):
        # 24 条互不相同的简短中文合成题干，逐条对应冻结 Q。
        # 单技能题不得暗测其它知识点：KP5 只考列式并给出算术结果；KP3 不要求自行通分。
        seed.run(self.db_path)
        conn = self._conn()
        stems = [r[0] for r in conn.execute(
            "SELECT stem FROM question ORDER BY id").fetchall()]
        conn.close()

        self.assertEqual(len(stems), N_ITEMS)
        self.assertEqual(len(set(stems)), N_ITEMS, "题干必须 24 条互不相同")
        for s in stems:
            self.assertTrue(s and s == s.strip(), "题干不得为空或含首尾空白")
            self.assertTrue(1 < len(s) <= 60, "题干应简短（≤60 字）：%r" % s)

        # 单技能 KP5（Q5/Q10/Q15）：只考数量关系/列式并给出算术结果，不要求计算。
        for idx in (4, 9, 14):
            self.assertIn("列式", stems[idx])
            self.assertIn("结果已给", stems[idx])
            self.assertNotIn("计算", stems[idx])

        # 单技能 KP3（Q3/Q8/Q13）：不得要求自行通分（避免暗测 KP2）。
        for idx in (2, 7, 12):
            self.assertNotIn("通分", stems[idx])

    def test_seed_prerequisites_match(self):
        seed.run(self.db_path)
        conn = self._conn()
        edges = conn.execute(
            "SELECT parent_id, child_id FROM prerequisite ORDER BY parent_id, child_id"
        ).fetchall()
        conn.close()
        self.assertEqual(edges, sorted(EXPECTED_EDGES))

    def test_seed_diagnosis_60_sorted_and_matches_recomputed(self):
        seed.run(self.db_path)
        conn = self._conn()
        q = _load_q(conn)
        x = _load_x(conn)
        g, s = _load_item_params(conn)
        rows = conn.execute(
            "SELECT student_id, kp_id, mastery_prob FROM diagnosis "
            "ORDER BY student_id, kp_id"
        ).fetchall()
        conn.close()

        self.assertEqual(len(rows), 60)
        marg, _ = dina.posterior_marginal(q, x, g, s)
        for (sid, kid, prob) in rows:
            self.assertTrue(0.0 <= prob <= 1.0)
            self.assertAlmostEqual(prob, marg[sid - 1][kid - 1], places=8)

    def test_seed_item_params_in_bounds(self):
        seed.run(self.db_path)
        conn = self._conn()
        g, s = _load_item_params(conn)
        conn.close()
        for v in g + s:
            self.assertTrue(0.02 <= v <= 0.35)

    def test_seed_refit_matches_stored_params_and_diagnosis(self):
        # 用从 SQLite 读回的 Q/X 重新跑一遍真 EM（冻结默认配置），逐题/逐格比对落库
        # guess/slip 与 diagnosis，排除 seed 直接用造数真值题参而非校准结果的可能。
        seed.run(self.db_path)
        conn = self._conn()
        q = _load_q(conn)
        x = _load_x(conn)
        g_stored, s_stored = _load_item_params(conn)
        rows = conn.execute(
            "SELECT student_id, kp_id, mastery_prob FROM diagnosis "
            "ORDER BY student_id, kp_id"
        ).fetchall()
        conn.close()

        res = dina.fit(q, x)  # 冻结默认配置，与 seed 内部一致
        for i in range(N_ITEMS):
            self.assertAlmostEqual(res.guess[i], g_stored[i], places=10)
            self.assertAlmostEqual(res.slip[i], s_stored[i], places=10)
        self.assertEqual(len(rows), 60)
        for (sid, kid, prob) in rows:
            self.assertAlmostEqual(prob, res.posterior_marginal[sid - 1][kid - 1],
                                   places=9)

    def test_seed_x_complete_288_records(self):
        # X 必须完整覆盖 12×24=288 条 (student_id, question_id)，缺失不得当作 0。
        seed.run(self.db_path)
        conn = self._conn()
        cnt = conn.execute("SELECT COUNT(*) FROM x_matrix").fetchone()[0]
        self.assertEqual(cnt, N_STUDENTS * N_ITEMS)
        pairs = set(conn.execute(
            "SELECT student_id, question_id FROM x_matrix"
        ).fetchall())
        conn.close()
        self.assertEqual(len(pairs), N_STUDENTS * N_ITEMS)
        self.assertEqual(pairs, {(s, q) for s in range(1, N_STUDENTS + 1)
                                 for q in range(1, N_ITEMS + 1)})

    def test_seed_deterministic(self):
        seed.run(self.db_path)
        path2 = os.path.join(self.tmpdir, "diagnosis2.db")
        seed.run(path2)
        self.assertEqual(_dump(self.db_path), _dump(path2))

    def test_seed_refuses_overwrite(self):
        seed.run(self.db_path)
        with self.assertRaises(FileExistsError):
            seed.run(self.db_path)

    def test_seed_force_rebuilds(self):
        seed.run(self.db_path)
        seed.run(self.db_path, force=True)  # 不抛异常


def _dump(path):
    conn = sqlite3.connect(path)
    tables = ["knowledge_point", "prerequisite", "question", "q_matrix",
              "student", "x_matrix", "item_param", "diagnosis"]
    out = {}
    for t in tables:
        out[t] = conn.execute("SELECT * FROM %s ORDER BY rowid" % t).fetchall()
    conn.close()
    return out


if __name__ == "__main__":
    unittest.main(verbosity=2)
