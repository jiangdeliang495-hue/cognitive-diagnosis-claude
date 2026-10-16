"""只读 HTTP 服务（stdlib http.server，零第三方依赖）。

- 只读库，响应 /api/*（JSON）与静态资源（安全白名单路由，防路径穿越）。
- 启动时 DB 不存在 → FileNotFoundError（不隐式建库）。
- 默认监听 127.0.0.1；测试用临时 DB 与 port=0。
- 支持 `python3 -m src.server` 与 `python3 src/server.py` 两种启动方式。
"""

import http.server
import json
import os
import re
import sys
import threading
import urllib.parse

if __package__ in (None, ""):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import advice, db

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_DB_PATH = "diagnosis.db"

_PROFILE_COUNT = 32  # 2^5 种潜在画像
_MAX_ID = (1 << 63) - 1  # SQLite INTEGER 上界（int64）

_STATIC_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "static"))

_STATIC_FILES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/style.css": "style.css",
    "/app.js": "app.js",
}

_MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}

_POSITIVE_INT = re.compile(r"^[1-9][0-9]*$")

# 建议接口错误码 → HTTP 状态（BAD_ADVICE 对外改写为 BAD_RESPONSE）
_ADVICE_HTTP_CODES = {
    "BAD_REQUEST": 400,
    "REQUEST_TOO_LARGE": 413,
    "NOT_FOUND": 404,
    "ORIGIN_FORBIDDEN": 403,
    "HOST_FORBIDDEN": 403,
    "BUSY": 429,
    "LLM_NOT_CONFIGURED": 503,
    "LLM_UNAUTHORIZED": 502,
    "LLM_PAYMENT_REQUIRED": 502,
    "LLM_RATE_LIMITED": 503,
    "LLM_UPSTREAM_ERROR": 502,
    "NETWORK": 502,
    "BAD_ADVICE": 502,
    "BAD_RESPONSE": 502,
    "TIMEOUT": 504,
    "INTERNAL": 500,
}


def _parse_student_id(segment):
    """解析学生 ID：须为正整数且在 SQLite int64 范围内。

    返回 (valid, sid)。非正整数或超出 int64 → (False, None)。
    """
    if not _POSITIVE_INT.match(segment):
        return False, None
    sid = int(segment)
    if sid > _MAX_ID:
        return False, None
    return True, sid


def _is_advice_path(path):
    """精确匹配 /api/students/{id}/advice（先于学生详情的宽泛前缀判断）。"""
    return path.startswith("/api/students/") and path.endswith("/advice")


