"""M9.1 独立 Runner 的计划和 S1-S4 语义，不复用 M9 G1-G4 配置。"""

from __future__ import annotations

from typing import Any


GROUPS = ("S1", "S2", "S3", "S4")


def group_config(group: str) -> dict[str, Any]:
    """返回 M9.1 实验组的独立组件配置。"""
    configs = {
        "S1": {"mode": "text", "state_enabled": False, "memory_enabled": False, "component": "text_baseline"},
        "S2": {"mode": "protocol", "state_enabled": False, "memory_enabled": False, "component": "compact_protocol_v2"},
        "S3": {"mode": "protocol", "state_enabled": True, "memory_enabled": False, "component": "compact_protocol_v2+state_vector_v2"},
        "S4": {"mode": "protocol", "state_enabled": True, "memory_enabled": True, "component": "compact_protocol_v2+state_vector_v2+gated_shared_memory_v2"},
    }
    if group not in configs:
        raise ValueError("unknown M9.1 experiment group")
    return dict(configs[group])


def plan(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """从 M9.1 Spec 返回不可变语义上的公开任务计划。"""
    if spec.get("experiment_groups") != list(GROUPS) or spec.get("task_plan_count") != 240:
        raise ValueError("invalid M9.1 plan scope")
    items = [dict(item) for item in spec["task_plan"]]
    if len(items) != 240 or len({(x["seed"], x["experiment_group"], x["dataset"], x["task_id"]) for x in items}) != 240:
        raise ValueError("invalid M9.1 task plan")
    return items


def select_plan(spec: dict[str, Any], combination: str | None = None) -> list[dict[str, Any]]:
    """按 S 组、数据集和 seed 选择十个公开任务。"""
    items = plan(spec)
    if combination is None:
        return items
    group, dataset, seed_text = combination.split(":")
    selected = [item for item in items if item["experiment_group"] == group and item["dataset"] == dataset and item["seed"] == int(seed_text)]
    if len(selected) != 10:
        raise ValueError("combination must resolve exactly ten tasks")
    return selected


def canary_item(spec: dict[str, Any], group: str, dataset: str, seed: int = 42) -> dict[str, Any]:
    """返回固定公开 canary 任务，不读取私有评测字段。"""
    item = next((item for item in plan(spec) if item["experiment_group"] == group and item["dataset"] == dataset and item["seed"] == seed), None)
    if item is None:
        raise ValueError("canary task not found")
    return item
