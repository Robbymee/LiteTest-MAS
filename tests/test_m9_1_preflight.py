from __future__ import annotations

import json
from pathlib import Path

from scripts.run_m9_1_fake_canary import main
from scripts.verify_m9_1_spec import validate_spec, verify_fake_canary


ROOT = Path(__file__).resolve().parents[1]


def test_m9_1_spec_preflight_and_fake_canary_are_independent(tmp_path, monkeypatch):
    """验证 Spec 门槛和 fake canary 不调用模型且不冒充正式 scope。"""
    spec = json.loads((ROOT / "experiments/m9_1/spec.json").read_text(encoding="utf-8"))
    assert validate_spec(spec) == []
    item = next(item for item in spec["task_plan"] if item["experiment_group"] == "S1")
    record = {**item, "result_scope": "m9_1_fake_canary", "final_status": "completed_success"}
    assert verify_fake_canary(record, spec) == []
    output = tmp_path / "fake.json"
    monkeypatch.setattr("sys.argv", ["run_m9_1_fake_canary", "--spec", str(ROOT / "experiments/m9_1/spec.json"), "--output", str(output)])
    assert main() == 0 and json.loads(output.read_text(encoding="utf-8"))["result_scope"] == "m9_1_fake_canary"


def test_m9_1_preflight_rejects_formal_scope_fake_record():
    """验证 fake canary 不能伪装为 supplementary 正式结果。"""
    spec = json.loads((ROOT / "experiments/m9_1/spec.json").read_text(encoding="utf-8"))
    item = next(item for item in spec["task_plan"] if item["experiment_group"] == "S1")
    record = {**item, "result_scope": spec["result_scope"], "final_status": "completed_success"}
    assert "fake_scope" in verify_fake_canary(record, spec)
