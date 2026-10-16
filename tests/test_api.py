"""src/server.py 只读 HTTP 服务的 TDD 测试（RED：契约先行，实现未完成）。

用真实 HTTP 验证 6 个 GET 接口的排序/计数/概率范围、correct_rate 重算、
无 profile_id 泄露、两名学生数据不同、GET 前后 DB 不变、404/400/405、
缺失 DB 不隐式建库。测试用临时 DB 与 port=0。
"""

import hashlib
import http.client
import json
import os
import shutil
import sqlite3
import tempfile
import threading
import unittest

from src import data_gen, seed, server


N_KP = 5
N_ITEMS = 24
N_STUDENTS = 12


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


def _file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="cdiag-api-")
        cls.db_path = os.path.join(cls.tmpdir, "diagnosis.db")
        seed.run(cls.db_path)
        cls.srv = server.make_server(cls.db_path, host="127.0.0.1", port=0)
        cls.port = cls.srv.server_address[1]
        cls.thread = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _request(self, method, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(method, path)
        resp = conn.getresponse()
        body = resp.read()
        headers = {k.lower(): v for k, v in resp.getheaders()}
        conn.close()
        return resp.status, headers, body

    def _get_json(self, path):
        status, headers, body = self._request("GET", path)
        self.assertEqual(status, 200, "GET %s → %d %r" % (path, status, body))
        self.assertEqual(headers.get("content-type"), "application/json; charset=utf-8")
        return json.loads(body.decode("utf-8"))

    def test_meta(self):
        data = self._get_json("/api/meta")
        self.assertEqual(data["student_count"], 12)
        self.assertEqual(data["question_count"], 24)
        self.assertEqual(data["profile_count"], 32)
        kps = data["knowledge_points"]
        self.assertEqual([kp["id"] for kp in kps], [1, 2, 3, 4, 5])
        self.assertEqual([kp["code"] for kp in kps],
                         ["KP1", "KP2", "KP3", "KP4", "KP5"])
        self.assertEqual(len(data["prerequisites"]), 5)
        self.assertNotIn("profile_id", json.dumps(data))

    def test_students(self):
        data = self._get_json("/api/students")
        students = data["students"]
        self.assertEqual(len(students), 12)
        self.assertEqual([s["id"] for s in students], list(range(1, 13)))
        for s in students:
            self.assertTrue(s["name"])
            self.assertNotIn("profile_id", s)

    def test_student_detail_shape(self):
        data = self._get_json("/api/students/1")
        self.assertEqual(data["student"]["id"], 1)
        mastery = data["mastery"]
        rate = data["correct_rate"]
        self.assertEqual(len(mastery), N_KP)
        self.assertEqual(len(rate), N_KP)
        for m in mastery:
            self.assertTrue(0.0 <= m["prob"] <= 1.0)
        for r in rate:
            self.assertTrue(0.0 <= r["rate"] <= 1.0)
        self.assertNotIn("profile_id", json.dumps(data))

    def test_correct_rate_recomputed(self):
        # 独立于 server 代码：直接从 DB 读 Q/X 重算 correct_rate 对照 API。
        conn = sqlite3.connect(self.db_path)
        q = _load_q(conn)
        x = _load_x(conn)
        conn.close()

        data = self._get_json("/api/students/3")
        got = [item["rate"] for item in data["correct_rate"]]
        sidx = 2  # 学生 3
        for k in range(N_KP):
            denom = sum(1 for i in range(N_ITEMS) if q[i][k] == 1)
            num = sum(1 for i in range(N_ITEMS) if q[i][k] == 1 and x[sidx][i] == 1)
            self.assertAlmostEqual(got[k], num / denom, places=12)

    def test_graph(self):
        data = self._get_json("/api/graph")
        self.assertEqual([n["id"] for n in data["nodes"]], [1, 2, 3, 4, 5])
        self.assertEqual(len(data["edges"]), 5)

    def test_items(self):
        data = self._get_json("/api/items")
        items = data["items"]
        self.assertEqual(len(items), 24)
        self.assertEqual([it["question_id"] for it in items], list(range(1, 25)))
        for it in items:
            q = it["q"]
            self.assertEqual(len(q), N_KP)
            for v in q:
                self.assertIn(v, (0, 1))
            self.assertTrue(0.02 <= it["guess"] <= 0.35)
            self.assertTrue(0.02 <= it["slip"] <= 0.35)

    def test_diagnosis_sorted_and_ranges(self):
        data = self._get_json("/api/diagnosis")
        matrix = data["matrix"]
        self.assertEqual(len(matrix), 60)
        keys = [(r["student_id"], r["kp_id"]) for r in matrix]
        self.assertEqual(keys, sorted(keys))
        for r in matrix:
            self.assertTrue(0.0 <= r["prob"] <= 1.0)
        self.assertNotIn("profile_id", json.dumps(data))

    def test_two_students_differ(self):
        a = self._get_json("/api/students/1")
        b = self._get_json("/api/students/12")
        self.assertNotEqual(a["mastery"], b["mastery"])
        self.assertNotEqual(a["correct_rate"], b["correct_rate"])

    def test_get_does_not_change_db(self):
        before = _file_hash(self.db_path)
        for path in ("/api/meta", "/api/students", "/api/students/1",
                     "/api/graph", "/api/items", "/api/diagnosis"):
            self._get_json(path)
        after = _file_hash(self.db_path)
        self.assertEqual(before, after)

    def test_non_get_method_not_allowed(self):
        for method in ("POST", "PUT", "DELETE", "PATCH"):
            status, _, body = self._request(method, "/api/meta")
            self.assertEqual(status, 405, "%s /api/meta → %d" % (method, status))
            self.assertEqual(json.loads(body.decode("utf-8"))["error"]["code"],
                             "METHOD_NOT_ALLOWED")

    def test_student_not_found(self):
        status, _, body = self._request("GET", "/api/students/999")
        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body.decode("utf-8"))["error"]["code"],
                         "NOT_FOUND")

    def test_student_bad_request(self):
        for bad in ("0", "-1", "abc", "1.5"):
            status, _, body = self._request("GET", "/api/students/" + bad)
            self.assertEqual(status, 400, "GET /api/students/%s → %d" % (bad, status))
            self.assertEqual(json.loads(body.decode("utf-8"))["error"]["code"],
                             "BAD_REQUEST")

    def test_missing_db_fails_without_creating(self):
        path = os.path.join(self.tmpdir, "missing.db")
        with self.assertRaises(FileNotFoundError):
            server.make_server(path, host="127.0.0.1", port=0)
        self.assertFalse(os.path.exists(path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
