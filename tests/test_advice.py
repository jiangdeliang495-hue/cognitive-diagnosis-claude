"""src/advice.py 的 TDD 测试（RED：契约先行，实现未完成）。

纯逻辑 + mock transport，不绑定端口、不访问网络、不读任何密钥：
- 严格 {} 请求体校验；提示词中文护栏与快照（两学生必然不同、无密钥/profile_id）；
- 建议 JSON 结构校验（1~3 项、技能 ID 存在且互异、文本类型/非空/长度上限）；
- 供应商载荷锁定字段（无 temperature）、固定 URL + Bearer、禁止重定向；
- mock transport 上的错误映射、字节上限、整体截止传递、无自动重试、忽略 reasoning_content。

契约见 docs/LLM_SUGGESTIONS.md §5–§6。RED 来自待实现的 src.advice 模块缺失。
"""

import io
import json
import socket
import time
import unittest
import urllib.error
import urllib.request

from src import advice


KNOWN_IDS = [1, 2, 3, 4, 5]


def _kp_name(kp_id):
    return {1: "分数概念", 2: "通分", 3: "分数加减", 4: "分数乘除",
            5: "应用题建模/列式"}[kp_id]


def _mastery(probs):
    return [(i + 1, _kp_name(i + 1), probs[i]) for i in range(5)]


def _rates(rates):
    return [(i + 1, _kp_name(i + 1), rates[i]) for i in range(5)]


KPS = [(i + 1, _kp_name(i + 1)) for i in range(5)]
EDGES = [(1, 2), (1, 4), (2, 3), (3, 5), (4, 5)]


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


def _mock_ok(extra=None, content=None, finish="stop"):
    """返回一个可复用的成功 transport（content 缺省为合法建议）。"""
    body = {
        "id": "chatcmpl-test-1",
        "choices": [{
            "message": {
                "content": json.dumps(_valid_advice(), ensure_ascii=False)
                if content is None else content,
                "reasoning_content": "这段思考过程绝不能被返回",
            },
            "finish_reason": finish,
        }],
        "usage": {"prompt_tokens": 12, "completion_tokens": 34},
    }
    if extra:
        body.update(extra)

    def transport(url, data, headers, socket_timeout, deadline):
        transport.calls.append(
            {"url": url, "data": data, "headers": headers,
             "socket_timeout": socket_timeout, "deadline": deadline})
        return 200, {"content-type": "application/json"}, json.dumps(body).encode("utf-8")

    transport.calls = []
    return transport


def _err_transport(fn):
    def transport(url, data, headers, socket_timeout, deadline):
        transport.calls.append(1)
        return fn()

    transport.calls = []
    return transport


