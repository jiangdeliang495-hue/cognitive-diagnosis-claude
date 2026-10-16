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
import urllib.parse

if __package__ in (None, ""):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import db

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


def make_server(db_path, *, host="127.0.0.1", port=0):
    """构造一个已绑定、只读的线程版 http.server.HTTPServer。"""
    if not os.path.exists(db_path):
        raise FileNotFoundError("数据库不存在：%s" % db_path)
    handler = _make_handler(db_path)
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


def _make_handler(db_path):
    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            pass  # 静默，避免污染测试输出

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
            self._method_not_allowed()

        def do_PUT(self):
            self._method_not_allowed()

        def do_DELETE(self):
            self._method_not_allowed()

        def do_PATCH(self):
            self._method_not_allowed()

        def _handle_api(self, path):
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
    args = parser.parse_args(argv)
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
