from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


PYTHON_EXTENSIONS = {".py"}
NOTEBOOK_EXTENSIONS = {".ipynb"}
GENERIC_EXTENSIONS = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".scala",
    ".lua",
}


@dataclass(slots=True)
class Symbol:
    symbol_id: str
    path: str
    name: str
    kind: str
    language: str
    start_line: int
    end_line: int
    signature: str = ""


@dataclass(slots=True)
class Ref:
    path: str
    owner_id: str
    target_name: str
    kind: str


@dataclass(slots=True)
class ParseResult:
    path: str
    language: str
    imports: list[str] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    refs: list[Ref] = field(default_factory=list)


def language_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in PYTHON_EXTENSIONS:
        return "python"
    if suffix in NOTEBOOK_EXTENSIONS:
        return "notebook"
    if suffix in GENERIC_EXTENSIONS:
        return suffix.lstrip(".")
    return "unknown"


def symbol_id(path: str, name: str, kind: str, start_line: int) -> str:
    return f"sym::{path}::{kind}::{name}::{start_line}"


def parse_source(path: Path, project_root: Path) -> ParseResult:
    rel = str(path.relative_to(project_root)).replace("\\", "/")
    language = language_for_path(path)
    if language == "python":
        return _parse_python(path, rel, language)
    if language == "notebook":
        return _parse_notebook(path, rel)
    if language != "unknown":
        return _parse_generic(path, rel, language)
    return ParseResult(path=rel, language=language)


class _PythonAnalyzer(ast.NodeVisitor):
    def __init__(self, rel_path: str, language: str) -> None:
        self.rel_path = rel_path
        self.language = language
        self.imports: list[str] = []
        self.symbols: list[Symbol] = []
        self.refs: list[Ref] = []
        self._owner_stack: list[str] = []

    def _owner(self) -> str:
        return self._owner_stack[-1] if self._owner_stack else f"file::{self.rel_path}"

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        if node.level > 0:
            module = "." * node.level + module
        self.imports.append(module)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        sid = symbol_id(self.rel_path, node.name, "class", node.lineno)
        self.symbols.append(
            Symbol(
                symbol_id=sid,
                path=self.rel_path,
                name=node.name,
                kind="class",
                language=self.language,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                signature=f"class {node.name}",
            )
        )
        self._owner_stack.append(sid)
        for base in node.bases:
            base_name = _expr_name(base)
            if base_name:
                self.refs.append(Ref(path=self.rel_path, owner_id=sid, target_name=base_name, kind="inherits"))
        self.generic_visit(node)
        self._owner_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        sid = symbol_id(self.rel_path, node.name, "function", node.lineno)
        self.symbols.append(
            Symbol(
                symbol_id=sid,
                path=self.rel_path,
                name=node.name,
                kind="function",
                language=self.language,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                signature=f"def {node.name}(...)",
            )
        )
        self._owner_stack.append(sid)
        self.generic_visit(node)
        self._owner_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        sid = symbol_id(self.rel_path, node.name, "function", node.lineno)
        self.symbols.append(
            Symbol(
                symbol_id=sid,
                path=self.rel_path,
                name=node.name,
                kind="function",
                language=self.language,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                signature=f"async def {node.name}(...)",
            )
        )
        self._owner_stack.append(sid)
        self.generic_visit(node)
        self._owner_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        target = _expr_name(node.func)
        if target:
            self.refs.append(Ref(path=self.rel_path, owner_id=self._owner(), target_name=target, kind="calls"))
        self.generic_visit(node)


def _expr_name(expr: ast.expr) -> str:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    return ""


def _parse_python(path: Path, rel_path: str, language: str) -> ParseResult:
    source = path.read_text(encoding="utf-8", errors="replace")
    result = ParseResult(path=rel_path, language=language)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return result
    analyzer = _PythonAnalyzer(rel_path=rel_path, language=language)
    analyzer.visit(tree)
    result.imports = analyzer.imports
    result.symbols = analyzer.symbols
    result.refs = analyzer.refs
    return result


def _parse_notebook(path: Path, rel_path: str) -> ParseResult:
    result = ParseResult(path=rel_path, language="notebook")
    try:
        notebook = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return result

    cells = notebook.get("cells", [])
    line_offset = 0
    for idx, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        pseudo_path = f"{rel_path}#cell-{idx}"
        parsed = _parse_python_source_string(src, pseudo_path, "notebook", line_offset)
        result.imports.extend(parsed.imports)
        result.symbols.extend(parsed.symbols)
        result.refs.extend(parsed.refs)
        line_offset += src.count("\n") + 1
    return result


def _parse_python_source_string(source: str, rel_path: str, language: str, line_offset: int) -> ParseResult:
    result = ParseResult(path=rel_path, language=language)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return result
    analyzer = _PythonAnalyzer(rel_path=rel_path, language=language)
    analyzer.visit(tree)
    # offset notebook line ranges into parent file line-space
    for symbol in analyzer.symbols:
        symbol.start_line += line_offset
        symbol.end_line += line_offset
    result.imports = analyzer.imports
    result.symbols = analyzer.symbols
    result.refs = analyzer.refs
    return result


IMPORT_PATTERNS = [
    re.compile(r"^\s*import\s+([a-zA-Z0-9_./@-]+)", re.MULTILINE),
    re.compile(r"^\s*from\s+([a-zA-Z0-9_./@-]+)\s+import", re.MULTILINE),
    re.compile(r"import\s+.*?from\s+[\"']([^\"']+)[\"']", re.MULTILINE),
    re.compile(r"require\([\"']([^\"']+)[\"']\)"),
    re.compile(r"#include\s+[\"<]([^\">]+)[\">]"),
]

SYMBOL_PATTERNS = [
    ("class", re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)),
    (
        "function",
        re.compile(
            r"^\s*(?:def|function|func|fn)\s+([A-Za-z_][A-Za-z0-9_]*)|^\s*(?:public|private|protected)?\s*(?:static\s+)?[A-Za-z_<>,\[\]]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
            re.MULTILINE,
        ),
    ),
    ("function", re.compile(r"\bconst\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\([^)]*\)\s*=>")),
]

CALL_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
CALL_KEYWORDS = {
    "if",
    "for",
    "while",
    "switch",
    "return",
    "sizeof",
    "catch",
    "new",
    "super",
    "await",
}


def _parse_generic(path: Path, rel_path: str, language: str) -> ParseResult:
    text = path.read_text(encoding="utf-8", errors="replace")
    result = ParseResult(path=rel_path, language=language)
    file_owner = f"file::{rel_path}"

    for pattern in IMPORT_PATTERNS:
        result.imports.extend(match.group(1) for match in pattern.finditer(text))

    for kind, pattern in SYMBOL_PATTERNS:
        for match in pattern.finditer(text):
            name = match.group(1) or match.group(2)
            if not name:
                continue
            line = text.count("\n", 0, match.start()) + 1
            sid = symbol_id(rel_path, name, kind, line)
            result.symbols.append(
                Symbol(
                    symbol_id=sid,
                    path=rel_path,
                    name=name,
                    kind=kind,
                    language=language,
                    start_line=line,
                    end_line=line,
                    signature=f"{kind} {name}",
                )
            )

    for match in CALL_PATTERN.finditer(text):
        target = match.group(1)
        if target in CALL_KEYWORDS:
            continue
        result.refs.append(Ref(path=rel_path, owner_id=file_owner, target_name=target, kind="calls"))

    return result
