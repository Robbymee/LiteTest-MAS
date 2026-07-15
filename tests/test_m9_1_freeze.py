"""验证 M9.1 freeze 候选只绑定公开、可复核的实验输入。"""

from __future__ import annotations

import json
from pathlib import Path

from experiments.m9_1_verifier import spec_hash


ROOT = Path(__file__).resolve().parents[1]


def test_m9_1_freeze_manifest_matches_checked_in_spec():
    """验证 freeze 清单绑定指标修复实现和当前确定性 Spec。"""
    manifest = json.loads((ROOT / "experiments/m9_1/freeze_manifest.json").read_text(encoding="utf-8"))
    spec = json.loads((ROOT / "experiments/m9_1/spec.json").read_text(encoding="utf-8"))

    assert manifest["experiment_id"] == spec["experiment_id"]
    assert manifest["implementation_git_sha"] == spec["implementation_git_sha"]
    assert manifest["spec_sha256"] == spec_hash(spec)
    assert manifest["task_plan_sha256"] == spec["task_plan_sha256"]
    assert manifest["result_scope"] == spec["result_scope"]
    # 清单不能以字段形式写入候选代码或私有评测内容。
    assert not {"candidate_code", "hidden_reference_tests", "official_tests"} & set(manifest)