def make_server(db_path, *, host="127.0.0.1", port=0, llm=None):
    """构造一个已绑定、只读的线程版 http.server.HTTPServer。

    - llm=None：自动读环境 DEEPSEEK_API_KEY（空串=未配置），transport 用默认网络层。
    - llm={"key": str, "transport": callable}：显式配置（测试注入 mock transport）。
    - llm={"key": None}：显式未配置。
    - 原调用（不传 llm）与原测试完全兼容。
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError("数据库不存在：%s" % db_path)
    if llm is None:
        key = os.environ.get("DEEPSEEK_API_KEY", "")
        llm = {"key": key or None, "transport": None}
    elif isinstance(llm, dict):
        key = llm.get("key")
        llm = {"key": key or None, "transport": llm.get("transport")}
    else:
        llm = {"key": None, "transport": None}
    handler = _make_handler(db_path, llm)
    return http.server.ThreadingHTTPServer((host, port), handler)


# ---------------------------------------------------------------------------
# 只读查询（每个请求开一个只读连接）
# ---------------------------------------------------------------------------

def _load_q(conn):
    nq = conn.execute("SELECT COUNT(*) FROM question").fetchone()[0]
    nk = conn.execute("SELECT COUNT(*) FROM knowledge_point").fetchone()[0]
    q = [[0] * nk for _ in range(nq)]
    for qid, kid, req in conn.execute(
            "SELECT question_id, kp_id, required FROM q_matrix"):
        q[qid - 1][kid - 1] = req
    return q


def _meta(conn):
    kps = conn.execute(
        "SELECT id, code, name, description FROM knowledge_point ORDER BY id"
    ).fetchall()
    edges = conn.execute(
        "SELECT parent_id, child_id FROM prerequisite ORDER BY parent_id, child_id"
    ).fetchall()
    return {
        "name": "智能化认知诊断 MVP",
        "knowledge_points": [
            {"id": r[0], "code": r[1], "name": r[2], "description": r[3]}
            for r in kps],
        "prerequisites": [{"parent": r[0], "child": r[1]} for r in edges],
        "student_count": conn.execute("SELECT COUNT(*) FROM student").fetchone()[0],
        "question_count": conn.execute("SELECT COUNT(*) FROM question").fetchone()[0],
        "profile_count": _PROFILE_COUNT,
    }


def _students(conn):
    rows = conn.execute("SELECT id, name FROM student ORDER BY id").fetchall()
    return {"students": [{"id": r[0], "name": r[1]} for r in rows]}


def _correct_rate(conn, sid):
    q = _load_q(conn)
    nq = len(q)
    nk = len(q[0])
    x = [0] * nq
    for qid, c in conn.execute(
            "SELECT question_id, is_correct FROM x_matrix WHERE student_id = ?",
            (sid,)):
        x[qid - 1] = c
    rates = []
    for k in range(nk):
        denom = sum(1 for i in range(nq) if q[i][k] == 1)
        num = sum(1 for i in range(nq) if q[i][k] == 1 and x[i] == 1)
        rates.append(num / denom)
    return rates


def _student_detail(conn, sid):
    row = conn.execute("SELECT id, name FROM student WHERE id = ?", (sid,)).fetchone()
    if row is None:
        return None
    kps = conn.execute(
        "SELECT id, code, name FROM knowledge_point ORDER BY id").fetchall()
    mastery_map = dict(conn.execute(
        "SELECT kp_id, mastery_prob FROM diagnosis WHERE student_id = ? ORDER BY kp_id",
        (sid,)).fetchall())
    rates = _correct_rate(conn, sid)
    mastery = [
        {"kp_id": kp_id, "code": code, "name": name, "prob": mastery_map[kp_id]}
        for (kp_id, code, name) in kps]
    correct_rate = [
        {"kp_id": kp_id, "code": code, "name": name, "rate": rates[i]}
        for i, (kp_id, code, name) in enumerate(kps)]
    return {
        "student": {"id": sid, "name": row[1]},
        "mastery": mastery,
        "correct_rate": correct_rate,
    }


def _graph(conn):
    kps = conn.execute(
        "SELECT id, code, name FROM knowledge_point ORDER BY id").fetchall()
    edges = conn.execute(
        "SELECT parent_id, child_id FROM prerequisite ORDER BY parent_id, child_id"
    ).fetchall()
    return {
        "nodes": [{"id": r[0], "code": r[1], "name": r[2]} for r in kps],
        "edges": [{"parent": r[0], "child": r[1]} for r in edges],
    }


def _items(conn):
    q = _load_q(conn)
    stems = dict(conn.execute("SELECT id, stem FROM question").fetchall())
    params = {r[0]: (r[1], r[2]) for r in conn.execute(
        "SELECT question_id, guess, slip FROM item_param").fetchall()}
    items = []
    for i, qrow in enumerate(q):
        qid = i + 1
        g, s = params[qid]
        items.append({"question_id": qid, "stem": stems[qid], "q": qrow,
                      "guess": g, "slip": s})
    return {"items": items}


def _diagnosis(conn):
    rows = conn.execute(
        "SELECT student_id, kp_id, mastery_prob FROM diagnosis "
        "ORDER BY student_id, kp_id").fetchall()
    return {"matrix": [{"student_id": r[0], "kp_id": r[1], "prob": r[2]}
                       for r in rows]}


def _make_handler(db_path, llm_config=None):
    if llm_config is None:
        llm_config = {"key": None, "transport": None}
    advice_lock = threading.Lock()  # 并发付费请求门禁（该 handler 类的全部实例共享）

    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            pass  # 静默，避免污染测试输出

        def _llm_key(self):
            return llm_config["key"]

        def _llm_transport(self):
            return llm_config["transport"] or advice.default_transport

        def _send_json(self, obj, status=200):
            # JSON 拒绝非有限值（NaN/Infinity），保持标准 JSON 而非伪造字面量。
            try:
                body = json.dumps(obj, ensure_ascii=False,
                                  allow_nan=False).encode("utf-8")
            except (ValueError, TypeError):
                body = json.dumps(
                    {"error": {"code": "INTERNAL", "message": "服务器内部错误"}},
                    ensure_ascii=False, allow_nan=False).encode("utf-8")
                status = 500
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            try:
                self._do_get()
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                self._send_json(
                    {"error": {"code": "INTERNAL", "message": "服务器内部错误"}},
                    500)

        def _do_get(self):
            path = urllib.parse.urlparse(self.path).path
            if path.startswith("/api/"):
                self._handle_api(path)
            else:
                self._handle_static(path)

        def _method_not_allowed(self):
            self._send_json(
                {"error": {"code": "METHOD_NOT_ALLOWED", "message": "仅支持 GET"}},
                405)

        def do_POST(self):
            path = urllib.parse.urlparse(self.path).path
            if _is_advice_path(path):
                self._handle_advice(path)
            else:
                self._method_not_allowed()

        def do_PUT(self):
            self._method_not_allowed()

        def do_DELETE(self):
            self._method_not_allowed()

        def do_PATCH(self):
            self._method_not_allowed()

        # -- LLM 学习建议（唯一付费接口） ---------------------------------

        def _send_advice_error(self, code, message, http=None):
            if code == "BAD_ADVICE":
                code = "BAD_RESPONSE"  # 对外不暴露内部校验码
            if http is None:
                http = _ADVICE_HTTP_CODES.get(code, 502)
            self._send_json({"error": {"code": code, "message": message}}, http)

        def _origin_trusted(self, origin):
            """同源 Origin：http://{127.0.0.1|localhost|::1}:<本服务实际绑定端口>"""
            try:
                parts = urllib.parse.urlsplit(origin)
            except ValueError:
                return False
            if parts.scheme != "http" or parts.hostname is None or parts.port is None:
                return False
            if parts.hostname.lower() not in ("127.0.0.1", "localhost", "::1"):
                return False
            return parts.port == self.server.server_address[1]

        def _handle_advice(self, path):
            """POST /api/students/{id}/advice。检查顺序（冻结）：
            framing → Host → Origin → ID → Content-Type/请求体 → 配置 → 并发门禁 →
            快照 → 供应商 → 封装。任何拒绝路径都不得调用供应商。
            """
            try:
                # 1) HTTP framing（先于一切，不被 Host/Origin 检查掩盖）
                cl_values = self.headers.get_all("Content-Length") or []
                if (self.headers.get("Transfer-Encoding") is not None
                        or len(cl_values) > 1):
                    self._send_advice_error("BAD_REQUEST", "请求体格式非法")
                    return
                # 2) Host 可信（hostname 白名单，端口不校验）
                host_header = self.headers.get("Host") or ""
                hostname = host_header.rsplit(":", 1)[0].lower().strip("[]")
                if hostname not in ("127.0.0.1", "localhost", "::1"):
                    self._send_advice_error("HOST_FORBIDDEN", "Host 不可信")
                    return
                # 3) Origin 同源（无 Origin 的本机 JSON 客户端允许）
                origin = self.headers.get("Origin")
                if origin is not None:
                    if origin == "null" or not self._origin_trusted(origin):
                        self._send_advice_error("ORIGIN_FORBIDDEN", "跨源请求被拒绝")
                        return
                # 4) 学生 ID
                segment = path[len("/api/students/"):-len("/advice")]
                valid, sid = _parse_student_id(segment)
                if not valid:
                    self._send_advice_error("BAD_REQUEST", "学生 ID 非法或超出范围")
                    return
                # 5) Content-Type 与请求体（小体积 + 严格 {}）
                ctype = (self.headers.get("Content-Type") or ""
                         ).split(";")[0].strip().lower()
                if ctype != "application/json":
                    self._send_advice_error(
                        "BAD_REQUEST", "Content-Type 必须为 application/json")
                    return
                try:
                    clen = int(cl_values[0])
                except (ValueError, IndexError):
                    self._send_advice_error("BAD_REQUEST", "Content-Length 非法")
                    return
                if clen > advice.MAX_REQUEST_BYTES:
                    self._send_advice_error("REQUEST_TOO_LARGE", "请求体过大")
                    return
                body = self.rfile.read(clen)
                try:
                    advice.check_request_json(body)
                except advice.AdviceError as e:
                    self._send_advice_error(e.code, e.message)
                    return
                # 6) 配置 + 并发付费门禁（只在真正要付费时占用）
                if not self._llm_key():
                    self._send_advice_error(
                        "LLM_NOT_CONFIGURED",
                        "未配置模型密钥（服务端环境 DEEPSEEK_API_KEY）")
                    return
                if not advice_lock.acquire(blocking=False):
                    self._send_advice_error("BUSY", "已有生成任务进行中，请稍后手动重试")
                    return
                try:
                    self._generate_advice(sid)
                except advice.AdviceError as e:
                    self._send_advice_error(e.code, e.message)
                finally:
                    advice_lock.release()
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                self._send_advice_error("INTERNAL", "服务器内部错误")

        def _generate_advice(self, sid):
            """快照（只读库，无 profile_id/其他学生，不重跑 EM、不改库）→
            关闭连接后调用供应商 → 结构校验 → 服务器封装（student_id/source 由服务端决定）。"""
            conn = db.connect(db_path, read_only=True)
            try:
                row = conn.execute("SELECT id, name FROM student WHERE id = ?",
                                   (sid,)).fetchone()
                if row is None:
                    self._send_advice_error("NOT_FOUND", "学生不存在")
                    return
                kps = conn.execute(
                    "SELECT id, name FROM knowledge_point ORDER BY id").fetchall()
                name_map = {kid: name for (kid, name) in kps}
                mastery_rows = conn.execute(
                    "SELECT kp_id, mastery_prob FROM diagnosis "
                    "WHERE student_id = ? ORDER BY kp_id", (sid,)).fetchall()
                edges = conn.execute(
                    "SELECT parent_id, child_id FROM prerequisite "
                    "ORDER BY parent_id, child_id").fetchall()
                rates = _correct_rate(conn, sid)
            finally:
                conn.close()  # 关闭只读连接后才调用供应商

            mastery = [(kid, name_map[kid], prob) for (kid, prob) in mastery_rows]
            correct_rate = [(kid, name_map[kid], rate)
                            for kid, rate in enumerate(rates, start=1)]
            prompt = advice.build_prompt(mastery, correct_rate, kps, edges)
            content, _finish, request_id, _usage = advice.call_provider(
                self._llm_transport(), self._llm_key(), prompt)
            parsed = advice.parse_advice(content, [kid for (kid, _name) in kps])
            self._send_json({
                "student_id": sid,
                "source": "llm",
                "provider": "deepseek",
                "model": advice.MODEL,
                "reasoning_effort": advice.REASONING_EFFORT,
                "request_id": request_id,
                "advice": parsed,
            }, 200)

        def _handle_api(self, path):
            # 建议接口先精确匹配（避免被学生详情宽泛前缀误判）；advice 仅 POST，GET 一律 405
            if _is_advice_path(path):
                self._send_json(
                    {"error": {"code": "METHOD_NOT_ALLOWED", "message": "仅支持 POST"}},
                    405)
                return
            conn = None
            status = 200
            obj = None
            try:
                conn = db.connect(db_path, read_only=True)
                if path == "/api/meta":
                    status, obj = 200, _meta(conn)
                elif path == "/api/students":
                    status, obj = 200, _students(conn)
                elif path == "/api/graph":
                    status, obj = 200, _graph(conn)
                elif path == "/api/items":
                    status, obj = 200, _items(conn)
                elif path == "/api/diagnosis":
                    status, obj = 200, _diagnosis(conn)
                elif path == "/api/llm/status":
                    status, obj = 200, advice.status_payload(self._llm_key())
                elif path.startswith("/api/students/"):
                    segment = path[len("/api/students/"):]
                    valid, sid = _parse_student_id(segment)
                    if not valid:
                        status, obj = 400, {
                            "error": {"code": "BAD_REQUEST",
                                      "message": "学生 ID 非法或超出范围"}}
                    else:
                        detail = _student_detail(conn, sid)
                        if detail is None:
                            status, obj = 404, {
                                "error": {"code": "NOT_FOUND",
                                          "message": "学生不存在"}}
                        else:
                            status, obj = 200, detail
                else:
                    status, obj = 404, {
                        "error": {"code": "NOT_FOUND", "message": "接口不存在"}}
            except Exception:
                status, obj = 500, {
                    "error": {"code": "INTERNAL", "message": "服务器内部错误"}}
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass
            self._send_json(obj, status)

        def _handle_static(self, path):
            name = _STATIC_FILES.get(path)
            if name is None:
                self._send_json(
                    {"error": {"code": "NOT_FOUND", "message": "资源不存在"}}, 404)
                return
            full = os.path.join(_STATIC_DIR, name)
            if not os.path.exists(full):
                self._send_json(
                    {"error": {"code": "NOT_FOUND", "message": "资源不存在"}}, 404)
                return
            ext = os.path.splitext(name)[1]
            with open(full, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", _MIME[ext])
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        prog="src.server",
        description="启动只读认知诊断 HTTP 服务（静态页 + /api/* JSON）。")
    parser.add_argument("db_path", nargs="?", default=DEFAULT_DB_PATH,
                        help="SQLite 数据库路径（默认 %(default)s）")
    parser.add_argument("port", nargs="?", type=int, default=DEFAULT_PORT,
                        help="监听端口（默认 %(default)s）")
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help="监听地址（默认 %(default)s）")
    parser.add_argument("--prompt-key", action="store_true",
                        help="交互式输入 DEEPSEEK_API_KEY（getpass 隐藏输入，"
                             "仅写入当前进程环境，不存盘）")
    args = parser.parse_args(argv)
    if args.prompt_key:
        import getpass
        key = getpass.getpass("请输入 DEEPSEEK_API_KEY（输入不回显）：")
        if key.strip():
            os.environ["DEEPSEEK_API_KEY"] = key
    srv = make_server(args.db_path, host=args.host, port=args.port)
    print("只读服务已启动：http://%s:%d" % (args.host, srv.server_address[1]))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
