from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from .analyzer import Analyzer
from .caveman import CAVEMAN_CHOICES, estimate_output_savings_pct
from .config import AppConfig, load_config, save_config
from .context_pack import build_context_pack
from .easy_mode import ASSISTANT_CHOICES, default_launch_command, read_prompt, run_use_flow
from .installer import install_integrations
from .specialists import (
    SPECIALIST_ROLES,
    install_all_specialist_slash_commands,
    run_specialist_flow,
)
from .watcher import Watcher



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="token-reduce", description="ReduceToken: Incremental code knowledge graph & direct token reduction framework")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root (default: current directory)")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create config and graph state directory")

    setup = sub.add_parser("setup", help="One-time setup: init + build + install slash commands")
    setup.add_argument("--no-watch", action="store_true", help="Skip starting watcher")
    setup.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    build = sub.add_parser("build", help="Scan project and build/update graph")
    build.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    sync = sub.add_parser("sync", help="Incrementally sync changed files")
    sync.add_argument("--files", nargs="*", default=[], help="Changed files (relative or absolute)")
    sync.add_argument("--git-head", action="store_true", help="Use files changed in HEAD commit")
    sync.add_argument("--worktree", action="store_true", help="Use changed files in current worktree")
    sync.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    blast = sub.add_parser("blast", help="Compute blast radius from changed files")
    blast.add_argument("--changed", nargs="+", required=True, help="Changed files")
    blast.add_argument("--depth", type=int, default=None, help="Traversal depth")
    blast.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    context = sub.add_parser("context", help="Produce minimal impacted context pack")
    context.add_argument("--changed", nargs="+", required=True, help="Changed files")
    context.add_argument("--depth", type=int, default=None, help="Traversal depth")
    context.add_argument("--max-files", type=int, default=None, help="Limit impacted files")
    context.add_argument("--max-tokens", type=int, default=None, help="Limit context token budget")
    context.add_argument("--caveman", choices=CAVEMAN_CHOICES, default="full", help="ReduceToken direct mode level (default: full)")
    context.add_argument("--print", dest="print_prompt", action="store_true", help="Print generated prompt markdown to stdout")
    context.add_argument("--out", type=Path, default=None, help="Write context JSON to file")

    use = sub.add_parser("use", help="Easy daily command: auto-sync + context + ready prompt")
    use.add_argument("--assistant", choices=ASSISTANT_CHOICES, default="generic", help="Prompt style template")
    use.add_argument("--changed", nargs="*", default=[], help="Optional changed files; if empty auto-detect from git")
    use.add_argument("--depth", type=int, default=None, help="Traversal depth")
    use.add_argument("--max-files", type=int, default=None, help="Limit impacted files")
    use.add_argument("--max-tokens", type=int, default=None, help="Limit context token budget")
    use.add_argument("--caveman", choices=CAVEMAN_CHOICES, default="full", help="ReduceToken direct mode level (default: full)")
    use.add_argument("--out-dir", type=Path, default=None, help="Output directory for context and prompt files")
    use.add_argument("--print", dest="print_prompt", action="store_true", help="Print generated prompt markdown to stdout")
    use.add_argument("--copy", dest="copy_prompt", action="store_true", help="Copy generated prompt markdown to clipboard")
    use.add_argument("--launch", action="store_true", help="Launch assistant CLI and send generated prompt over stdin")
    use.add_argument("--cmd", type=str, default=None, help="Override launch command, e.g. 'gemini'")
    use.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    clean = sub.add_parser("clean", help="Reset/clean graph database and cached state")
    clean.add_argument("--all", action="store_true", help="Also remove assistant prompt/context cache")
    clean.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    watch = sub.add_parser("watch", help="Watch filesystem and sync graph incrementally")
    watch.add_argument("--interval", type=float, default=None, help="Polling interval seconds")

    install = sub.add_parser("install", help="Install editor/tool integrations + hooks + watcher")
    install.add_argument("--no-watch", action="store_true", help="Skip starting watcher")
    install.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    status = sub.add_parser("status", help="Show graph metadata")
    status.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # Specialist role commands
    def _add_specialist_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--assistant", choices=ASSISTANT_CHOICES, default="claude", help="Assistant format (default: claude)")
        p.add_argument("--changed", nargs="*", default=[], help="Optional changed files; if empty auto-detect from git")
        p.add_argument("--depth", type=int, default=None, help="Traversal depth")
        p.add_argument("--max-files", type=int, default=None, help="Limit impacted files")
        p.add_argument("--max-tokens", type=int, default=None, help="Limit context token budget")
        p.add_argument("--caveman", choices=CAVEMAN_CHOICES, default="full", help="ReduceToken direct mode level (default: full)")
        p.add_argument("--out-dir", type=Path, default=None, help="Output directory for context and prompt files")
        p.add_argument("--print", dest="print_prompt", action="store_true", help="Print generated prompt markdown to stdout")
        p.add_argument("--copy", dest="copy_prompt", action="store_true", help="Copy generated prompt markdown to clipboard")
        p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    specialist = sub.add_parser("specialist", help="Run role-specific specialist review on blast radius")
    specialist.add_argument("--role", choices=list(SPECIALIST_ROLES.keys()), default="review", help="Specialist role (default: review)")
    specialist.add_argument("--setup", action="store_true", help="Install specialist slash commands")
    _add_specialist_args(specialist)

    review_p = sub.add_parser("review", help="Staff Engineer code review on blast radius (/review)")
    _add_specialist_args(review_p)

    plan_p = sub.add_parser("plan", help="Eng Manager architecture gate on call graph (/plan)")
    _add_specialist_args(plan_p)

    sec_p = sub.add_parser("security", help="CSO threat model & auth audit on changed attack surface (/security)")
    _add_specialist_args(sec_p)

    qa_p = sub.add_parser("qa", help="QA Lead: verify edge cases and generate regression tests (/qa)")
    _add_specialist_args(qa_p)

    ship_p = sub.add_parser("ship", help="Release Engineer: pre-flight checks and PR notes (/ship)")
    _add_specialist_args(ship_p)

    debug_p = sub.add_parser("debug", help="Root cause debugger tracing AST call graph (/debug)")
    _add_specialist_args(debug_p)

    strat_p = sub.add_parser("strategy", help="Founder Strategy: 6 forcing questions to reframe scope (/strategy)")
    _add_specialist_args(strat_p)

    return parser