class PromptTests(unittest.TestCase):
    def test_prompt_contains_chinese_guardrails(self):
        p = advice.build_prompt(
            _mastery([0.93, 0.40, 0.55, 0.80, 0.20]), _rates([0.9, 0.3, 0.5, 0.8, 0.2]),
            KPS, EDGES)
        # 掌握概率是估计、与答对率区分
        self.assertIn("掌握概率", p)
        self.assertIn("估计", p)
        self.assertIn("答对率", p)
        # 薄弱知识与前置关系
        self.assertIn("前置", p)
        # 具体练习动作与检查方法
        self.assertIn("练习", p)
        self.assertIn("检查", p)
        # 不编造学生经历/测验结果
        self.assertIn("编造", p)
        # 合成小样本局限
        self.assertIn("合成", p)
        self.assertIn("小样本", p)
        # 输出结构（summary/priorities/actions/check）
        self.assertIn("summary", p)
        self.assertIn("priorities", p)
        self.assertIn("actions", p)
        self.assertIn("check", p)

    def test_prompt_contains_kp_names_and_3_decimal_probs(self):
        p = advice.build_prompt(
            _mastery([0.933, 0.401, 0.55, 0.8, 0.2]), _rates([0.9, 0.3, 0.5, 0.8, 0.2]),
            KPS, EDGES)
        for name in [_kp_name(i) for i in KNOWN_IDS]:
            self.assertIn(name, p)
        self.assertIn("0.933", p)  # 3 位小数快照
        self.assertIn("0.401", p)

    def test_prompt_differs_between_students(self):
        a = advice.build_prompt(
            _mastery([0.93, 0.40, 0.55, 0.80, 0.20]), _rates([0.9, 0.3, 0.5, 0.8, 0.2]),
            KPS, EDGES)
        b = advice.build_prompt(
            _mastery([0.10, 0.95, 0.90, 0.85, 0.70]), _rates([0.1, 0.9, 0.9, 0.8, 0.7]),
            KPS, EDGES)
        self.assertNotEqual(a, b)

    def test_prompt_lists_prerequisite_edges(self):
        p = advice.build_prompt(
            _mastery([0.93, 0.40, 0.55, 0.80, 0.20]), _rates([0.9, 0.3, 0.5, 0.8, 0.2]),
            KPS, EDGES)
        for parent, child in EDGES:
            self.assertIn("KP%d→KP%d" % (parent, child), p)

    def test_prompt_has_no_profile_or_key_reference(self):
        p = advice.build_prompt(
            _mastery([0.93, 0.40, 0.55, 0.80, 0.20]), _rates([0.9, 0.3, 0.5, 0.8, 0.2]),
            KPS, EDGES)
        self.assertNotIn("profile_id", p)
        self.assertNotIn("DEEPSEEK_API_KEY", p)


