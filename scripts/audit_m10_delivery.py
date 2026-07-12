from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_m10_dashboard import FORBIDDEN, recursive_keys


PATH_PATTERN = re.compile(r"(?:[A-Za-z]:\\|/(?:home|Users|root|tmp)/)")
SECRET_PATTERN = re.compile(r"(?i)(?:api[_-]?key\s*[:=]|authorization\s*[:=]|bearer\s+[a-z0-9._-]+)")


def audit(delivery_dir: Path) -> dict[str, Any]:
    expected = {"index.html", "data.json"}
    files = {path.name: path for path in delivery_dir.iterdir() if path.is_file()}
    missing = sorted(expected - set(files))
    errors = [f"missing:{name}" for name in missing]
    data = None
    if "data.json" in files:
        try:
            data = json.loads(files["data.json"].read_text(encoding="utf-8"))
            forbidden = FORBIDDEN & recursive_keys(data)
            if forbidden:
                errors.append("forbidden_fields:" + ",".join(sorted(forbidden)))
        except (OSError, json.JSONDecodeError):
            errors.append("invalid:data.json")
    checksums = {}
    for name, path in sorted(files.items()):
        content = path.read_text(encoding="utf-8")
        checksums[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if PATH_PATTERN.search(content):
            errors.append("absolute_path:" + name)
        if SECRET_PATTERN.search(content):
            errors.append("credential_pattern:" + name)
    if data is not None and data.get("strict_verifier", {}).get("valid") is not True:
        errors.append("strict_verifier_not_valid")
    return {"valid": not errors, "errors": errors, "checksums": checksums, "file_count": len(files)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delivery-dir", required=True)
    args = parser.parse_args()
    try:
        result = audit(Path(args.delivery_dir))
    except OSError as error:
        print(f"delivery audit failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
