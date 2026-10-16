"""src/db.py 建库与 schema 约束的 TDD 测试（RED：契约先行，实现未完成）。

按 docs/schema.sql 冻结的数据不变量编写：
- 建齐 8 张表。
- 外键引用完整性（q_matrix/x_matrix/item_param/diagnosis 均 FK 到主表）。
- x_matrix.is_correct ∈ {0,1}（二元）。
- item_param.guess/slip ∈ [0.02,0.35]。
- student.profile_id ∈ [0,31]。
- prerequisite 禁止自环（parent <> child）。
"""

import sqlite3
import unittest

from src import db


class SchemaCreationTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        db.init_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def _tables(self):
        rows = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        return {r["name"] for r in rows}

    def _seed_kp(self):
        self.conn.execute(
            "INSERT INTO knowledge_point(id, code, name) VALUES (1, 'KP1', '分数概念')"
        )
        self.conn.execute(
            "INSERT INTO knowledge_point(id, code, name) VALUES (2, 'KP2', '通分')"
        )

    def _seed_minimal(self):
        self._seed_kp()
        self.conn.execute("INSERT INTO question(id, stem) VALUES (1, '题')")
        self.conn.execute(
            "INSERT INTO student(id, name, profile_id) VALUES (1, '学生01', 0)"
        )

    def test_creates_all_tables(self):
        self.assertEqual(self._tables(), {
            "knowledge_point", "prerequisite", "question", "q_matrix",
            "student", "x_matrix", "item_param", "diagnosis",
        })

    def test_foreign_keys_enforced(self):
        self._seed_kp()
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO q_matrix(question_id, kp_id, required) VALUES (999, 1, 1)"
            )

    def test_x_matrix_binary(self):
        self._seed_minimal()
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO x_matrix(student_id, question_id, is_correct) VALUES (1, 1, 2)"
            )

    def test_item_param_bounds(self):
        self._seed_minimal()
        # guess 越上界 / slip 越下界 均拒绝
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO item_param(question_id, guess, slip) VALUES (1, 0.50, 0.10)"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO item_param(question_id, guess, slip) VALUES (1, 0.20, 0.01)"
            )

    def test_student_profile_bounds(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO student(id, name, profile_id) VALUES (1, '学生01', 32)"
            )

    def test_prerequisite_no_self_loop(self):
        self._seed_kp()
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO prerequisite(parent_id, child_id) VALUES (1, 1)"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