class ParseAdviceTests(unittest.TestCase):
    def test_valid_advice_parsed(self):
        got = advice.parse_advice(
            json.dumps(_valid_advice(), ensure_ascii=False), KNOWN_IDS)
        self.assertEqual(got["summary"], _valid_advice()["summary"])
        self.assertEqual(len(got["priorities"]), 2)
        self.assertEqual(got["priorities"][0]["kp_id"], 2)
        self.assertEqual(got["priorities"][0]["actions"],
                         _valid_advice()["priorities"][0]["actions"])

    def _assert_bad(self, content):
        with self.assertRaises(advice.AdviceError) as cm:
            advice.parse_advice(content, KNOWN_IDS)
        self.assertEqual(cm.exception.code, "BAD_ADVICE")

    def test_rejects_empty_or_non_json(self):
        for bad in ("", "   ", "不是 JSON", "42", '"str"', "[]", "null"):
            self._assert_bad(bad)

    def test_rejects_missing_keys_and_wrong_types(self):
        for bad in [
            '{"priorities": []}',
            '{"summary": "x"}',
            '{"summary": 42, "priorities": []}',
            '{"summary": "x", "priorities": "no"}',
            '{"summary": "x", "priorities": []}',   # 空 priorities
        ]:
            self._assert_bad(bad)

    def test_rejects_empty_priority_list_and_too_many(self):
        self._assert_bad(json.dumps({"summary": "x", "priorities": []}))
        many = {"summary": "x", "priorities": [
            {"kp_id": k, "reason": "r", "actions": ["a"], "check": "c"}
            for k in (1, 2, 3, 4)]}
        self._assert_bad(json.dumps(many))

    def test_rejects_boolean_kp_id(self):
        # bool 是 int 子类，必须显式拒绝（JSON true/false）
        for kp in (True, False):
            bad = {"summary": "x", "priorities": [
                {"kp_id": kp, "reason": "r", "actions": ["a"], "check": "c"}]}
            self._assert_bad(json.dumps(bad))

    def test_unknown_fields_stripped_not_passed_through(self):
        content = json.dumps({
            "summary": "s",
            "priorities": [
                {"kp_id": 1, "reason": "r", "actions": ["a"], "check": "c",
                 "hint": "内部字段", "grade": 9},
            ],
            "extra": "x", "chain_of_thought": "不应带出",
        })
        got = advice.parse_advice(content, KNOWN_IDS)
        self.assertEqual(sorted(got.keys()), ["priorities", "summary"])
        self.assertEqual(sorted(got["priorities"][0].keys()),
                         ["actions", "check", "kp_id", "reason"])
        dumped = json.dumps(got, ensure_ascii=False)
        self.assertNotIn("chain_of_thought", dumped)
        self.assertNotIn("hint", dumped)
        self.assertNotIn("extra", dumped)

    def test_rejects_unknown_or_duplicate_kp_id(self):
        for kp in (9, 0, -1, "2", 2.0):
            bad = {"summary": "x", "priorities": [
                {"kp_id": kp, "reason": "r", "actions": ["a"], "check": "c"}]}
            self._assert_bad(json.dumps(bad))
        dup = {"summary": "x", "priorities": [
            {"kp_id": 1, "reason": "r", "actions": ["a"], "check": "c"},
            {"kp_id": 1, "reason": "r", "actions": ["a"], "check": "c"}]}
        self._assert_bad(json.dumps(dup))

    def test_rejects_bad_text_fields_and_lengths(self):
        base = {"kp_id": 1, "reason": "r", "actions": ["a"], "check": "c"}
        for field in ("reason", "check"):
            for value in (None, 42, "", "   "):
                bad = dict(base)
                bad[field] = value
                self._assert_bad(json.dumps({"summary": "x", "priorities": [bad]}))
        bad = dict(base)
        bad["reason"] = "长" * (advice.MAX_REASON_LEN + 1)
        self._assert_bad(json.dumps({"summary": "x", "priorities": [bad]}))
        bad = dict(base)
        bad["check"] = "长" * (advice.MAX_CHECK_LEN + 1)
        self._assert_bad(json.dumps({"summary": "x", "priorities": [bad]}))

    def test_rejects_bad_actions(self):
        base = {"kp_id": 1, "reason": "r", "actions": None, "check": "c"}
        for actions in (None, "a", [], ["a"] * 4, ["a", 42], ["a", ""], ["a", "   "]):
            bad = dict(base)
            bad["actions"] = actions
            self._assert_bad(json.dumps({"summary": "x", "priorities": [bad]}))
        bad = dict(base)
        bad["actions"] = ["长" * (advice.MAX_ACTION_LEN + 1)]
        self._assert_bad(json.dumps({"summary": "x", "priorities": [bad]}))

    def test_rejects_bad_or_overlong_summary(self):
        for value in (None, 42, "", "   "):
            self._assert_bad(json.dumps({"summary": value, "priorities": [
                {"kp_id": 1, "reason": "r", "actions": ["a"], "check": "c"}]}))
        self._assert_bad(json.dumps({"summary": "长" * (advice.MAX_SUMMARY_LEN + 1),
                                     "priorities": [
                                         {"kp_id": 1, "reason": "r",
                                          "actions": ["a"], "check": "c"}]}))


class RequestJsonTests(unittest.TestCase):
    def test_accepts_strict_empty_object(self):
        advice.check_request_json(b"{}")          # 不抛
        advice.check_request_json(b" { } ")       # 允许首尾空白

    def test_rejects_non_empty_object_and_other_json(self):
        for bad in (b'{"x": 1}', b"[]", b'"str"', b"42", b"null", b"", b"   "):
            with self.assertRaises(advice.AdviceError) as cm:
                advice.check_request_json(bad)
            self.assertEqual(cm.exception.code, "BAD_REQUEST")

    def test_rejects_non_utf8(self):
        with self.assertRaises(advice.AdviceError):
            advice.check_request_json(b"\xff\xfe{}")

    def test_rejects_oversized_body(self):
        body = b'{"pad": "' + b"x" * advice.MAX_REQUEST_BYTES + b'"}'
        with self.assertRaises(advice.AdviceError) as cm:
            advice.check_request_json(body)
        self.assertEqual(cm.exception.code, "REQUEST_TOO_LARGE")