def _load_cfg(root: Path) -> AppConfig:
    root = root.resolve()
    cfg = load_config(root)
    save_config(cfg)
    return cfg


def _intercept_slash_commands(argv: list[str]) -> list[str]:
    """Intercept slash command aliases like '/', '/reduce', '/review', '/plan', etc. and map to commands.

    Also handles edge cases:
    - Shell expanding '/' to the root directory path on some systems
    - Windows path separators
    - Bare 'r' or 'rt' as shorthand aliases
    - Specialist roles: /review, /plan, /security, /qa, /ship, /debug, /strategy
    """
    if not argv:
        return argv
    first = argv[0]
    # Normalize: treat bare '/', root-dir path variants, and known slash aliases
    _slash_aliases = {"/", "/reduce", "/reducetoken", "/caveman", "/opt", "/raw", "r", "rt"}
    _raw_aliases = {"/caveman", "/raw"}
    if first in _slash_aliases:
        mode_lvl = "raw" if first in _raw_aliases else "full"
        return ["use", "--caveman", mode_lvl, "--copy", "--print"] + argv[1:]

    # Dedicated slash commands
    _role_cmd_map = {
        "/review": "review",
        "/plan": "plan",
        "/security": "security",
        "/cso": "security",
        "/qa": "qa",
        "/ship": "ship",
        "/debug": "debug",
        "/investigate": "debug",
        "/strategy": "strategy",
    }
    if first in _role_cmd_map:
        target_cmd = _role_cmd_map[first]
        return [target_cmd, "--copy", "--print"] + argv[1:]

    return argv




