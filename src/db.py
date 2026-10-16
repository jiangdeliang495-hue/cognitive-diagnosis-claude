"""SQLite 建库与读写封装（TDD RED 阶段：接口桩，逻辑未实现）。

按 docs/schema.sql（唯一权威定义）建库，并强制数据不变量（FK、二元 X、题参边界）。
"""

import sqlite3


def connect(path, *, read_only=False):
    """打开 SQLite 连接并设置 PRAGMA foreign_keys=ON。

    read_only=True 时以只读 URI 打开（供 server 使用），返回 sqlite3.Connection。
    """
    raise NotImplementedError


def init_schema(conn):
    """按 docs/schema.sql 建表（幂等：CREATE TABLE IF NOT EXISTS）。"""
    raise NotImplementedError