class PayloadTests(unittest.TestCase):
    def test_locked_fields_no_temperature(self):
        payload = advice.build_llm_payload("提示词")
        self.assertEqual(payload["model"], "deepseek-v4-pro")
        self.assertEqual(payload["messages"], [{"role": "user", "content": "提示词"}])
        self.assertEqual(payload["thinking"], {"type": "enabled"})
        self.assertEqual(payload["reasoning_effort"], "max")
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertIs(payload["stream"], False)
        self.assertEqual(payload["max_tokens"], 8192)
        self.assertNotIn("temperature", payload)


class BuildRequestTests(unittest.TestCase):
    def test_fixed_url_bearer_and_json_body_within_prompt_limit(self):
        # 完整 build_prompt → build_request：正常中文诊断提示词必须通过供应商 16 KiB 上限
        prompt = advice.build_prompt(
            _mastery([0.93, 0.40, 0.55, 0.80, 0.20]), _rates([0.9, 0.3, 0.5, 0.8, 0.2]),
            KPS, EDGES)
        url, headers, body = advice.build_request("k-123", prompt)
        self.assertEqual(url, advice.PROVIDER_URL)
        self.assertEqual(headers["Authorization"], "Bearer k-123")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertGreater(len(body), 0)
        self.assertLessEqual(len(body), advice.MAX_PROMPT_BYTES)
        parsed = json.loads(body.decode("utf-8"))
        self.assertEqual(parsed["model"], "deepseek-v4-pro")

    def test_prompt_payload_over_limit_rejected(self):
        # 客户端 {} 上限（MAX_REQUEST_BYTES）与供应商载荷上限（MAX_PROMPT_BYTES）是独立常量
        with self.assertRaises(advice.AdviceError) as cm:
            advice.build_request("k-123", "长" * (advice.MAX_PROMPT_BYTES + 1))
        self.assertEqual(cm.exception.code, "INTERNAL")


class _FakeResponse:
    """受控假响应：只实现 read1（单次有界读取）；read() 直接报错，防止实现退回
    聚合读取（真实 HTTPResponse.read(n) 内部可能连续底层读、跨过截止检查）。"""

    def __init__(self, status=200, headers=None, chunks=None, error=None, on_read1=None):
        self.status = status
        self.headers = headers or {}
        self._chunks = list(chunks) if chunks else []
        self._error = error
        self.on_read1 = on_read1
        self.closed = False
        self.read1_calls = 0

    def read1(self, amt=-1):
        self.read1_calls += 1
        if self.on_read1 is not None:
            self.on_read1(self)
        if self._error is not None:
            raise self._error
        if not self._chunks:
            return b""
        return self._chunks.pop(0)

    def read(self, amt=-1):
        raise AssertionError("默认传输必须使用单次有界 read1，禁止聚合 read()")

    def close(self):
        self.closed = True


class _FakeOpener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def open(self, req, timeout=None):
        self.calls.append({"url": req.full_url, "timeout": timeout,
                           "auth": req.get_header("Authorization"),
                           "data": req.data})
        if self.error is not None:
            raise self.error
        return self.response


