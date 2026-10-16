"""src/server.py 的 LLM 学习建议接口 TDD 测试（RED：契约先行，实现未完成）。

mock 供应商 transport + 真实本机 HTTP（需本机端口绑定，沙箱外运行）：
- 状态接口只返回非敏感字段；成功建议使用当前学生的数据库快照（两名学生提示词不同）、
  DB 文件前后 hash 不变；严格 {} 请求体；405/400/404/413；Origin/Host 拒绝且不调用供应商；
  无宽泛 CORS；上游错误映射且不回显上游 body/异常 repr/密钥；未配置 503；
  并发付费请求 BUSY 429；chunked 与歧义 Content-Length 拒绝；内容型安全（只 200 响应）。

契约见 docs/LLM_SUGGESTIONS.md。RED 来自待实现的接口与 src/advice 模块缺失。
"""

import hashlib
import http.client
import json
import os
import shutil
import socket
import sqlite3
import tempfile
import threading
import time
import unittest
from unittest import mock

from src import seed, server

N_KP = 5
N_ITEMS = 24
N_STUDENTS = 12
TEST_KEY = "test-key-9f3k-not-real"

KP_NAMES = {1: "分数概念", 2: "通分", 3: "分数加减", 4: "分数乘除", 5: "应用题建模/列式"}


def _file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_q(conn):
    rows = conn.execute("SELECT question_id, kp_id, required FROM q_matrix").fetchall()
    q = [[0] * N_KP for _ in range(N_ITEMS)]
    for qid, kid, req in rows:
        q[qid - 1][kid - 1] = req
    return q


def _load_x(conn):
    rows = conn.execute(
        "SELECT student_id, question_id, is_correct FROM x_matrix").fetchall()
    x = [[0] * N_ITEMS for _ in range(N_STUDENTS)]
    for sid, qid, corr in rows:
        x[sid - 1][qid - 1] = corr
    return x


def _correct_rate(conn, sid):
    q = _load_q(conn)
    x = _load_x(conn)
    rates = []
    for k in range(N_KP):
        denom = sum(1 for i in range(N_ITEMS) if q[i][k] == 1)
        num = sum(1 for i in range(N_ITEMS) if q[i][k] == 1 and x[sid - 1][i] == 1)
        rates.append(num / denom)
    return rates


def _valid_advice():
    return {
        "summary": "本周重点巩固通分与分数加减。",
        "priorities": [
            {"kp_id": 2, "reason": "掌握概率较低，是加减的前置。",
             "actions": ["每天练 5 道异分母通分题", "用最小公倍数检查分母"],
             "check": "不看答案独立完成 3 题并全对"},
            {"kp_id": 3, "reason": "受通分拖累，正确率不足。",
             "actions": ["同分母加减各 5 题"],
             "check": "限时 10 分钟正确率 ≥ 80%"},
        ],
    }


def _ok_transport(content=None, finish="stop"):
    def transport(url, data, req_headers, socket_timeout, deadline):
        transport.calls.append({
            "url": url, "payload": json.loads(data.decode("utf-8")),
            "headers": req_headers})
        body = {
            "id": "chatcmpl-req-1",
            "choices": [{
                "message": {
                    "content": json.dumps(_valid_advice(), ensure_ascii=False)
                    if content is None else content,
                    "reasoning_content": "内部思考过程，绝不应回传",
                },
                "finish_reason": finish,
            }],
        }
        return 200, {"content-type": "application/json"}, json.dumps(body).encode("utf-8")

    transport.calls = []
    return transport


def _status_transport(status, body=b""):
    def transport(url, data, headers, socket_timeout, deadline):
        transport.calls.append(1)
        return status, {}, body

    transport.calls = []
    return transport


def _raising_transport(exc):
    def transport(url, data, headers, socket_timeout, deadline):
        transport.calls.append(1)
        raise exc

    transport.calls = []
    return transport


