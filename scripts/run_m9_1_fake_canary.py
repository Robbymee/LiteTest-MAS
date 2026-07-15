"""生成并验证 M9.1 fake canary，不调用真实模型。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.verify_m9_1_spec import verify_fake_canary


def main() -> int:
    """为一个公开任务写入独立 fake canary 记录。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    item = next(item for item in spec["task_plan"] if item["experiment_group"] == "S1" and item["dataset"] == "mbpp" and item["seed"] == 42)
    record = {"schema_version": "1.0", **item, "result_scope": "m9_1_fake_canary", "final_status": "completed_success", "parse_status": "success", "task_success": True, "official_test_count": 0, "official_test_pass_count": 0, "public_leakage_count": 0}
    errors = verify_fake_canary(record, spec)
    if errors:
        raise SystemExit("fake_canary_failed:" + ",".join(errors))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid": True, "result_scope": record["result_scope"], "task_id": record["task_id"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
