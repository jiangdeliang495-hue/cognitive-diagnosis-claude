"""SQLite 建库与读写封装（stdlib sqlite3，零第三方依赖）。

按 docs/schema.sql（唯一权威定义）建库，并强制数据不变量（FK、二元 X、题参边界）。
"""

import os
import sqlite3
import urllib.parse

_SCHEMA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "docs", "schema.sql")
)


def connect(path, *, read_only=False):
    """打开 SQLite 连接并设置 PRAGMA foreign_keys=ON。

    read_only=True 时以只读 URI 打开（供 server 使用），返回 sqlite3.Connection。
    """
    if read_only:
        uri = "file:%s?mode=ro" % urllib.parse.quote(os.path.abspath(path))
        conn = sqlite3.connect(uri, uri=True)
    else:
        conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn):
    """按 docs/schema.sql 建表（幂等：CREATE TABLE IF NOT EXISTS）。"""
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
