from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from token_reduce.analyzer import Analyzer
from token_reduce.cli import _launch_assistant
from token_reduce.config import load_config
from token_reduce.easy_mode import run_use_flow
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
        # --project-root must come BEFORE the subcommand (global argparse flag)
        self.assertIn("token-reduce --project-root", script)
        self.assertIn("sync --git-head", script)
        self.assertIn("python3 -m token_reduce --project-root", script)
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

    def test_use_flow_generates_prompt_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "main.py"
            src.write_text("def run_task():\n    return 1\n", encoding="utf-8")

            cfg = load_config(root)
            analyzer = Analyzer(cfg)
            try:
                result = run_use_flow(
                    config=cfg,
                    analyzer=analyzer,
                    assistant="chatgpt",
                    changed_inputs=["main.py"],
                    depth=2,
                    max_files=5,
                    out_dir=None,
                )
                self.assertTrue(Path(result.context_json_path).exists())
                self.assertTrue(Path(result.prompt_md_path).exists())
                prompt = Path(result.prompt_md_path).read_text(encoding="utf-8")
                self.assertIn("ReduceToken Context Prompt (chatgpt)", prompt)
                self.assertIn("Changed Files", prompt)
            finally:
                analyzer.close()

    def test_launch_assistant_not_found(self) -> None:
        status, error = _launch_assistant("gemini", "hello", "definitely-not-a-real-cli-binary")
        self.assertEqual(status, "not_found")
        self.assertIsNotNone(error)


    def test_typescript_and_relative_import_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "utils.ts").write_text("export function helper(): number { return 42; }\n", encoding="utf-8")
            (root / "src" / "index.ts").write_text("import { helper } from './utils';\n", encoding="utf-8")
            (root / "src" / "components").mkdir()
            (root / "src" / "components" / "index.tsx").write_text("export const Card = () => null;\n", encoding="utf-8")

            cfg = load_config(root)
            analyzer = Analyzer(cfg)
            try:
                # Direct relative import without extension
                resolved = analyzer.resolve_import("src/index.ts", "./utils")
                self.assertEqual(resolved, "src/utils.ts")

                # Directory index resolution
                resolved_index = analyzer.resolve_import("src/index.ts", "./components")
                self.assertEqual(resolved_index, "src/components/index.tsx")
            finally:
                analyzer.close()

    def test_enhanced_language_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # TypeScript
            (root / "app.ts").write_text(
                "export interface User { id: string; }\n"
                "export const greet = (name: string) => `Hello ${name}`;\n"
                "export async function fetchUser(): Promise<User> { return { id: '1' }; }\n",
                encoding="utf-8",
            )
            # Python with typed signature
            (root / "service.py").write_text(
                "class BaseService:\n    pass\n\n"
                "class UserService(BaseService):\n"
                "    def find_user(self, user_id: str, active: bool = True) -> dict:\n"
                "        return {'id': user_id}\n",
                encoding="utf-8",
            )
            # Go
            (root / "server.go").write_text(
                "package main\n\n"
                "type Server struct {}\n\n"
                "func (s *Server) Start() error { return nil }\n",
                encoding="utf-8",
            )
            # Rust
            (root / "lib.rs").write_text(
                "pub struct Config {}\n\n"
                "pub fn init() -> Config { Config {} }\n",
                encoding="utf-8",
            )

            cfg = load_config(root)
            analyzer = Analyzer(cfg)
            try:
                summary = analyzer.build_graph()
                self.assertEqual(summary["tracked"], 4)

                ts_symbols = {s.name: s for s in analyzer.store.symbols_in_file("app.ts")}
                self.assertIn("User", ts_symbols)
                self.assertIn("greet", ts_symbols)
                self.assertIn("fetchUser", ts_symbols)

                py_symbols = {s.name: s for s in analyzer.store.symbols_in_file("service.py")}
                self.assertIn("UserService", py_symbols)
                self.assertIn("BaseService", py_symbols["UserService"].signature)
                self.assertIn("find_user", py_symbols)
                self.assertIn("user_id: str", py_symbols["find_user"].signature)

                go_symbols = {s.name: s for s in analyzer.store.symbols_in_file("server.go")}
                self.assertIn("Server", go_symbols)
                self.assertIn("Start", go_symbols)

                rs_symbols = {s.name: s for s in analyzer.store.symbols_in_file("lib.rs")}
                self.assertIn("Config", rs_symbols)
                self.assertIn("init", rs_symbols)
            finally:
                analyzer.close()

    def test_token_estimation_and_max_tokens_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("def big_func():\n" + "    x = 1\n" * 100, encoding="utf-8")
            (root / "b.py").write_text("import a\ndef caller():\n    return a.big_func()\n", encoding="utf-8")

            cfg = load_config(root)
            analyzer = Analyzer(cfg)
            try:
                analyzer.build_graph()
                result = run_use_flow(
                    config=cfg,
                    analyzer=analyzer,
                    assistant="gemini",
                    changed_inputs=["a.py"],
                    depth=2,
                    max_files=10,
                    out_dir=None,
                    max_tokens=300,
                )
                self.assertGreater(result.estimated_tokens, 0)
                self.assertGreater(result.baseline_tokens, 0)
                self.assertGreaterEqual(result.token_reduction_pct, 0.0)

                prompt = Path(result.prompt_md_path).read_text(encoding="utf-8")
                self.assertIn("ReduceToken Optimization Engine", prompt)
                self.assertIn("Gemini mode", prompt)
            finally:
                analyzer.close()

    def test_clean_command_removes_state(self) -> None:
        from token_reduce.cli import main
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "main.py").write_text("def x(): pass\n", encoding="utf-8")
            # Run setup
            ret = main(["--project-root", str(root), "setup", "--no-watch"])
            self.assertEqual(ret, 0)
            self.assertTrue((root / ".token-reduce" / "graph.db").exists())

            # Run clean
            ret_clean = main(["--project-root", str(root), "clean", "--all"])
            self.assertEqual(ret_clean, 0)
            self.assertFalse((root / ".token-reduce" / "graph.db").exists())

    def test_configure_gemini_and_vscode(self) -> None:
        from token_reduce.installer import _configure_gemini, _configure_vscode
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Gemini configure when GEMINI.md or .gemini doesn't exist
            self.assertFalse(_configure_gemini(root))
            (root / "GEMINI.md").write_text("# Old Notes\n", encoding="utf-8")
            self.assertTrue(_configure_gemini(root))
            self.assertIn("Token Reduce Context Workflow", (root / "GEMINI.md").read_text(encoding="utf-8"))

            # VS Code tasks
            self.assertFalse(_configure_vscode(root))
            (root / ".vscode").mkdir()
            self.assertTrue(_configure_vscode(root))
            self.assertTrue((root / ".vscode" / "tasks.json").exists())

    def test_git_porcelain_parsing(self) -> None:
        from unittest.mock import patch, MagicMock
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = load_config(root)
            analyzer = Analyzer(cfg)
            try:
                mock_proc = MagicMock()
                mock_proc.returncode = 0
                mock_proc.stdout = "R  old.py -> new.py\n?? \"quoted.py\"\nM  regular.py\n"
                with patch("subprocess.run", return_value=mock_proc):
                    changed = analyzer.changed_files_from_worktree()
                    names = [p.name for p in changed]
                    self.assertIn("new.py", names)
                    self.assertIn("quoted.py", names)
                    self.assertIn("regular.py", names)
                    self.assertNotIn("old.py", names)
            finally:
                analyzer.close()

    def test_caveman_directives_and_savings_estimation(self) -> None:
        from token_reduce.caveman import format_caveman_directive, estimate_output_savings_pct

        # Test savings estimation
        self.assertEqual(estimate_output_savings_pct("off"), 0.0)
        self.assertEqual(estimate_output_savings_pct("mild"), 40.0)
        self.assertEqual(estimate_output_savings_pct("full"), 65.0)
        self.assertEqual(estimate_output_savings_pct("raw"), 75.0)

        # Off mode has no directive
        self.assertEqual(format_caveman_directive("off"), "")

        # Mild, Full, Raw modes contain thinking override
        for mode in ["mild", "full", "raw"]:
            directive = format_caveman_directive(mode)
            self.assertIn("CRITICAL SYSTEM OVERRIDE - ZERO CONVERSATIONAL FILLER", directive)
            self.assertIn("DO NOT think out loud, monologue", directive)

        # Raw mode requires code-only
        raw_directive = format_caveman_directive("raw")
        self.assertIn("Output ONLY code blocks", raw_directive)

    def test_slash_commands_installation(self) -> None:
        from token_reduce.slash_commands import install_all_slash_commands
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            installed = install_all_slash_commands(root)
            expected_cmds = [

                "/reduce",
                "/reducetoken",
                "/plan",
                "/review",
                "/security",
                "/qa",
                "/ship",
                "/debug",
                "/strategy",
            ]
            self.assertEqual(installed.claude_commands, expected_cmds)
            self.assertEqual(len(installed.cursor_rules), 1)
            self.assertTrue(installed.gemini_configured)
            self.assertTrue(installed.vscode_configured)
            self.assertTrue(installed.copilot_configured)

            # Local project install writes all role commands to root/.claude/commands/
            for cmd_name in ("reduce", "reducetoken", "plan", "review", "security", "qa", "ship", "debug", "strategy"):
                cmd_path = root / ".claude" / "commands" / f"{cmd_name}.md"
                self.assertTrue(cmd_path.exists(), f"Missing {cmd_path}")

            claude_reduce = (root / ".claude" / "commands" / "reduce.md").read_text(encoding="utf-8")
            self.assertIn("/reduce", claude_reduce)
            self.assertIn("token-reduce", claude_reduce)

            # Check Cursor rule
            cursor_rule = root / ".cursor" / "rules" / "reduce-token.mdc"
            self.assertTrue(cursor_rule.exists())
            rule_text = cursor_rule.read_text(encoding="utf-8")
            self.assertIn("alwaysApply: true", rule_text)
            self.assertIn("ReduceToken", rule_text)

            # Check Gemini / Antigravity instruction
            gemini_file = root / "GEMINI.md"
            self.assertTrue(gemini_file.exists())
            self.assertIn("ReduceToken Mode", gemini_file.read_text(encoding="utf-8"))


    def test_cli_slash_command_interception(self) -> None:
        from token_reduce.cli import _intercept_slash_commands
        # Test bare slash '/'
        args_slash = _intercept_slash_commands(["/"])
        self.assertEqual(args_slash[0], "use")
        self.assertIn("--caveman", args_slash)
        self.assertIn("full", args_slash)

        # Test '/reducetoken'
        args_reduce_tok = _intercept_slash_commands(["/reducetoken"])
        self.assertEqual(args_reduce_tok[0], "use")
        self.assertIn("--caveman", args_reduce_tok)
        self.assertIn("full", args_reduce_tok)

        # Test role slash commands
        for slash_cmd, expected_subcmd in (
            ("/review", "review"),
            ("/plan", "plan"),
            ("/security", "security"),
            ("/qa", "qa"),
            ("/ship", "ship"),
            ("/debug", "debug"),
            ("/strategy", "strategy"),
        ):
            args_role = _intercept_slash_commands([slash_cmd])
            self.assertEqual(args_role[0], expected_subcmd)
            self.assertIn("--copy", args_role)
            self.assertIn("--print", args_role)

        # Test regular command passes through untouched
        args_normal = _intercept_slash_commands(["status", "--json"])
        self.assertEqual(args_normal, ["status", "--json"])

    def test_use_flow_with_caveman_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "calculator.py").write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")
            cfg = load_config(root)
            analyzer = Analyzer(cfg)
            try:
                analyzer.build_graph()
                result = run_use_flow(
                    config=cfg,
                    analyzer=analyzer,
                    assistant="cursor",
                    changed_inputs=["calculator.py"],
                    depth=1,
                    max_files=5,
                    out_dir=None,
                    caveman="full",
                )
                self.assertEqual(result.caveman, "full")
                self.assertEqual(result.caveman_savings_pct, 65.0)

                prompt_content = Path(result.prompt_md_path).read_text(encoding="utf-8")
                # ReduceToken badge should be present
                self.assertIn("ReduceToken Optimization Engine", prompt_content)
                self.assertIn("CRITICAL SYSTEM OVERRIDE - ZERO CONVERSATIONAL FILLER", prompt_content)
                self.assertIn("REDUCETOKEN DIRECT", prompt_content)
            finally:
                analyzer.close()

    def test_specialist_flow_and_prompt_generation(self) -> None:
        from token_reduce.specialists import run_specialist_flow
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "auth.py").write_text(
                "def authenticate(user: str, token: str) -> bool:\n"
                "    return token == 'secret'\n",
                encoding="utf-8",
            )
            cfg = load_config(root)
            analyzer = Analyzer(cfg)
            try:
                analyzer.build_graph()
                res = run_specialist_flow(
                    config=cfg,
                    analyzer=analyzer,
                    role="review",
                    assistant="claude",
                    changed_inputs=["auth.py"],
                    caveman="full",
                )
                self.assertEqual(res.role_key, "review")
                self.assertIn("Staff Engineer", res.title)
                self.assertIn("auth.py", res.changed)

                prompt_text = Path(res.prompt_md_path).read_text(encoding="utf-8")
                self.assertIn("ReduceToken Specialist Prompt", prompt_text)
                self.assertIn("Staff Engineer Code Reviewer", prompt_text)
                self.assertIn("CRITICAL SYSTEM OVERRIDE", prompt_text)
                self.assertIn("Impacted Codebase Context (AST Blast Radius)", prompt_text)
            finally:
                analyzer.close()

    def test_specialist_cli_execution(self) -> None:
        from token_reduce.cli import main
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("def start():\n    pass\n", encoding="utf-8")
            for subcmd in ("review", "plan", "security"):
                ret = main(["--project-root", str(root), subcmd, "--json"])
                self.assertEqual(ret, 0, f"Command {subcmd} failed")


if __name__ == "__main__":
    unittest.main()