class DefaultTransportTests(unittest.TestCase):
    """默认网络层行为测试：read1 单次有界读取、读取截止检查、socket 空闲超时、
    损坏响应、HTTPError 脱敏与资源关闭。全部注入受控时钟（真实 monotonic 可能远超
    固定 9999，测试自身不得因此误超时）。"""

    URL = "https://api.deepseek.com/chat/completions"
    T0 = 100.0        # 受控时钟起点
    DEADLINE = 220.0  # T0 + OVERALL_DEADLINE

    def _clock(self):
        return self.T0

    def test_success_closes_response(self):
        resp = _FakeResponse(status=200, headers={"content-type": "application/json"},
                             chunks=[b'{"ok":', b' true}'])
        opener = _FakeOpener(response=resp)
        status, hdrs, body = advice.default_transport(
            self.URL, b"{}", {"Authorization": "Bearer k"}, 60.0, self.DEADLINE,
            opener=opener, clock=self._clock)
        self.assertEqual(status, 200)
        self.assertEqual(body, b'{"ok": true}')
        self.assertTrue(resp.closed)
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(opener.calls[0]["auth"], "Bearer k")

    def test_overall_deadline_checked_between_read1_chunks(self):
        # 读取截止检查：正常 read1 分块 + 假时钟，块之间检查 clock()，超期中断并关闭，
        # 未读数据被丢弃（不以 socket 空闲超时代替整体截止）。
        clock = {"t": 100.0}

        def on_read1(resp):
            if resp.read1_calls == 2:
                clock["t"] = 221.0  # 第 2 块读完后推进假时钟超过截止

        resp = _FakeResponse(chunks=[b"a", b"b", b"c"], on_read1=on_read1)
        with self.assertRaises(advice.DeadlineError):
            advice.default_transport(
                self.URL, b"{}", {"Authorization": "Bearer k"}, 60.0, 220.0,
                opener=_FakeOpener(response=resp), clock=lambda: clock["t"])
        self.assertTrue(resp.closed)
        self.assertEqual(resp.read1_calls, 2)  # 有界读取次数，未无限聚合读取

    def test_socket_idle_timeout_closes_immediately_timout(self):
        # socket 空闲超时：read1 抛 socket.timeout → 立即安全关闭并返回 TIMEOUT，
        # 绝不 catch 后继续轮询（真实 HTTPResponse 缓冲对象可能已不可继续读）。
        resp = _FakeResponse(error=socket.timeout("idle"))
        with self.assertRaises(advice.AdviceError) as cm:
            advice.default_transport(
                self.URL, b"{}", {"Authorization": "Bearer k"}, 60.0, self.DEADLINE,
                opener=_FakeOpener(response=resp), clock=self._clock)
        self.assertEqual(cm.exception.code, "TIMEOUT")
        self.assertTrue(resp.closed)
        self.assertEqual(resp.read1_calls, 1)  # 只读了一次，没有重试轮询

    def test_corrupt_response_maps_bad_response_and_closes(self):
        for exc in (http.client.IncompleteRead(b"partial"),
                    http.client.HTTPException("broken"),
                    ValueError("bad read")):
            resp = _FakeResponse(error=exc)
            with self.assertRaises(advice.AdviceError) as cm:
                advice.default_transport(
                    self.URL, b"{}", {"Authorization": "Bearer k"}, 60.0, self.DEADLINE,
                    opener=_FakeOpener(response=resp), clock=self._clock)
            self.assertEqual(cm.exception.code, "BAD_RESPONSE")
            self.assertNotIn("partial", cm.exception.message)
            self.assertTrue(resp.closed)

    def test_size_limit_closes_response(self):
        resp = _FakeResponse(chunks=[b"x" * (advice.MAX_RESPONSE_BYTES + 1)])
        with self.assertRaises(advice.AdviceError) as cm:
            advice.default_transport(
                self.URL, b"{}", {"Authorization": "Bearer k"}, 60.0, self.DEADLINE,
                opener=_FakeOpener(response=resp), clock=self._clock)
        self.assertEqual(cm.exception.code, "BAD_RESPONSE")
        self.assertTrue(resp.closed)

    def test_http_error_mapping_sanitized_and_fp_closed(self):
        for code, want in [(401, "LLM_UNAUTHORIZED"), (402, "LLM_PAYMENT_REQUIRED"),
                           (429, "LLM_RATE_LIMITED"), (500, "LLM_UPSTREAM_ERROR"),
                           (302, "LLM_UPSTREAM_ERROR")]:
            fp = io.BytesIO(b"upstream-secret-body")
            err = urllib.error.HTTPError(
                self.URL, code, "msg",
                {"Location": "https://evil.example/x", "Content-Length": "19"}, fp)
            with self.assertRaises(advice.AdviceError) as cm:
                advice.default_transport(
                    self.URL, b"{}", {"Authorization": "Bearer k"}, 60.0, self.DEADLINE,
                    opener=_FakeOpener(error=err), clock=self._clock)
            self.assertEqual(cm.exception.code, want)
            self.assertTrue(fp.closed)
            self.assertNotIn("upstream-secret-body", cm.exception.message)
            self.assertNotIn("evil.example", cm.exception.message)

    def test_302_redirect_never_followed_and_no_auth_forwarded(self):
        # 纯单元 fake 异常映射（真实 build_opener 禁跳转的行为测试见
        # tests/test_advice_api.py 的本地 302 服务器 + 独立目标服务器用例）
        fp = io.BytesIO(b"")
        err = urllib.error.HTTPError(self.URL, 302, "Found",
                                     {"Location": "https://evil.example/x"}, fp)
        opener = _FakeOpener(error=err)
        with self.assertRaises(advice.AdviceError) as cm:
            advice.default_transport(
                self.URL, b"{}", {"Authorization": "Bearer k-secret"}, 60.0,
                self.DEADLINE, opener=opener, clock=self._clock)
        self.assertEqual(cm.exception.code, "LLM_UPSTREAM_ERROR")
        self.assertEqual(len(opener.calls), 1)  # 没有第二次请求
        self.assertNotIn("evil.example", cm.exception.message)
        self.assertNotIn("k-secret", cm.exception.message)

    def test_urlerror_and_open_timeout_mapping(self):
        for exc, code in [(urllib.error.URLError("boom"), "NETWORK"),
                          (socket.timeout("open blocked"), "TIMEOUT")]:
            opener = _FakeOpener(error=exc)
            with self.assertRaises(advice.AdviceError) as cm:
                advice.default_transport(
                    self.URL, b"{}", {"Authorization": "Bearer k"}, 60.0, self.DEADLINE,
                    opener=opener, clock=self._clock)
            self.assertEqual(cm.exception.code, code)


