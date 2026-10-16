"""src/seed.py 与 src/server.py 的 CLI 启动回归测试。

用真实 subprocess 验证 `main`（而非只测 `run` / `make_server`）：
- `python3 -m src.*` 与 `python3 src/*.py` 两种启动方式。
- `--help`、临时 DB 创建 / 启动。
"""

import http.client
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _run(args, timeout=60):
    return subprocess.run(
        [sys.executable] + args, cwd=ROOT, capture_output=True, text=True,
        timeout=timeout)


class SeedCliTests(unittest.TestCase):
    def test_help_via_module(self):
        r = _run(["-m", "src.seed", "--help"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("db_path", r.stdout)
        self.assertIn("--force", r.stdout)

    def test_help_via_script(self):
        r = _run(["src/seed.py", "--help"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--force", r.stdout)

    def test_creates_db_via_module(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "d.db")
            r = _run(["-m", "src.seed", db])
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(os.path.exists(db))

    def test_creates_db_via_script(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "d.db")
            r = _run(["src/seed.py", db])
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(os.path.exists(db))

    def test_force_rebuilds(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "d.db")
            self.assertEqual(_run(["-m", "src.seed", db]).returncode, 0)
            r = _run(["-m", "src.seed", db, "--force"])
            self.assertEqual(r.returncode, 0, r.stderr)


class ServerCliTests(unittest.TestCase):
    def test_help_via_module(self):
        r = _run(["-m", "src.server", "--help"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("db_path", r.stdout)
        self.assertIn("port", r.stdout)

    def test_help_via_script(self):
        r = _run(["src/server.py", "--help"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("db_path", r.stdout)

    def test_startup_and_serve_via_module(self):
        from src import seed
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "d.db")
            seed.run(db)
            s = socket.socket()
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
            s.close()
            proc = subprocess.Popen(
                [sys.executable, "-m", "src.server", db, str(port)],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True)
            try:
                status = None
                deadline = time.time() + 8
                while time.time() < deadline:
                    try:
                        c = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
                        c.request("GET", "/api/meta")
                        resp = c.getresponse()
                        status = resp.status
                        c.close()
                        break
                    except OSError:
                        time.sleep(0.05)
                self.assertEqual(status, 200)
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()


if __name__ == "__main__":
    unittest.main(verbosity=2)
