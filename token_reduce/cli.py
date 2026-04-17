from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from .analyzer import Analyzer
from .config import AppConfig, load_config, save_config
from .context_pack import build_context_pack
from .easy_mode import ASSISTANT_CHOICES, default_launch_command, read_prompt, run_use_flow
from .installer import install_integrations
from .watcher import Watcher


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="token-reduce", description="Incremental code knowledge graph for AI context reduction")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root (default: current directory)")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create config and graph state directory")

    setup = sub.add_parser("setup", help="One-time setup: init + build + install")
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
    context.add_argument("--out", type=Path, default=None, help="Write context JSON to file")

    use = sub.add_parser("use", help="Easy daily command: auto-sync + context + ready prompt")
    use.add_argument("--assistant", choices=ASSISTANT_CHOICES, default="generic", help="Prompt style template")
    use.add_argument("--changed", nargs="*", default=[], help="Optional changed files; if empty auto-detect from git")
    use.add_argument("--depth", type=int, default=None, help="Traversal depth")
    use.add_argument("--max-files", type=int, default=None, help="Limit impacted files")
    use.add_argument("--out-dir", type=Path, default=None, help="Output directory for context and prompt files")
    use.add_argument("--print", dest="print_prompt", action="store_true", help="Print generated prompt markdown to stdout")
    use.add_argument("--launch", action="store_true", help="Launch assistant CLI and send generated prompt over stdin")
    use.add_argument("--cmd", type=str, default=None, help="Override launch command, e.g. 'gemini'")
    use.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    watch = sub.add_parser("watch", help="Watch filesystem and sync graph incrementally")
    watch.add_argument("--interval", type=float, default=None, help="Polling interval seconds")

    install = sub.add_parser("install", help="Install editor/tool integrations + hooks + watcher")
    install.add_argument("--no-watch", action="store_true", help="Skip starting watcher")
    install.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    status = sub.add_parser("status", help="Show graph metadata")
    status.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    return parser


def _load_cfg(root: Path) -> AppConfig:
    root = root.resolve()
    cfg = load_config(root)
    save_config(cfg)
    return cfg


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = _load_cfg(args.project_root)

    if args.command == "init":
        print(f"initialized: {cfg.state_dir}")
        return 0

    if args.command == "setup":
        analyzer = Analyzer(cfg)
        try:
            build_summary = analyzer.build_graph()
        finally:
            analyzer.close()

        install_result = install_integrations(cfg, start_watcher=not args.no_watch)
        payload = {
            "build": build_summary,
            "install": {
                "configured_tools": install_result.configured_tools,
                "hooks_installed": install_result.hooks_installed,
                "watcher_started": install_result.watcher_started,
                "notes": install_result.notes,
            },
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(
                " ".join(
                    [
                        "setup_complete",
                        f"tracked={build_summary['tracked']}",
                        f"processed={build_summary['processed']}",
                        f"watcher_started={install_result.watcher_started}",
                    ]
                )
            )
            if install_result.configured_tools:
                print(f"configured_tools={','.join(install_result.configured_tools)}")
            if install_result.hooks_installed:
                print(f"hooks_installed={','.join(install_result.hooks_installed)}")
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
            pack = build_context_pack(cfg, analyzer.store, blast, changed_rel, max_files=args.max_files)
            payload = pack.to_json()
            if args.out:
                args.out.write_text(payload, encoding="utf-8")
                print(str(args.out))
            else:
                print(payload)
            return 0

        if args.command == "use":
            try:
                result = run_use_flow(
                    config=cfg,
                    analyzer=analyzer,
                    assistant=args.assistant,
                    changed_inputs=args.changed,
                    depth=args.depth,
                    max_files=args.max_files,
                    out_dir=args.out_dir,
                )
            except ValueError as err:
                print(f"error: {err}", file=sys.stderr)
                return 2
            payload = {
                "assistant": result.assistant,
                "graph_built": result.graph_built,
                "changed": result.changed,
                "sync": result.sync_summary,
                "context_json": result.context_json_path,
                "prompt_md": result.prompt_md_path,
            }
            prompt_text = read_prompt(result)

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
                print(f"assistant={result.assistant}")
                print(f"changed={','.join(result.changed) or 'none'}")
                print(
                    f"sync_parsed={result.sync_summary['parsed']} sync_skipped={result.sync_summary['skipped']} sync_removed={result.sync_summary['removed']}"
                )
                print(f"context_json={result.context_json_path}")
                print(f"prompt_md={result.prompt_md_path}")
                if args.print_prompt:
                    print("")
                    print(prompt_text)
                if args.launch:
                    print(f"launch_status={launch_status}")
                    if launch_error:
                        print(f"launch_error={launch_error}")
                if not args.print_prompt and not args.launch:
                    print("next: copy prompt_md content and paste it into your AI assistant.")
            return 0

        if args.command == "status":
            row = analyzer.store.conn.execute("SELECT COUNT(*) AS count FROM files").fetchone()
            file_count = int(row["count"]) if row else 0
            row = analyzer.store.conn.execute("SELECT COUNT(*) AS count FROM symbols").fetchone()
            symbol_count = int(row["count"]) if row else 0
            row = analyzer.store.conn.execute("SELECT COUNT(*) AS count FROM edges").fetchone()
            edge_count = int(row["count"]) if row else 0
            payload = {
                "project_root": cfg.project_root,
                "graph_db": str(cfg.graph_db_path),
                "files": file_count,
                "symbols": symbol_count,
                "edges": edge_count,
            }
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                print(
                    f"files={payload['files']} symbols={payload['symbols']} edges={payload['edges']} graph_db={payload['graph_db']}"
                )
            return 0

        if args.command == "watch":
            watcher = Watcher(cfg)
            watcher.run(interval_seconds=args.interval)
            return 0

        print("unknown command", file=sys.stderr)
        return 2
    finally:
        analyzer.close()


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