def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    argv = _intercept_slash_commands(argv)
    args = build_parser().parse_args(argv)
    cfg = _load_cfg(args.project_root)

    if args.command == "init":
        print(f"initialized: {cfg.state_dir}")
        return 0

    if args.command == "clean":
        files_removed = []
        for name in ("graph.db", "graph.db-wal", "graph.db-shm", "watch.pid", "watch.log"):
            p = cfg.state_dir / name
            if p.exists():
                try:
                    p.unlink(missing_ok=True)
                    files_removed.append(name)
                except OSError:
                    pass
        if getattr(args, "all", False):
            assistant_dir = cfg.state_dir / "assistant"
            if assistant_dir.exists():
                try:
                    shutil.rmtree(assistant_dir, ignore_errors=True)
                    files_removed.append("assistant/")
                except OSError:
                    pass
        payload = {"cleaned": True, "removed": files_removed, "state_dir": str(cfg.state_dir)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"clean_complete: removed {len(files_removed)} state item(s) from {cfg.state_dir}")
        return 0

    if args.command == "setup":
        analyzer = Analyzer(cfg)
        try:
            build_summary = analyzer.build_graph()
        finally:
            analyzer.close()

        install_result = install_integrations(cfg, start_watcher=not args.no_watch)
        specialist_cmds = install_all_specialist_slash_commands(cfg.project_root)
        payload = {
            "build": build_summary,
            "install": {
                "configured_tools": install_result.configured_tools,
                "hooks_installed": install_result.hooks_installed,
                "watcher_started": install_result.watcher_started,
                "specialist_commands": specialist_cmds,
                "notes": install_result.notes,
            },
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            import platform
            print()
            print("=" * 65)
            print("  ⚡ ReduceToken Setup Complete!")
            print("=" * 65)
            print(f"  Files indexed : {build_summary['tracked']}")
            print(f"  Processed     : {build_summary['processed']}")
            if install_result.configured_tools:
                print(f"  Integrations  : {', '.join(install_result.configured_tools)}")
            if install_result.hooks_installed:
                print(f"  Git hooks     : {', '.join(install_result.hooks_installed)}")
            print()
            print("  Universal Slash Commands Installed Globally (~/.claude/commands/):")
            print("    /reduce       - General Blast-Radius Context Optimizer")
            print("    /reducetoken  - Direct Mode (zero monologue, instant code)")
            print("    /review       - Staff Engineer Code Review on blast radius")
            print("    /plan         - Engineering Manager Architecture Gate")
            print("    /security     - CSO Threat Model & Security Audit")
            print("    /qa           - QA Lead Regression & Edge Case Verification")
            print("    /ship         - Release Engineer Pre-Flight & PR Summary")
            print("    /debug        - Root Cause Debugger & Dependency Tracer")
            print("    /strategy     - Founder Strategy & Scope Forcing Questions")
            print("  → Works in ALL projects across your machine!")
            print()
            print("  CLI Quick Commands:")
            print("    token-reduce /          (or 'tr /')")
            print("    token-reduce review")
            print("    token-reduce plan")
            print("    token-reduce security")
            print("    token-reduce qa")
            print("    token-reduce ship")

            if platform.system() == "Windows":
                import sysconfig
                scripts_dir = sysconfig.get_path("scripts")
                print()
                print("  Windows PATH note:")
                print("    If 'token-reduce' is not found, add this to your PATH:")
                print(f"    {scripts_dir}")
                print("    Then restart your terminal / PowerShell.")
            print("=" * 65)
            print()
            for note in install_result.notes:
                print(f"note: {note}")

        return 0



    if args.command == "install":
        result = install_integrations(cfg, start_watcher=not args.no_watch)
        payload = {
            "configured_tools": result.configured_tools,
            "hooks_installed": result.hooks_installed,
            "watcher_started": result.watcher_started,
            "notes": result.notes,
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"configured_tools={','.join(result.configured_tools) or 'none'}")
            print(f"hooks_installed={','.join(result.hooks_installed) or 'none'}")
            print(f"watcher_started={result.watcher_started}")
            for note in result.notes:
                print(f"note: {note}")
        return 0

    analyzer = Analyzer(cfg)
    try:
        if args.command == "build":
            summary = analyzer.build_graph()
            if args.json:
                print(json.dumps(summary, indent=2))
            else:
                print(
                    " ".join(
                        [
                            f"processed={summary['processed']}",
                            f"unchanged={summary['unchanged']}",
                            f"removed={summary['removed']}",
                            f"tracked={summary['tracked']}",
                        ]
                    )
                )
            return 0

        if args.command == "sync":
            files: list[Path] = [Path(item) for item in args.files]
            if args.git_head:
                files.extend(analyzer.changed_files_from_head())
            if args.worktree:
                files.extend(analyzer.changed_files_from_worktree())

            deduped: list[Path] = []
            seen: set[str] = set()
            for path in files:
                key = str(path)
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(path)

            summary = analyzer.sync_files(deduped)
            if args.json:
                print(json.dumps(summary, indent=2))
            else:
                print(f"parsed={summary['parsed']} skipped={summary['skipped']} removed={summary['removed']}")
            return 0

        if args.command == "blast":
            changed = [Path(item) for item in args.changed]
            blast = analyzer.blast_radius(changed, max_depth=args.depth)
            if args.json:
                print(json.dumps([{"node": node, "distance": distance} for node, distance in blast], indent=2))
            else:
                for node, distance in blast:
                    print(f"{distance}\t{node}")
            return 0

        if args.command == "context":
            changed = [Path(item) for item in args.changed]
            blast = analyzer.blast_radius(changed, max_depth=args.depth)
            changed_rel = []
            for p in changed:
                resolved = (p if p.is_absolute() else analyzer.project_root / p).resolve()
                try:
                    rel = str(resolved.relative_to(analyzer.project_root)).replace("\\", "/")
                except ValueError:
                    continue
                changed_rel.append(rel)
            pack = build_context_pack(
                config=cfg,
                store=analyzer.store,
                blast=blast,
                changed=changed_rel,
                max_files=args.max_files,
                max_tokens=args.max_tokens,
                caveman=getattr(args, "caveman", "full"),
            )
            payload = pack.to_json()
            if args.out:
                args.out.write_text(payload, encoding="utf-8")
                print(str(args.out))
            elif getattr(args, "print_prompt", False):
                print(pack.to_markdown())
            else:
                print(payload)
            return 0

        if args.command == "use":
            caveman_lvl = getattr(args, "caveman", "full")
            try:
                result = run_use_flow(
                    config=cfg,
                    analyzer=analyzer,
                    assistant=args.assistant,
                    changed_inputs=args.changed,
                    depth=args.depth,
                    max_files=args.max_files,
                    out_dir=args.out_dir,
                    max_tokens=args.max_tokens,
                    caveman=caveman_lvl,
                )
            except ValueError as err:
                print(f"error: {err}", file=sys.stderr)
                return 2

            prompt_text = read_prompt(result)
            copied = False
            if getattr(args, "copy_prompt", False):
                copied = _copy_to_clipboard(prompt_text)

            out_savings = estimate_output_savings_pct(result.caveman)
            payload = {
                "assistant": result.assistant,
                "mode": "ReduceToken(AST+DirectEngine)",
                "graph_built": result.graph_built,
                "changed": result.changed,
                "sync": result.sync_summary,
                "context_json": result.context_json_path,
                "prompt_md": result.prompt_md_path,
                "estimated_tokens": result.estimated_tokens,
                "baseline_tokens": result.baseline_tokens,
                "token_reduction_pct": result.token_reduction_pct,
                "direct_mode": result.caveman,
                "estimated_output_savings_pct": out_savings,
                "clipboard_copied": copied,
            }

            launch_status = None
            launch_error = None
            if args.launch:
                launch_status, launch_error = _launch_assistant(
                    assistant=args.assistant,
                    prompt_text=prompt_text,
                    override_command=args.cmd,
                )
                payload["launch_status"] = launch_status
                if launch_error:
                    payload["launch_error"] = launch_error

            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                mode_lbl = "DIRECT" if result.caveman == "full" else result.caveman.upper()
                print(f"mode=ReduceToken(AST+DirectEngine) assistant={result.assistant}")
                print(f"changed={','.join(result.changed) or 'none'}")
                print(
                    f"tokens_input=~{result.estimated_tokens:,} "
                    f"baseline=~{result.baseline_tokens:,} "
                    f"saved={result.token_reduction_pct:.1f}%"
                )
                print(
                    f"reducetoken_mode={mode_lbl} (est_output_saved=~{out_savings:.0f}% + thinking_overridden)"
                )
                print(
                    f"sync_parsed={result.sync_summary['parsed']} sync_skipped={result.sync_summary['skipped']} sync_removed={result.sync_summary['removed']}"
                )
                print(f"context_json={result.context_json_path}")
                print(f"prompt_md={result.prompt_md_path}")
                if copied:
                    print("clipboard=copied ReduceToken prompt to system clipboard!")
                if args.print_prompt:
                    print("")
                    print(prompt_text)
                if args.launch:
                    print(f"launch_status={launch_status}")
                    if launch_error:
                        print(f"launch_error={launch_error}")
                if not args.print_prompt and not args.launch and not copied:
                    print("next: copy prompt_md content or run with --copy / --print / --launch.")
            return 0

        if args.command == "status":
            row = analyzer.store.conn.execute("SELECT COUNT(*) AS count FROM files").fetchone()
            file_count = int(row["count"]) if row else 0
            row = analyzer.store.conn.execute("SELECT COUNT(*) AS count FROM symbols").fetchone()
            symbol_count = int(row["count"]) if row else 0
            row = analyzer.store.conn.execute("SELECT COUNT(*) AS count FROM edges").fetchone()
            edge_count = int(row["count"]) if row else 0

            lang_rows = analyzer.store.conn.execute(
                "SELECT language, COUNT(*) AS count FROM files GROUP BY language ORDER BY count DESC"
            ).fetchall()
            languages = {r["language"]: int(r["count"]) for r in lang_rows}

            db_size_kb = 0.0
            if cfg.graph_db_path.exists():
                try:
                    db_size_kb = round(cfg.graph_db_path.stat().st_size / 1024, 1)
                except OSError:
                    pass

            pid_file = cfg.state_dir / "watch.pid"
            watcher_active = False
            if pid_file.exists():
                try:
                    import os
                    pid = int(pid_file.read_text(encoding="utf-8").strip())
                    os.kill(pid, 0)
                    watcher_active = True
                except (ValueError, OSError):
                    pass

            payload = {
                "project_root": cfg.project_root,
                "graph_db": str(cfg.graph_db_path),
                "db_size_kb": db_size_kb,
                "files": file_count,
                "symbols": symbol_count,
                "edges": edge_count,
                "languages": languages,
                "watcher_active": watcher_active,
            }
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                lang_str = ", ".join(f"{k}:{v}" for k, v in languages.items()) or "none"
                print(
                    f"files={file_count} symbols={symbol_count} edges={edge_count} "
                    f"db_size={db_size_kb}KB watcher_active={watcher_active}"
                )
                print(f"languages={lang_str}")
                print(f"graph_db={payload['graph_db']}")
            return 0

        if args.command in ("specialist", "review", "plan", "security", "qa", "ship", "debug", "strategy"):
            if getattr(args, "setup", False):
                installed_cmds = install_all_specialist_slash_commands(cfg.project_root)
                if args.json:
                    print(json.dumps({"specialist_installed": installed_cmds}, indent=2))
                else:
                    print(f"setup_complete: installed {len(installed_cmds)} slash command(s): {', '.join(installed_cmds)}")
                return 0

            caveman_lvl = getattr(args, "caveman", "full")
            role = args.command if args.command != "specialist" else getattr(args, "role", "review")
            try:
                spec_res = run_specialist_flow(
                    config=cfg,
                    analyzer=analyzer,
                    role=role,
                    assistant=args.assistant,
                    changed_inputs=args.changed,
                    depth=args.depth,
                    max_files=args.max_files,
                    max_tokens=args.max_tokens,
                    out_dir=args.out_dir,
                    caveman=caveman_lvl,
                )
            except ValueError as err:
                print(f"error: {err}", file=sys.stderr)
                return 2

            prompt_text = Path(spec_res.prompt_md_path).read_text(encoding="utf-8")
            copied = False
            if getattr(args, "copy_prompt", False):
                copied = _copy_to_clipboard(prompt_text)

            payload = {
                "framework": "ReduceToken",
                "role": spec_res.role_key,
                "title": spec_res.title,
                "command": spec_res.command,
                "assistant": args.assistant,
                "changed": spec_res.changed,
                "impacted_count": spec_res.impacted_count,
                "estimated_tokens": spec_res.estimated_tokens,
                "baseline_tokens": spec_res.baseline_tokens,
                "token_reduction_pct": spec_res.token_reduction_pct,
                "direct_mode": spec_res.caveman,
                "estimated_output_savings_pct": spec_res.caveman_savings_pct,
                "context_json": spec_res.context_json_path,
                "prompt_md": spec_res.prompt_md_path,
                "clipboard_copied": copied,
            }

            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                print(f"mode=ReduceToken role=\"{spec_res.title}\" command={spec_res.command}")
                print(f"changed={','.join(spec_res.changed) or 'none'}")
                print(
                    f"tokens_input=~{spec_res.estimated_tokens:,} "
                    f"baseline=~{spec_res.baseline_tokens:,} "
                    f"saved={spec_res.token_reduction_pct:.1f}%"
                )
                print(
                    f"reducetoken_mode=DIRECT (est_output_saved=~{spec_res.caveman_savings_pct:.0f}% + thinking_overridden)"
                )
                print(f"prompt_md={spec_res.prompt_md_path}")
                if copied:
                    print(f"clipboard=copied {spec_res.command} prompt to system clipboard!")
                if getattr(args, "print_prompt", False):
                    print("")
                    print(prompt_text)
            return 0


        if args.command == "watch":
            watcher = Watcher(cfg)
            watcher.run(interval_seconds=args.interval)
            return 0


        print("unknown command", file=sys.stderr)
        return 2
    finally:
        analyzer.close()


def _copy_to_clipboard(text: str) -> bool:
    for cmd in (["pbcopy"], ["xclip", "-selection", "clipboard"], ["wl-copy"], ["clip"]):
        if shutil.which(cmd[0]):
            try:
                proc = subprocess.run(cmd, input=text, text=True, check=False)
                if proc.returncode == 0:
                    return True
            except OSError:
                pass
    return False


def _launch_assistant(assistant: str, prompt_text: str, override_command: str | None) -> tuple[str, str | None]:
    command_text = override_command or default_launch_command(assistant)
    if not command_text:
        return "not_configured", "No default launch command for this assistant. Use --cmd."

    argv = shlex.split(command_text)
    if not argv:
        return "invalid_command", "Launch command is empty."

    binary = argv[0]
    if shutil.which(binary) is None:
        return "not_found", f"Command not found in PATH: {binary}"

    try:
        proc = subprocess.run(argv, input=prompt_text, text=True, check=False)
        if proc.returncode != 0:
            return "failed", f"Assistant CLI exited with code {proc.returncode}"
        return "ok", None
    except OSError as err:
        return "failed", str(err)


if __name__ == "__main__":
    raise SystemExit(main())
