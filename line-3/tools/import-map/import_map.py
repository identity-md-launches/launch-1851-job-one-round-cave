#!/usr/bin/env python3
"""Map Python source imports without importing or executing project code."""

import argparse
import ast
import json
from pathlib import Path
import sys


SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__", ".venv", "venv", "node_modules"}


def source_files(root):
    """Yield regular Python files beneath root in reproducible path order."""
    for path in sorted(root.rglob("*.py")):
        if path.is_symlink() or not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS or part.startswith(".") for part in relative.parts[:-1]):
            continue
        yield path


def module_name(relative):
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def is_main_guard(node):
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq) or len(test.comparators) != 1:
        return False
    pair = (test.left, test.comparators[0])
    return any(isinstance(a, ast.Name) and a.id == "__name__" and isinstance(b, ast.Constant) and b.value == "__main__" for a, b in (pair, pair[::-1]))


def package_of(module, is_package):
    return module if is_package else module.rpartition(".")[0]


def relative_anchor(module, is_package, level, name):
    package = package_of(module, is_package)
    parts = package.split(".") if package else []
    if level > len(parts):
        return None
    prefix = parts[:len(parts) - level + 1]
    if name:
        prefix.extend(name.split("."))
    return ".".join(prefix)


def cycles(graph):
    """Tarjan's algorithm, with deterministic output."""
    index = 0
    indices = {}
    low = {}
    stack = []
    on_stack = set()
    result = []

    def visit(node):
        nonlocal index
        indices[node] = low[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in sorted(graph[node]):
            if target not in indices:
                visit(target)
                low[node] = min(low[node], low[target])
            elif target in on_stack:
                low[node] = min(low[node], indices[target])
        if low[node] == indices[node]:
            group = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                group.append(member)
                if member == node:
                    break
            if len(group) > 1 or node in graph[node]:
                result.append(sorted(group))

    for node in sorted(graph):
        if node not in indices:
            visit(node)
    return sorted(result)


def inspect(root):
    paths = {}
    for path in source_files(root):
        relative = path.relative_to(root)
        name = module_name(relative)
        if name:
            paths[name] = relative.as_posix()
    modules = set(paths)
    namespaces = {".".join(name.split(".")[:i]) for name in modules for i in range(1, len(name.split(".")))}
    local_names = modules | namespaces
    local_roots = {name.split(".")[0] for name in local_names}
    graph = {name: set() for name in modules}
    records = []
    issues = []

    for name, relative in sorted(paths.items()):
        record = {"module": name, "path": relative, "entrypoint": False, "imports": [], "dynamic_import_lines": []}
        records.append(record)
        try:
            # Explicit UTF-8 matches the default source encoding of Python 3.
            source = (root / relative).read_text(encoding="utf-8")
            tree = ast.parse(source, filename=relative)
        except (SyntaxError, UnicodeError) as exc:
            issues.append({"type": "parse_error", "path": relative, "line": getattr(exc, "lineno", None), "detail": str(exc)})
            continue

        is_package = Path(relative).name == "__init__.py"
        record["entrypoint"] = any(is_main_guard(node) for node in ast.walk(tree))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and (
                isinstance(node.func, ast.Name) and node.func.id == "__import__"
                or isinstance(node.func, ast.Attribute) and node.func.attr == "import_module"
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "importlib"
            ):
                record["dynamic_import_lines"].append(node.lineno)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = alias.name
                    if target in modules:
                        kind, resolved = "local", target
                    elif target in namespaces:
                        kind, resolved = "local_namespace", target
                    elif target.split(".")[0] in local_roots:
                        kind, resolved = "unresolved_local", None
                    else:
                        kind, resolved = "external", None
                    entry = {"line": node.lineno, "target": target, "kind": kind}
                    if resolved:
                        entry["resolved"] = resolved
                    record["imports"].append(entry)
                    if kind == "local":
                        graph[name].add(resolved)
                    if kind == "unresolved_local":
                        issues.append({"type": kind, "path": relative, "line": node.lineno, "target": target})
            elif isinstance(node, ast.ImportFrom):
                anchor = relative_anchor(name, is_package, node.level, node.module) if node.level else node.module
                spelling = "." * node.level + (node.module or "")
                if not anchor:
                    kind, resolved = ("unresolved_relative" if node.level else "external"), None
                elif anchor in modules:
                    kind, resolved = "local", anchor
                elif anchor in namespaces:
                    kind, resolved = "local_namespace", anchor
                elif node.level or anchor.split(".")[0] in local_roots:
                    kind, resolved = "unresolved_local", None
                else:
                    kind, resolved = "external", None
                for alias in node.names:
                    child = anchor + "." + alias.name if anchor and alias.name != "*" else None
                    child_resolved = child if child in modules else None
                    final_resolved = child_resolved or resolved
                    final_kind = "local" if child_resolved else kind
                    target = spelling + " import " + alias.name
                    entry = {"line": node.lineno, "target": target, "kind": final_kind}
                    if final_resolved:
                        entry["resolved"] = final_resolved
                    record["imports"].append(entry)
                    if final_resolved in modules:
                        graph[name].add(final_resolved)
                    if final_kind.startswith("unresolved"):
                        issues.append({"type": final_kind, "path": relative, "line": node.lineno, "target": target})
        record["imports"].sort(key=lambda item: (item["line"], item["target"]))
        record["dynamic_import_lines"] = sorted(set(record["dynamic_import_lines"]))

    issues.sort(key=lambda item: (item["path"], item.get("line") or 0, item["type"], item.get("target", "")))
    edges = [{"from": name, "to": target} for name in sorted(graph) for target in sorted(graph[name])]
    return {"modules": records, "edges": edges, "cycles": cycles(graph), "issues": issues,
            "summary": {"module_count": len(records), "local_edge_count": len(edges),
                        "cycle_count": len(cycles(graph)), "issue_count": len(issues),
                        "entrypoints": [record["module"] for record in records if record["entrypoint"]]}}


def format_text(report):
    lines = [f"Modules: {report['summary']['module_count']}; local edges: {report['summary']['local_edge_count']}; cycles: {report['summary']['cycle_count']}; issues: {report['summary']['issue_count']}"]
    for record in report["modules"]:
        suffix = " [entry point]" if record["entrypoint"] else ""
        lines.append(f"{record['module']} ({record['path']}){suffix}")
        for item in record["imports"]:
            via = f" -> {item['resolved']}" if "resolved" in item else ""
            lines.append(f"  {item['line']}: {item['kind']}: {item['target']}{via}")
        for line in record["dynamic_import_lines"]:
            lines.append(f"  {line}: dynamic import call; target may be unknown")
    for group in report["cycles"]:
        lines.append("Cycle: " + " <-> ".join(group))
    for issue in report["issues"]:
        lines.append(f"Issue: {issue['path']}:{issue.get('line') or '?'} {issue['type']} {issue.get('target', issue.get('detail', ''))}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Python import root to inspect")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    parser.add_argument("--strict", action="store_true", help="exit 1 for cycles or issues")
    args = parser.parse_args(argv)
    if not args.root.is_dir():
        parser.error("root must be an existing directory")
    report = inspect(args.root)
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else format_text(report))
    return 1 if args.strict and (report["cycles"] or report["issues"]) else 0


if __name__ == "__main__":
    sys.exit(main())
