"""Read-only validation of the sole Firebase CLI root; no SDK dependencies."""
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def validate(root: Path) -> list[str]:
    failures = []
    try:
        manifest = json.loads((root / "firebase.json").read_text())
        aliases = json.loads((root / ".firebaserc").read_text())["projects"]
        catalog = json.loads((ROOT / "mcp-backend/functions/config/environment_catalog.json").read_text())["environments"]
    except (OSError, ValueError, KeyError):
        return ["Missing or invalid Firebase manifest, aliases, or environment catalog"]
    excluded = {"node_modules", ".git", ".venv", "venv", ".worktrees", ".superpowers", ".next"}
    duplicate_names = {"firebase.json", ".firebaserc", "firestore.rules", "firestore.indexes.json", "storage.rules"}
    for directory, subdirs, files in os.walk(root):
        subdirs[:] = [item for item in subdirs if item not in excluded]
        for name in files:
            item = Path(directory) / name
            if name in duplicate_names and item.parent != root:
                failures.append(f"Duplicate Firebase resource file: {item.relative_to(root)}")
    if "default" in aliases or set(aliases) != {"staging", "production"}:
        failures.append("Firebase aliases must be explicit staging and production only")
    for name in ("staging", "production"):
        if aliases.get(name) != catalog[name]["project_id"]:
            failures.append(f"Firebase alias mismatch: {name}")
    functions = manifest.get("functions", [])
    if len(functions) != 1 or functions[0].get("source") != "mcp-backend/functions":
        failures.append("Functions source must be mcp-backend/functions")
    if not functions or functions[0].get("runtime") != "python311":
        failures.append("Functions runtime must be python311")
    if any("region" in item for item in functions):
        failures.append("Functions region belongs in decorators, not the manifest")
    if manifest.get("hosting", {}).get("source") != "mcp-website":
        failures.append("Hosting source must be mcp-website")
    for key in ("auth", "functions", "firestore", "pubsub", "storage"):
        item = manifest.get("emulators", {}).get(key, {})
        if not item.get("port") or item.get("host") != "127.0.0.1":
            failures.append(f"Missing loopback emulator configuration: {key}")
    for service, keys in (("firestore", ("rules", "indexes")), ("storage", ("rules",))):
        for key in keys:
            filename = manifest.get(service, {}).get(key)
            if not filename or Path(filename).name != filename or not (root / filename).is_file():
                failures.append(f"Missing canonical {service} {key}")
    return failures


if __name__ == "__main__":
    issues = validate(ROOT)
    for issue in issues:
        print(issue, file=sys.stderr)
    if not issues:
        print("Canonical Firebase configuration: valid")
    sys.exit(1 if issues else 0)