class CallProviderTests(unittest.TestCase):
    def test_success_returns_content_only_fields(self):
        t = _mock_ok()
        content, finish, rid, usage = advice.call_provider(
            t, "k", "提示词")
        self.assertEqual(finish, "stop")
        self.assertEqual(rid, "chatcmpl-test-1")
        self.assertEqual(content, json.dumps(_valid_advice(), ensure_ascii=False))
        self.assertIsInstance(usage, dict)
        self.assertEqual(len(t.calls), 1)  # 恰好一次，无自动重试
        call = t.calls[0]
        self.assertEqual(call["url"], advice.PROVIDER_URL)
        self.assertEqual(call["headers"]["Authorization"], "Bearer k")
        # reasoning_content 绝不混入返回内容
        self.assertNotIn("这段思考过程", content)

    def test_deadline_is_monotonic_plus_overall_deadline(self):
        t = _mock_ok()
        before = time.monotonic()
        advice.call_provider(t, "k", "提示词")
        after = time.monotonic()
        d = t.calls[0]["deadline"]
        self.assertGreaterEqual(d, before + advice.OVERALL_DEADLINE - 1.0)
        self.assertLessEqual(d, after + advice.OVERALL_DEADLINE + 1.0)
        self.assertAlmostEqual(t.calls[0]["socket_timeout"], advice.SOCKET_TIMEOUT)

    def test_http_error_mapping(self):
        for status, code in [(401, "LLM_UNAUTHORIZED"),
                             (402, "LLM_PAYMENT_REQUIRED"),
                             (429, "LLM_RATE_LIMITED"),
                             (500, "LLM_UPSTREAM_ERROR"),
                             (503, "LLM_UPSTREAM_ERROR")]:
            t = _err_transport(lambda s=status: (s, {}, b'{"error":"upstream body"}'))
            with self.assertRaises(advice.AdviceError) as cm:
                advice.call_provider(t, "k", "p")
            self.assertEqual(cm.exception.code, code)
            self.assertEqual(len(t.calls), 1)  # 不自动重试

    def test_network_and_timeout_mapping(self):
        for fn, code in [
            (lambda: (_ for _ in ()).throw(socket.timeout("idle")), "TIMEOUT"),
            (lambda: (_ for _ in ()).throw(advice.DeadlineError("整体截止")), "TIMEOUT"),
            (lambda: (_ for _ in ()).throw(urllib.error.URLError("boom")), "NETWORK"),
            (lambda: (_ for _ in ()).throw(OSError("conn reset")), "NETWORK"),
        ]:
            t = _err_transport(fn)
            with self.assertRaises(advice.AdviceError) as cm:
                advice.call_provider(t, "k", "p")
            self.assertEqual(cm.exception.code, code)

    def test_bad_response_cases(self):
        # 截断 finish_reason
        t = _mock_ok(finish="length")
        with self.assertRaises(advice.AdviceError) as cm:
            advice.call_provider(t, "k", "p")
        self.assertEqual(cm.exception.code, "BAD_RESPONSE")
        # 空 content
        t = _mock_ok(content="")
        with self.assertRaises(advice.AdviceError):
            advice.call_provider(t, "k", "p")
        # 非 JSON 响应体
        t = _err_transport(lambda: (200, {}, b"not json at all"))
        with self.assertRaises(advice.AdviceError) as cm:
            advice.call_provider(t, "k", "p")
        self.assertEqual(cm.exception.code, "BAD_RESPONSE")
        # 超字节上限
        big = b"x" * (advice.MAX_RESPONSE_BYTES + 1)
        t = _err_transport(lambda: (200, {}, big))
        with self.assertRaises(advice.AdviceError) as cm:
            advice.call_provider(t, "k", "p")
        self.assertEqual(cm.exception.code, "BAD_RESPONSE")

    def test_bad_response_structure_cases(self):
        # 空/错类型 choices、message、content；缺失或非 "stop" 的 finish_reason 一律拒绝
        cases = [
            json.dumps({"choices": []}).encode("utf-8"),
            json.dumps({"choices": "no"}).encode("utf-8"),
            json.dumps({"choices": [{}]}).encode("utf-8"),
            json.dumps({"choices": [{"message": {}}]}).encode("utf-8"),
            json.dumps({"choices": [{"message": {"content": 42}}]}).encode("utf-8"),
            json.dumps({"choices": [{"message": {"content": None}}]}).encode("utf-8"),
            json.dumps({"choices": [{"message": {"content": "{}"}}]}).encode("utf-8"),
            json.dumps({"choices": [{"message": {"content": "{}"},
                                     "finish_reason": None}]}).encode("utf-8"),
            json.dumps({"choices": [{"message": {"content": "{}"},
                                     "finish_reason": "content_filter"}]}).encode("utf-8"),
        ]
        for body in cases:
            t = _err_transport(lambda b=body: (200, {}, b))
            with self.assertRaises(advice.AdviceError) as cm:
                advice.call_provider(t, "k", "p")
            self.assertEqual(cm.exception.code, "BAD_RESPONSE", body[:60])

    def test_only_finish_reason_stop_succeeds(self):
        t = _mock_ok(finish="stop")
        content, finish, _, _ = advice.call_provider(t, "k", "p")
        self.assertEqual(finish, "stop")
        self.assertTrue(content)

    def test_error_messages_do_not_echo_upstream_or_key(self):
        t = _err_transport(lambda: (401, {}, b'{"secret":"upstream-leak"}'))
        with self.assertRaises(advice.AdviceError) as cm:
            advice.call_provider(t, "k-secret-123", "p")
        self.assertNotIn("upstream-leak", cm.exception.message)
        self.assertNotIn("k-secret-123", cm.exception.message)


class StatusPayloadTests(unittest.TestCase):
    def test_configured_and_unconfigured(self):
        got = advice.status_payload("k-abc")
        self.assertEqual(got, {"configured": True, "provider": "deepseek",
                               "model": "deepseek-v4-pro", "reasoning_effort": "max"})
        for key in ("", None):
            got = advice.status_payload(key)
            self.assertEqual(got, {"configured": False, "provider": None,
                                   "model": None, "reasoning_effort": None})

    def test_status_never_contains_key(self):
        dumped = json.dumps(advice.status_payload("k-abc"))
        self.assertNotIn("k-abc", dumped)


if __name__ == "__main__":
    unittest.main(verbosity=2)