class AdviceApiTests(unittest.TestCase):
    """已配置服务器（mock transport）+ 真实本机 HTTP。"""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="cdiag-advice-")
        cls.db_path = os.path.join(cls.tmpdir, "diagnosis.db")
        seed.run(cls.db_path)
        cls.transport = _ok_transport()
        cls.srv = server.make_server(
            cls.db_path, host="127.0.0.1", port=0,
            llm={"key": TEST_KEY, "transport": cls.transport})
        cls.port = cls.srv.server_address[1]
        cls.thread = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def setUp(self):
        # 共享 transport 的调用记录每个测试独立清零（unittest 按字母序运行，
        # 先前测试不得污染后续成功/状态/两学生对比的绝对次数断言）
        self.transport.calls.clear()

    def _request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request(method, path, body=body, headers=headers or {})
        resp = conn.getresponse()
        raw = resp.read()
        hdrs = {k.lower(): v for k, v in resp.getheaders()}
        conn.close()
        return resp.status, hdrs, raw

    def _advice(self, sid, body=b"{}", headers=None):
        h = {"Content-Type": "application/json"}
        if headers:
            h.update(headers)
        return self._request("POST", "/api/students/%d/advice" % sid, body=body,
                             headers=h)

    # ---- 状态接口 ----

    def test_llm_status_configured_non_sensitive(self):
        status, hdrs, raw = self._request("GET", "/api/llm/status")
        self.assertEqual(status, 200)
        data = json.loads(raw.decode("utf-8"))
        self.assertEqual(data, {"configured": True, "provider": "deepseek",
                                "model": "deepseek-v4-pro", "reasoning_effort": "max"})
        self.assertNotIn(TEST_KEY, raw.decode("utf-8"))
        self.assertEqual(len(self.transport.calls), 0)  # 状态接口不调用供应商

    # ---- 成功路径与快照 ----

    def test_advice_success_uses_student_snapshot(self):
        before = _file_hash(self.db_path)
        status, hdrs, raw = self._advice(3)
        self.assertEqual(status, 200, raw.decode("utf-8"))
        data = json.loads(raw.decode("utf-8"))
        self.assertEqual(data["student_id"], 3)
        self.assertEqual(data["source"], "llm")
        self.assertEqual(data["provider"], "deepseek")
        self.assertEqual(data["model"], "deepseek-v4-pro")
        self.assertEqual(data["reasoning_effort"], "max")
        self.assertEqual(data["request_id"], "chatcmpl-req-1")
        self.assertEqual(data["advice"]["summary"], _valid_advice()["summary"])
        self.assertEqual(len(data["advice"]["priorities"]), 2)
        self.assertNotIn(TEST_KEY, raw.decode("utf-8"))
        self.assertNotIn("内部思考过程", raw.decode("utf-8"))

        # 供应商载荷与提示词：当前学生 3 的库快照
        self.assertEqual(len(self.transport.calls), 1)
        call = self.transport.calls[0]
        self.assertEqual(call["url"], "https://api.deepseek.com/chat/completions")
        payload = call["payload"]
        self.assertEqual(payload["model"], "deepseek-v4-pro")
        self.assertEqual(payload["thinking"], {"type": "enabled"})
        self.assertEqual(payload["reasoning_effort"], "max")
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertIs(payload["stream"], False)
        self.assertNotIn("temperature", payload)
        prompt = payload["messages"][0]["content"]

        conn = sqlite3.connect(self.db_path)
        probs = dict(conn.execute(
            "SELECT kp_id, mastery_prob FROM diagnosis WHERE student_id=3").fetchall())
        conn.close()
        for kp in range(1, N_KP + 1):
            self.assertIn("%.3f" % probs[kp], prompt, "提示词缺 KP%d 掌握概率快照" % kp)
            self.assertIn(KP_NAMES[kp], prompt)
        self.assertIn("答对率", prompt)
        self.assertIn("前置", prompt)
        self.assertIn("小样本", prompt)
        # 不泄露真值/其他学生/密钥
        self.assertNotIn("profile_id", prompt)
        for other in ("学生01", "学生02", "学生04", "学生12"):
            self.assertNotIn(other, prompt)
        self.assertNotIn(TEST_KEY, prompt)

        self.assertEqual(_file_hash(self.db_path), before)  # DB 前后不变

    def test_advice_prompt_differs_between_students(self):
        self._advice(1)
        self._advice(2)
        self.assertEqual(len(self.transport.calls), 2)
        p1 = self.transport.calls[0]["payload"]["messages"][0]["content"]
        p2 = self.transport.calls[1]["payload"]["messages"][0]["content"]
        self.assertNotEqual(p1, p2)

    # ---- 请求体与路由 ----

    def test_advice_requires_strict_empty_json(self):
        n = len(self.transport.calls)
        for body in (b'{"prob": 0.5}', b"[]", b'"str"', b"", b"null"):
            status, _, raw = self._advice(3, body=body)
            self.assertEqual(status, 400, "%r → %d" % (body, status))
            self.assertEqual(json.loads(raw.decode("utf-8"))["error"]["code"],
                             "BAD_REQUEST")
        self.assertEqual(len(self.transport.calls), n)  # 供应商零调用

    def test_advice_requires_json_content_type(self):
        n = len(self.transport.calls)
        status, _, raw = self._request(
            "POST", "/api/students/3/advice", body=b"{}",
            headers={"Content-Type": "text/plain"})
        self.assertEqual(status, 400)
        self.assertEqual(len(self.transport.calls), n)

    def test_advice_methods(self):
        n = len(self.transport.calls)
        status, _, raw = self._request("GET", "/api/students/3/advice")
        self.assertEqual(status, 405)
        self.assertEqual(json.loads(raw.decode("utf-8"))["error"]["code"],
                         "METHOD_NOT_ALLOWED")
        status, _, _ = self._request("POST", "/api/meta", body=b"{}")
        self.assertEqual(status, 405)  # 原 GET 接口的 POST 仍 405
        self.assertEqual(len(self.transport.calls), n)

    def test_advice_bad_id_and_not_found(self):
        n = len(self.transport.calls)
        for bad in ("0", "-1", "abc", "1.5"):
            status, _, raw = self._request(
                "POST", "/api/students/%s/advice" % bad, body=b"{}",
                headers={"Content-Type": "application/json"})
            self.assertEqual(status, 400, bad)
        status, _, raw = self._request(
            "POST", "/api/students/999/advice", body=b"{}",
            headers={"Content-Type": "application/json"})
        self.assertEqual(status, 404)
        self.assertEqual(len(self.transport.calls), n)

    def test_advice_oversized_body_413(self):
        n = len(self.transport.calls)
        body = b'{"pad":"' + b"a" * 5000 + b'"}'
        status, _, raw = self._advice(3, body=body)
        self.assertEqual(status, 413)
        self.assertEqual(json.loads(raw.decode("utf-8"))["error"]["code"],
                         "REQUEST_TOO_LARGE")
        self.assertEqual(len(self.transport.calls), n)

    # ---- Origin / Host / CORS ----

    def test_advice_rejects_cross_origin_and_null_origin(self):
        n = len(self.transport.calls)
        for origin in ("http://evil.example", "https://other.example", "null"):
            status, _, raw = self._advice(
                3, headers={"Origin": origin})
            self.assertEqual(status, 403, origin)
            self.assertEqual(json.loads(raw.decode("utf-8"))["error"]["code"],
                             "ORIGIN_FORBIDDEN")
        self.assertEqual(len(self.transport.calls), n)  # 不调用供应商

    def test_advice_same_origin_origin_allowed_others_rejected(self):
        # 正确同源 Origin（含实际绑定端口）必须有成功正例——否则「拒绝一切 Origin」的
        # 伪实现也会全绿，浏览器反而不可用。
        status, _, raw = self._advice(
            3, headers={"Origin": "http://127.0.0.1:%d" % self.port})
        self.assertEqual(status, 200, raw.decode("utf-8"))
        # 同 hostname 异端口 / 恶意后缀域名 / 异源 → 403 且零供应商调用
        n = len(self.transport.calls)
        for origin in ("http://127.0.0.1:9999",
                       "http://127.0.0.1.evil.example",
                       "https://evil.example",
                       "http://evil-127.0.0.1.example"):
            status, _, raw = self._advice(3, headers={"Origin": origin})
            self.assertEqual(status, 403, origin)
            self.assertEqual(json.loads(raw.decode("utf-8"))["error"]["code"],
                             "ORIGIN_FORBIDDEN")
        self.assertEqual(len(self.transport.calls), n)

    def test_advice_rejects_untrusted_host(self):
        n = len(self.transport.calls)
        status, _, raw = self._advice(3, headers={"Host": "evil.example"})
        self.assertEqual(status, 403)
        self.assertEqual(json.loads(raw.decode("utf-8"))["error"]["code"],
                         "HOST_FORBIDDEN")
        self.assertEqual(len(self.transport.calls), n)

    def test_advice_no_cors_headers(self):
        status, hdrs, _ = self._advice(3)
        self.assertEqual(status, 200)
        self.assertNotIn("access-control-allow-origin", hdrs)

    # ---- 结构校验（mock 返回坏建议）----

    def test_advice_rejects_bad_llm_content(self):
        n = len(self.transport.calls)
        cases = [
            "",                                            # 空 content
            "not json",                                    # 非 JSON
            json.dumps({"summary": "x", "priorities": []}),  # 空 priorities
            json.dumps({"summary": "x", "priorities": [
                {"kp_id": 9, "reason": "r", "actions": ["a"], "check": "c"}]}),
            json.dumps({"summary": "x", "priorities": [
                {"kp_id": 2, "reason": "r", "actions": ["a"], "check": "c"},
                {"kp_id": 2, "reason": "r", "actions": ["a"], "check": "c"}]}),
            json.dumps({"summary": "长" * 400, "priorities": [
                {"kp_id": 1, "reason": "r", "actions": ["a"], "check": "c"}]}),
        ]
        for content in cases:
            srv = server.make_server(
                self.db_path, host="127.0.0.1", port=0,
                llm={"key": TEST_KEY, "transport": _ok_transport(content=content)})
            t = threading.Thread(target=srv.serve_forever, daemon=True)
            t.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1],
                                                  timeout=10)
                conn.request("POST", "/api/students/3/advice", body=b"{}",
                             headers={"Content-Type": "application/json"})
                resp = conn.getresponse()
                raw = resp.read()
                conn.close()
                self.assertEqual(resp.status, 502, "%r → %d" % (content[:40], resp.status))
                self.assertEqual(json.loads(raw.decode("utf-8"))["error"]["code"],
                                 "BAD_RESPONSE")
            finally:
                srv.shutdown()
                srv.server_close()
        self.assertEqual(len(self.transport.calls), n)

    def test_advice_strips_unknown_model_fields(self):
        # 模型 JSON 的未知字段必须剥离或拒绝，不能原样带出到响应
        content = json.dumps({
            "summary": "s",
            "priorities": [
                {"kp_id": 1, "reason": "r", "actions": ["a"], "check": "c", "hint": "x"}],
            "extra": "e", "chain_of_thought": "内部思考",
        }, ensure_ascii=False)
        srv = server.make_server(
            self.db_path, host="127.0.0.1", port=0,
            llm={"key": TEST_KEY, "transport": _ok_transport(content=content)})
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1],
                                              timeout=10)
            conn.request("POST", "/api/students/3/advice", body=b"{}",
                         headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            raw = resp.read()
            conn.close()
            self.assertEqual(resp.status, 200)
            data = json.loads(raw.decode("utf-8"))
            self.assertEqual(sorted(data["advice"].keys()), ["priorities", "summary"])
            self.assertEqual(sorted(data["advice"]["priorities"][0].keys()),
                             ["actions", "check", "kp_id", "reason"])
            self.assertNotIn("chain_of_thought", raw.decode("utf-8"))
            self.assertNotIn("hint", raw.decode("utf-8"))
        finally:
            srv.shutdown()
            srv.server_close()

    def test_advice_rejects_truncated_finish_reason(self):
        srv = server.make_server(
            self.db_path, host="127.0.0.1", port=0,
            llm={"key": TEST_KEY, "transport": _ok_transport(finish="length")})
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1],
                                              timeout=10)
            conn.request("POST", "/api/students/3/advice", body=b"{}",
                         headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            raw = resp.read()
            conn.close()
            self.assertEqual(resp.status, 502)
            self.assertEqual(json.loads(raw.decode("utf-8"))["error"]["code"],
                             "BAD_RESPONSE")
        finally:
            srv.shutdown()
            srv.server_close()

    # ---- 上游错误映射（不回显）----

    def test_advice_upstream_error_mapping_and_no_leak(self):
        cases = [
            (401, 502, "LLM_UNAUTHORIZED"),
            (402, 502, "LLM_PAYMENT_REQUIRED"),
            (429, 503, "LLM_RATE_LIMITED"),
            (500, 502, "LLM_UPSTREAM_ERROR"),
        ]
        for upstream, expected_http, code in cases:
            srv = server.make_server(
                self.db_path, host="127.0.0.1", port=0,
                llm={"key": TEST_KEY,
                     "transport": _status_transport(
                         upstream, b'{"upstream":"secret-leak-body"}')})
            t = threading.Thread(target=srv.serve_forever, daemon=True)
            t.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1],
                                                  timeout=10)
                conn.request("POST", "/api/students/3/advice", body=b"{}",
                             headers={"Content-Type": "application/json"})
                resp = conn.getresponse()
                raw = resp.read()
                conn.close()
                self.assertEqual(resp.status, expected_http, code)
                text = raw.decode("utf-8")
                err = json.loads(text)["error"]
                self.assertEqual(err["code"], code)
                self.assertNotIn("secret-leak-body", text)
                self.assertNotIn(TEST_KEY, text)
                self.assertTrue(any("一" <= ch <= "鿿" for ch in err["message"]))
            finally:
                srv.shutdown()
                srv.server_close()

    def test_advice_network_and_timeout_mapping(self):
        import socket as _sock
        import urllib.error
        cases = [
            (_raising_transport(_sock.timeout("idle")), 504, "TIMEOUT"),
            (_raising_transport(urllib.error.URLError("boom")), 502, "NETWORK"),
        ]
        for transport, expected_http, code in cases:
            srv = server.make_server(
                self.db_path, host="127.0.0.1", port=0,
                llm={"key": TEST_KEY, "transport": transport})
            t = threading.Thread(target=srv.serve_forever, daemon=True)
            t.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1],
                                                  timeout=10)
                conn.request("POST", "/api/students/3/advice", body=b"{}",
                             headers={"Content-Type": "application/json"})
                resp = conn.getresponse()
                raw = resp.read()
                conn.close()
                self.assertEqual(resp.status, expected_http, code)
                self.assertEqual(json.loads(raw.decode("utf-8"))["error"]["code"], code)
            finally:
                srv.shutdown()
                srv.server_close()

    # ---- 并发限制 ----

    def test_advice_concurrent_limit_busy_429(self):
        entered = threading.Event()
        release = threading.Event()

        def blocking(url, data, headers, socket_timeout, deadline):
            blocking.calls.append(1)
            entered.set()
            release.wait(timeout=15)
            body = json.dumps({
                "id": "chatcmpl-busy",
                "choices": [{"message": {
                    "content": json.dumps(_valid_advice(), ensure_ascii=False),
                    "reasoning_content": ""}, "finish_reason": "stop"}]})
            return 200, {}, body.encode("utf-8")

        blocking.calls = []
        srv = server.make_server(
            self.db_path, host="127.0.0.1", port=0,
            llm={"key": TEST_KEY, "transport": blocking})
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        results = {}

        def post(sid):
            conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1],
                                              timeout=10)
            conn.request("POST", "/api/students/%d/advice" % sid, body=b"{}",
                         headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            results[sid] = (resp.status, resp.read())
            conn.close()

        try:
            th = threading.Thread(target=post, args=(1,))
            th.start()
            self.assertTrue(entered.wait(timeout=10))     # 第一个请求已占用
            post(2)                                        # 第二个应被 BUSY 拒绝
            release.set()
            th.join(timeout=15)
            self.assertEqual(results[1][0], 200)
            status2 = results[2][0]
            self.assertEqual(status2, 429)
            self.assertEqual(json.loads(results[2][1].decode("utf-8"))["error"]["code"],
                             "BUSY")
            self.assertEqual(len(blocking.calls), 1)       # 供应商只被调用一次
        finally:
            release.set()
            srv.shutdown()
            srv.server_close()

    # ---- 原始字节请求（chunked / 歧义 Content-Length）----

    def _raw(self, request_bytes):
        s = socket.create_connection(("127.0.0.1", self.port), timeout=10)
        s.sendall(request_bytes)
        resp = s.recv(4096)
        s.close()
        return resp

    def test_advice_rejects_chunked_and_ambiguous_content_length(self):
        # Host 使用真实绑定端口，避免被 Host 拒绝掩盖 framing 检查
        n = len(self.transport.calls)
        host = ("127.0.0.1:%d" % self.port).encode("ascii")
        chunked = (b"POST /api/students/3/advice HTTP/1.1\r\n"
                   b"Host: " + host + b"\r\n"
                   b"Content-Type: application/json\r\n"
                   b"Transfer-Encoding: chunked\r\n\r\n"
                   b"2\r\n{}\r\n0\r\n\r\n")
        dup_cl = (b"POST /api/students/3/advice HTTP/1.1\r\n"
                  b"Host: " + host + b"\r\n"
                  b"Content-Type: application/json\r\n"
                  b"Content-Length: 2\r\n"
                  b"Content-Length: 2\r\n\r\n"
                  b"{}")
        conflict_cl = (b"POST /api/students/3/advice HTTP/1.1\r\n"
                       b"Host: " + host + b"\r\n"
                       b"Content-Type: application/json\r\n"
                       b"Content-Length: 2\r\n"
                       b"Content-Length: 3\r\n\r\n"
                       b"{}")
        te_cl = (b"POST /api/students/3/advice HTTP/1.1\r\n"
                 b"Host: " + host + b"\r\n"
                 b"Content-Type: application/json\r\n"
                 b"Content-Length: 2\r\n"
                 b"Transfer-Encoding: chunked\r\n\r\n"
                 b"2\r\n{}\r\n0\r\n\r\n")
        for req in (chunked, dup_cl, conflict_cl, te_cl):
            resp = self._raw(req)
            self.assertIn(b" 400", resp.split(b"\r\n", 1)[0])
        self.assertEqual(len(self.transport.calls), n)  # 供应商零调用


class AdviceUnconfiguredTests(unittest.TestCase):
    """未配置 / 环境读取路径。"""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="cdiag-advice-uc-")
        cls.db_path = os.path.join(cls.tmpdir, "diagnosis.db")
        seed.run(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _serve(self, llm):
        srv = server.make_server(self.db_path, host="127.0.0.1", port=0, llm=llm)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(srv.shutdown)
        self.addCleanup(srv.server_close)
        return srv

    def _get(self, port, path):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        conn.request("GET", path)
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        return resp.status, raw

    def test_status_and_advice_when_not_configured(self):
        srv = self._serve({"key": None})
        status, raw = self._get(srv.server_address[1], "/api/llm/status")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw.decode("utf-8")),
                         {"configured": False, "provider": None,
                          "model": None, "reasoning_effort": None})
        conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=10)
        conn.request("POST", "/api/students/3/advice", body=b"{}",
                     headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        self.assertEqual(resp.status, 503)
        self.assertEqual(json.loads(raw.decode("utf-8"))["error"]["code"],
                         "LLM_NOT_CONFIGURED")

    def test_status_reads_env_key_when_llm_none(self):
        with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": "env-key-xyz"}):
            srv = self._serve(None)
            status, raw = self._get(srv.server_address[1], "/api/llm/status")
        self.assertEqual(status, 200)
        data = json.loads(raw.decode("utf-8"))
        self.assertEqual(data["configured"], True)
        self.assertEqual(data["model"], "deepseek-v4-pro")
        self.assertNotIn("env-key-xyz", raw.decode("utf-8"))

    def test_status_unconfigured_when_env_empty(self):
        with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""}):
            srv = self._serve(None)
            status, raw = self._get(srv.server_address[1], "/api/llm/status")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw.decode("utf-8"))["configured"], False)


