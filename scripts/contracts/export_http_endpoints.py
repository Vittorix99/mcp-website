"""Inventory exported HTTP functions without importing application code or SDKs."""
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import sys


HTTP_DECORATORS = {
    "api.decorators.public_endpoint", "api.decorators.admin_endpoint",
    "api.decorators.member_endpoint", "firebase_functions.https_fn.on_request",
}


def _imports(tree):
    bindings = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for name in node.names:
                bindings[name.asname or name.name] = f"{node.module}.{name.name}"
        elif isinstance(node, ast.Import):
            for name in node.names:
                bindings[name.asname or name.name.split(".")[0]] = name.name if name.asname else name.name.split(".")[0]
    return bindings


def _qualified(node, bindings):
    if isinstance(node, ast.Call):
        return _qualified(node.func, bindings)
    if isinstance(node, ast.Name):
        return bindings.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        return f"{_qualified(node.value, bindings)}.{node.attr}"
    return ""


def _assert_single_binding(tree, names):
    def bindings(node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield node.name
            return  # Function/class locals do not replace module bindings.
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for item in node.names:
                yield item.asname or (item.name.split(".")[0] if isinstance(node, ast.Import) else item.name)
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            yield node.id
        for child in ast.iter_child_nodes(node):
            yield from bindings(child)

    counts = Counter(bindings(tree))
    if any(counts[name] != 1 for name in names):
        raise ValueError("Rebound API function or decorator")


def export_http_endpoints(root: Path) -> set[str]:
    functions = root / "mcp-backend/functions"
    main = ast.parse((functions / "main.py").read_text())
    modules = {}
    exported = set()
    for node in main.body:
        if not isinstance(node, ast.ImportFrom) or not (node.module or "").startswith("api."):
            continue
        if any(name.name == "*" for name in node.names):
            raise ValueError("Wildcard API exports are unsupported")
        if node.module not in modules:
            source = functions.joinpath(*node.module.split(".")).with_suffix(".py")
            tree = ast.parse(source.read_text())
            bindings = _imports(tree)
            modules[node.module] = {
                item.name for item in tree.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                and any(_qualified(decorator, bindings) in HTTP_DECORATORS for decorator in item.decorator_list)
            }
            decorator_bindings = {
                name for name, qualified in bindings.items()
                if qualified in HTTP_DECORATORS or qualified == "firebase_functions.https_fn"
            }
            _assert_single_binding(tree, modules[node.module] | decorator_bindings)
        for name in node.names:
            if name.name in modules[node.module]:
                exported.add(name.asname or name.name)
    _assert_single_binding(main, exported)
    return exported


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(sorted(export_http_endpoints(args.root))))
    except (OSError, SyntaxError, ValueError) as error:
        # SyntaxError text may contain a source line; never echo application values.
        print(f"API inventory rejected: {type(error).__name__}", file=sys.stderr)
        sys.exit(1)
