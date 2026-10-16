"""seed 编排（TDD RED 阶段：接口桩，逻辑未实现）。

编排：建库 → 合成（data_gen）→ 校准（dina.fit）→ 落库（db）。
- 默认拒绝覆盖已有库（FileExistsError）；force=True 时显式重建。
- 支持 `python3 -m src.seed` 与 `python3 src/seed.py` 两种启动方式。
"""

DEFAULT_DB_PATH = "diagnosis.db"


def run(db_path, *, force=False, seed=None):
    """建库并写入全部数据，返回 db_path。

    - db_path 已存在且 force=False → FileExistsError。
    - seed：合成随机种子（None 使用 data_gen.SEED）。
    """
    raise NotImplementedError


def main(argv=None):
    """CLI 入口：解析 db_path 与 --force（供 python3 -m src.seed / src/seed.py）。"""
    raise NotImplementedError


if __name__ == "__main__":
    main()
