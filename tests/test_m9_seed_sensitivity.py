from __future__ import annotations

from scripts.analyze_m9_seed_sensitivity import cluster_bootstrap_mean_ci, cluster_comparisons, seed_consistency


def record(group: str, seed: int, task_id: str, *, success: bool, tokens: int, candidate: str) -> dict:
    """构造仅含公共字段的三 seed 合成记录。"""
    return {
        "experiment_group": group, "dataset": "mbpp", "group_id": "group_1", "task_id": task_id, "seed": seed,
        "candidate_sha256": candidate, "task_success": success, "official_test_count": 2, "official_test_pass_count": 2 if success else 1,
        "official_test_pass_rate": 1.0 if success else 0.5, "total_tokens": tokens, "latency_seconds": 1.0,
        "state_vector_count": 0, "state_vector_bytes": 0, "memory_read_count": 0, "memory_hit_count": 0,
        "memory_reuse_count": 0, "memory_write_count": 0,
    }


def all_records() -> list[dict]:
    """构造四组、两个任务、三个 seed 的配对公共记录。"""
    return [
        record(group, seed, task_id, success=group != "G1", tokens=10 + seed, candidate=f"{group}-{task_id}")
        for group in ("G1", "G2", "G3", "G4")
        for task_id in ("task-1", "task-2")
        for seed in (42, 43, 44)
    ]


def test_seed_consistency_reports_full_three_seed_repetition():
    """验证跨 seed 重复率基于完整三条记录计算。"""
    rows = seed_consistency(all_records())
    g1 = next(row for row in rows if row["experiment_group"] == "G1")
    assert g1["candidate_sha256_all_seed_equal_rate"] == 1.0
    assert g1["task_success_all_seed_equal_rate"] == 1.0
    assert g1["total_tokens_all_seed_equal_rate"] == 0.0


def test_cluster_bootstrap_is_deterministic_and_uses_task_clusters():
    """验证 task-cluster Bootstrap 固定随机种子且每簇包含三个 seed。"""
    first = cluster_bootstrap_mean_ci([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], resamples=100, confidence=0.95, seed=20260711)
    second = cluster_bootstrap_mean_ci([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], resamples=100, confidence=0.95, seed=20260711)
    rows = cluster_comparisons(all_records(), bootstrap_seed=20260711, resamples=20, confidence=0.95)
    success = next(row for row in rows if row["treatment_group"] == "G2" and row["control_group"] == "G1" and row["metric"] == "task_success")
    assert first == second
    assert success["cluster_count"] == 2
    assert success["paired_count"] == 6
