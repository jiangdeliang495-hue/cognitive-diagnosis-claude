"""只读 HTTP 服务（TDD RED 阶段：接口桩，逻辑未实现）。

- 只读库，响应 /api/*（JSON）与静态资源。
- 启动时 DB 不存在 → FileNotFoundError（不隐式建库）。
- 默认监听 127.0.0.1；测试用临时 DB 与 port=0。
- 支持 `python3 -m src.server` 与 `python3 src/server.py` 两种启动方式。
"""

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def make_server(db_path, *, host="127.0.0.1", port=0):
    """构造一个已绑定、只读的 http.server.HTTPServer。

    - db_path 不存在 → FileNotFoundError，且不创建该文件。
    - 返回 HTTPServer（线程版），调用方 serve_forever()。
    """
    raise NotImplementedError


def main(argv=None):
    """CLI 入口：解析 db_path/host/port（供 python3 -m src.server / src/server.py）。"""
    raise NotImplementedError


if __name__ == "__main__":
    main()