class AdviceSnapshotIsolationTests(unittest.TestCase):
    """独立临时库：修改 diagnosis 后提示词必须反映真实新值/实际答对率/前置边；
    第二份不同的合法上游内容必须原样映射（防硬编码 fixture），且不污染其它测试。"""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="cdiag-advice-snap-")
        cls.db_path = os.path.join(cls.tmpdir, "diagnosis.db")
        seed.run(cls.db_path)
        conn = sqlite3.connect(cls.db_path)
        conn.execute(
            "UPDATE diagnosis SET mastery_prob = 0.123456 WHERE student_id = 3")
        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _post(self, transport):
        srv = server.make_server(
            self.db_path, host="127.0.0.1", port=0,
            llm={"key": TEST_KEY, "transport": transport})
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1],
                                              timeout=10)
            conn.request("POST", "/api/students/3/advice", body=b"{}",
                         headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            raw = resp.read()
            conn.close()
            return resp.status, raw
        finally:
            srv.shutdown()
            srv.server_close()

    def test_prompt_reflects_modified_db_actual_rates_and_edges(self):
        transport = _ok_transport()
        status, raw = self._post(transport)
        self.assertEqual(status, 200, raw.decode("utf-8"))
        self.assertEqual(len(transport.calls), 1)
        prompt = transport.calls[0]["payload"]["messages"][0]["content"]

        # 修改后的掌握概率（0.123456 → 3 位小数快照）
        self.assertIn("0.123", prompt)
        # 实际答对率（独立从 Q/X 重算，而非仅含 KP 名字）
        conn = sqlite3.connect(self.db_path)
        rates = _correct_rate(conn, 3)
        conn.close()
        for k in range(N_KP):
            self.assertIn("%.3f" % rates[k], prompt, "提示词缺 KP%d 实际答对率" % (k + 1))
        # 5 条前置边以 KP<parent>→KP<child> 列出
        for parent, child in [(1, 2), (1, 4), (2, 3), (3, 5), (4, 5)]:
            self.assertIn("KP%d→KP%d" % (parent, child), prompt)
        self.assertNotIn("profile_id", prompt)

    def test_second_distinct_upstream_content_maps_verbatim(self):
        # 与默认 fixture 完全不同的合法上游内容必须原样映射到规范化 advice
        alt = {
            "summary": "完全不同的摘要：应用题优先。",
            "priorities": [
                {"kp_id": 5, "reason": "应用题建模需加强", "actions": ["每天一道应用题"],
                 "check": "列式正确且结果吻合"},
            ],
        }
        transport = _ok_transport(content=json.dumps(alt, ensure_ascii=False))
        status, raw = self._post(transport)
        self.assertEqual(status, 200, raw.decode("utf-8"))
        data = json.loads(raw.decode("utf-8"))
        self.assertEqual(data["advice"], alt)


class DefaultTransportRedirectTests(unittest.TestCase):
    """真实 build_opener 禁跳转行为测试：本地 302 服务器 + 独立目标服务器计数请求，
    实际调用 build_opener().open，断言 302 未跟随、目标零调用、Bearer 未转发。
    需要本机端口绑定，沙箱外运行（沙箱 socket 限制下不声称已跑通）。"""

    def _serve_once(self, handler):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]

        def run():
            conn, _ = srv.accept()
            try:
                data = conn.recv(4096)
                handler(conn, data)
            finally:
                conn.close()
                srv.close()

        t = threading.Thread(target=run, daemon=True)
        t.start()
        return port, t

    def test_302_not_followed_and_bearer_not_forwarded(self):
        from src import advice  # 懒导入：保持模块级 RED 粒度（advice 尚未实现）

        target_conns = []

        def target_handler(conn, data):
            target_conns.append(data)
            conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n"
                         b"Connection: close\r\n\r\nok")

        target_port, _ = self._serve_once(target_handler)

        redirect_conns = []

        def redirect_handler(conn, data):
            redirect_conns.append(data)
            body = ("HTTP/1.1 302 Found\r\n"
                    "Location: http://127.0.0.1:%d/steal\r\n"
                    "Content-Length: 0\r\n"
                    "Connection: close\r\n\r\n" % target_port)
            conn.sendall(body.encode("ascii"))

        redirect_port, _ = self._serve_once(redirect_handler)

        with self.assertRaises(advice.AdviceError) as cm:
            # opener=None → 真实 build_opener()；指向本地重定向服务器
            advice.default_transport(
                "http://127.0.0.1:%d/start" % redirect_port, b"{}",
                {"Authorization": "Bearer fake-secret", "Content-Type": "application/json"},
                10.0, time.monotonic() + 60.0)
        self.assertEqual(cm.exception.code, "LLM_UPSTREAM_ERROR")
        self.assertEqual(len(target_conns), 0, "302 不得被跟随，目标服务器必须零调用")
        self.assertEqual(len(redirect_conns), 1, "只应有第一次请求")
        self.assertIn(b"Bearer fake-secret", redirect_conns[0])  # 第一次合法携带
        self.assertNotIn("fake-secret", cm.exception.message)
        self.assertNotIn("steal", cm.exception.message)


if __name__ == "__main__":
    unittest.main(verbosity=2)
