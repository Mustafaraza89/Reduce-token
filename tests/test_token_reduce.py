from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from token_reduce.analyzer import Analyzer
from token_reduce.config import load_config
from token_reduce.installer import _hook_script, _install_git_hooks


class TokenReduceTests(unittest.TestCase):
    def test_build_and_blast_radius(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("import b\n\ndef foo():\n    return b.bar()\n", encoding="utf-8")
            (root / "b.py").write_text("def bar():\n    return 1\n", encoding="utf-8")

            cfg = load_config(root)
            analyzer = Analyzer(cfg)
            try:
                summary = analyzer.build_graph()
                self.assertEqual(summary["tracked"], 2)
                blast = analyzer.blast_radius([root / "b.py"], max_depth=2)
                nodes = {node for node, _ in blast}
                self.assertIn("file::a.py", nodes)
                self.assertIn("file::b.py", nodes)
            finally:
                analyzer.close()

    def test_notebook_is_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nb = {
                "cells": [
                    {"cell_type": "code", "source": ["def nb_func():\n", "    return 123\n"], "metadata": {}},
                    {"cell_type": "markdown", "source": ["# title"], "metadata": {}},
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
            (root / "analysis.ipynb").write_text(json.dumps(nb), encoding="utf-8")

            cfg = load_config(root)
            analyzer = Analyzer(cfg)
            try:
                analyzer.build_graph()
                row = analyzer.store.conn.execute("SELECT COUNT(*) AS count FROM symbols").fetchone()
                self.assertIsNotNone(row)
                self.assertGreater(int(row["count"]), 0)
            finally:
                analyzer.close()

    def test_hook_script_has_python_fallback(self) -> None:
        script = _hook_script("head")
        self.assertIn("token-reduce sync", script)
        self.assertIn("python3 -m token_reduce sync", script)
        self.assertIn("--git-head", script)

    def test_install_git_hooks_in_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            hooks, notes = _install_git_hooks(root)
            self.assertEqual(notes, [])
            self.assertIn("post-commit", hooks)
            self.assertIn("post-merge", hooks)
            self.assertTrue((root / ".git" / "hooks" / "post-commit").exists())


if __name__ == "__main__":
    unittest.main()
