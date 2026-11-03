"""Inventory exported HTTP functions without importing application code or SDKs."""
import argparse
import ast
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
        for name in node.names:
            if name.name in modules[node.module]:
                exported.add(name.asname or name.name)
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
