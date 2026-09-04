from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .analyzer import Analyzer
from .config import load_config
from .context_pack import build_context_pack
from .risk import calculate_risk_score
from .specialists import run_specialist_flow


def get_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "reducetoken_get_context",
            "description": "Get minimal AST blast-radius context pack for changed files, saving 80-95% input tokens.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "changed_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of changed file paths relative to project root. If omitted, auto-detects from git.",
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Optional maximum context token budget (e.g. 2000).",
                    },
                    "caveman": {
                        "type": "string",
                        "enum": ["off", "mild", "full", "raw"],
                        "default": "full",
                        "description": "ReduceToken direct brevity mode.",
                    },
                },
            },
        },
        {
            "name": "reducetoken_blast_radius",
            "description": "Calculate which files and symbols are impacted by changes using the AST knowledge graph.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "changed_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of changed file paths relative to project root.",
                    },
                    "depth": {
                        "type": "integer",
                        "default": 2,
                        "description": "Graph traversal depth for dependents (default: 2).",
                    },
                },
            },
        },
        {
            "name": "reducetoken_risk_score",
            "description": "Calculate objective change risk score (0-100), detect test gaps, and identify sensitive modified components.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "changed_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of changed file paths relative to project root.",
                    },
                },
            },
        },
        {
            "name": "reducetoken_specialist",
            "description": "Execute role-based engineering specialist workflow (review, plan, security, qa, ship, debug).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "enum": ["review", "plan", "security", "qa", "ship", "debug", "strategy"],
                        "default": "review",
                        "description": "Specialist persona to assume.",
                    },
                    "changed_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of changed file paths.",
                    },
                },
                "required": ["role"],
            },
        },
    ]


def handle_mcp_request(request: dict[str, Any], project_root: Path) -> dict[str, Any] | None:
    """Handle a single MCP JSON-RPC 2.0 request."""
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "reducetoken",
                    "version": "1.0.0",
                },
                "capabilities": {
                    "tools": {},
                },
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": get_tool_definitions(),
            },
        }

    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        cfg = load_config(project_root)
        analyzer = Analyzer(cfg)
        try:
            if analyzer.store.conn.execute("SELECT COUNT(*) AS c FROM files").fetchone()["c"] == 0:
                analyzer.build_graph()

            if tool_name == "reducetoken_blast_radius":
                changed = [Path(p) for p in arguments.get("changed_files", [])]
                if not changed:
                    from .easy_mode import _resolve_changed
                    changed = _resolve_changed(analyzer, [])
                depth = arguments.get("depth", 2)
                blast = analyzer.blast_radius(changed, max_depth=depth)
                impacted = [
                    {"node": node, "distance": dist}
                    for node, dist in blast
                ]
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps({"changed": [str(c) for c in changed], "impacted": impacted}, indent=2)}
                        ]
                    },
                }

            if tool_name == "reducetoken_risk_score":
                from .easy_mode import _resolve_changed, _to_rel_paths
                changed = [Path(p) for p in arguments.get("changed_files", [])]
                if not changed:
                    changed = _resolve_changed(analyzer, [])
                changed_rel = _to_rel_paths(analyzer, changed)
                blast = analyzer.blast_radius(changed)
                report = calculate_risk_score(analyzer.store, changed_rel, blast)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps(report.to_dict(), indent=2)}
                        ]
                    },
                }

            if tool_name == "reducetoken_get_context":
                from .easy_mode import _resolve_changed, _to_rel_paths
                changed_in = arguments.get("changed_files", [])
                changed = [Path(p) for p in changed_in] if changed_in else _resolve_changed(analyzer, [])
                changed_rel = _to_rel_paths(analyzer, changed)
                blast = analyzer.blast_radius(changed)
                pack = build_context_pack(
                    config=cfg,
                    store=analyzer.store,
                    blast=blast,
                    changed=changed_rel,
                    max_tokens=arguments.get("max_tokens"),
                    caveman=arguments.get("caveman", "full"),
                )
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": pack.to_markdown(assistant="generic")}
                        ]
                    },
                }

            if tool_name == "reducetoken_specialist":
                role = arguments.get("role", "review")
                changed_in = arguments.get("changed_files", [])
                res = run_specialist_flow(
                    config=cfg,
                    analyzer=analyzer,
                    role=role,
                    assistant="generic",
                    changed_inputs=changed_in,
                )
                prompt_text = Path(res.prompt_md_path).read_text(encoding="utf-8")
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": prompt_text}
                        ]
                    },
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }
        finally:
            analyzer.close()

    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    return None


def run_mcp_server(project_root: Path | None = None) -> int:
    """Run the ReduceToken stdio MCP server."""
    root = project_root or Path.cwd()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        resp = handle_mcp_request(req, root)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

    return 0


def generate_mcp_config(root: Path | str) -> dict[str, Any]:
    """Generate the standard MCP configuration snippet for this project."""
    root_path = Path(root).resolve()
    return {
        "mcpServers": {
            "reducetoken": {
                "command": "token-reduce",
                "args": ["--project-root", str(root_path), "mcp"],
            }
        }
    }


def install_mcp_configs(root: Path | str) -> list[str]:
    """Install MCP configuration for Claude Desktop, Cursor, and VS Code."""
    root_path = Path(root).resolve()
    installed: list[str] = []
    cfg = generate_mcp_config(root_path)

    # 1. Cursor MCP config: .cursor/mcp.json
    cursor_mcp = root_path / ".cursor" / "mcp.json"
    cursor_mcp.parent.mkdir(parents=True, exist_ok=True)
    try:
        cursor_mcp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        installed.append("cursor-mcp")
    except OSError:
        pass

    # 2. VS Code / Copilot: .vscode/mcp.json
    vscode_mcp = root_path / ".vscode" / "mcp.json"
    vscode_mcp.parent.mkdir(parents=True, exist_ok=True)
    try:
        vscode_mcp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        installed.append("vscode-mcp")
    except OSError:
        pass

    # 3. Global Claude Desktop config if exists
    claude_desktop = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if claude_desktop.parent.exists():
        try:
            current: dict[str, Any] = {}
            if claude_desktop.exists():
                current = json.loads(claude_desktop.read_text(encoding="utf-8"))
            servers = current.setdefault("mcpServers", {})
            servers["reducetoken"] = cfg["mcpServers"]["reducetoken"]
            claude_desktop.write_text(json.dumps(current, indent=2), encoding="utf-8")
            installed.append("claude-desktop-mcp")
        except (OSError, json.JSONDecodeError):
            pass

    return installed
