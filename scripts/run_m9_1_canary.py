"""执行 M9.1 S 组语义 canary 的计划校验；真实模型接入单独验收。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.m9_1_runner import canary_item, execute_canary, group_config


def main() -> int:
    """输出公开 canary 计划与组件配置，不生成正式结果。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--group", choices=("S1", "S2", "S3", "S4"), required=True)
    parser.add_argument("--dataset", choices=("mbpp", "humaneval"), required=True)
    parser.add_argument("--backend", choices=("mock", "openai_compatible"), default="mock")
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    if args.backend == "openai_compatible":
        record = execute_canary(ROOT, spec, args.group, args.dataset, Path("runs/m9_1_canary"), args.backend)
        print(json.dumps({"canary": True, "result_scope": record["result_scope"], "task_id": record["task_id"], "task_success": record["task_success"]}, ensure_ascii=False, sort_keys=True))
        return 0
    item = canary_item(spec, args.group, args.dataset)
    print(json.dumps({"canary": True, "result_scope": "m9_1_runner_canary", "backend": "mock", "task_id": item["task_id"], "experiment_group": item["experiment_group"], "dataset": item["dataset"], "component": group_config(args.group)["component"], "model_call": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
