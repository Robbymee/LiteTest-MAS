"""独立的 Gated SharedMemory V2：门控、隔离并审计记忆复用。"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, asdict
from typing import Any, Iterable


_BLOCKED = {"hidden_reference_tests", "private", "candidate_code", "raw_response", "canonical_solution", "expected_output", "private_traceback", "api_key", "authorization"}


def _tokens(text: str) -> int:
    """使用轻量空白切分估算注入预算，不调用模型 tokenizer。"""
    return len(text.split())


@dataclass
class MemoryV2Metrics:
    """记录检索、门控、注入、复用和隔离指标。"""

    memory_query_count: int = 0
    memory_candidate_count: int = 0
    memory_hit_count: int = 0
    memory_accept_count: int = 0
    memory_reject_count: int = 0
    memory_abstain_count: int = 0
    memory_reuse_count: int = 0
    memory_injected_count: int = 0
    memory_injected_tokens: int = 0
    memory_write_count: int = 0
    memory_success_write_count: int = 0
    memory_eviction_count: int = 0
    memory_effective_reuse_count: int = 0
    group_isolation_violations: int = 0

    def as_dict(self) -> dict[str, Any]:
        """返回稳定指标并计算可定义的比率。"""
        data = asdict(self)
        data["memory_hit_rate"] = self.memory_hit_count / self.memory_query_count if self.memory_query_count else None
        data["memory_accept_rate"] = self.memory_accept_count / self.memory_candidate_count if self.memory_candidate_count else None
        data["memory_effective_reuse_rate"] = self.memory_effective_reuse_count / self.memory_reuse_count if self.memory_reuse_count else None
        return data


@dataclass
class MemoryV2Record:
    """包含来源、时间、任务语义和成功状态的脱敏记忆单元。"""

    memory_id: str
    source_agent: str
    created_at: str
    task_topic: str
    summary: str
    tags: tuple[str, ...]
    task_group: str
    task_type: str
    provenance: str
    confidence: float
    success_status: str
    reuse_count: int
    last_used_at: str | None
    schema_version: str = "2.0"
    dataset: str = ""
    seed: int = 0
    experiment_id: str = ""
    source_task_id: str = ""

    @property
    def token_count(self) -> int:
        """返回脱敏摘要的预算估算。"""
        return _tokens(self.summary)


class GatedSharedMemoryV2:
    """提供固定阈值、隔离边界和主动 abstain 的轻量共享记忆。"""

    def __init__(self, *, dataset: str, task_group: str, seed: int, experiment_id: str, top_k: int = 3, relevance_threshold: float = 0.5, confidence_threshold: float = 0.5, token_budget: int = 128, max_records: int = 32) -> None:
        if top_k < 1 or token_budget < 1 or max_records < 1 or not 0 <= relevance_threshold <= 1 or not 0 <= confidence_threshold <= 1:
            raise ValueError("invalid memory gate configuration")
        self.dataset, self.task_group, self.seed, self.experiment_id = dataset, task_group, seed, experiment_id
        self.top_k, self.relevance_threshold, self.confidence_threshold, self.token_budget, self.max_records = top_k, relevance_threshold, confidence_threshold, token_budget, max_records
        self.metrics = MemoryV2Metrics()
        self._records: list[MemoryV2Record] = []
        self._counter = 0

    @staticmethod
    def _check_public(values: Iterable[str]) -> None:
        """拒绝私有评测材料、候选代码和凭据。"""
        for value in values:
            if not isinstance(value, str) or any(blocked in value.lower() for blocked in _BLOCKED):
                raise ValueError("unsafe memory content")

    def write(self, *, source_agent: str, created_at: str, task_topic: str, summary: str, tags: Iterable[str], task_type: str, provenance: str, confidence: float, success_status: str, source_task_id: str) -> MemoryV2Record:
        """写入成功或失败经验；失败经验保留标记但默认不会被检索接受。"""
        if success_status not in {"success", "failure"} or not 0 <= confidence <= 1:
            raise ValueError("invalid memory status or confidence")
        tag_values = tuple(sorted(set(str(tag) for tag in tags)))
        self._check_public((source_agent, created_at, task_topic, summary, *tag_values, task_type, provenance, source_task_id))
        self._counter += 1
        record = MemoryV2Record(f"mem2_{self._counter:04d}", source_agent, created_at, task_topic, summary, tag_values, self.task_group, task_type, provenance, confidence, success_status, 0, None, dataset=self.dataset, seed=self.seed, experiment_id=self.experiment_id, source_task_id=source_task_id)
        self._records.append(record)
        self.metrics.memory_write_count += 1
        if success_status == "success":
            self.metrics.memory_success_write_count += 1
        while len(self._records) > self.max_records:
            self._records.pop(0)
            self.metrics.memory_eviction_count += 1
        return record

    def retrieve(self, *, task_id: str, topic: str, tags: Iterable[str], task_type: str) -> list[MemoryV2Record]:
        """检索并门控 top_k 记忆；没有满足条件时主动 abstain。"""
        self.metrics.memory_query_count += 1
        query_tags = set(str(tag) for tag in tags)
        self._check_public((task_id, topic, task_type, *query_tags))
        candidates: list[tuple[float, MemoryV2Record]] = []
        query_words = set(re.findall(r"[a-zA-Z0-9_]+", topic.lower()))
        for record in self._records:
            if record.dataset != self.dataset or record.task_group != self.task_group or record.seed != self.seed or record.experiment_id != self.experiment_id or record.source_task_id == task_id or record.success_status != "success":
                continue
            overlap = len(query_tags & set(record.tags)) / max(1, len(query_tags | set(record.tags)))
            words = set(re.findall(r"[a-zA-Z0-9_]+", record.task_topic.lower()))
            keyword = len(query_words & words) / max(1, len(query_words | words))
            score = 0.6 * overlap + 0.2 * keyword + 0.2 * float(record.task_type == task_type)
            candidates.append((score, record))
        candidates.sort(key=lambda item: (-item[0], item[1].memory_id))
        self.metrics.memory_candidate_count += len(candidates)
        if candidates:
            self.metrics.memory_hit_count += 1
        accepted: list[MemoryV2Record] = []
        budget = 0
        for score, record in candidates[: self.top_k]:
            if score < self.relevance_threshold or record.confidence < self.confidence_threshold or budget + record.token_count > self.token_budget:
                self.metrics.memory_reject_count += 1
                continue
            accepted.append(record)
            budget += record.token_count
        self.metrics.memory_accept_count += len(accepted)
        self.metrics.memory_injected_count += len(accepted)
        self.metrics.memory_injected_tokens += budget
        if not accepted:
            self.metrics.memory_abstain_count += 1
        return accepted

    def reuse(self, memory_id: str, *, task_id: str, task_success: bool) -> None:
        """记录下游实际引用及其最终可评测结果，不宣称因果提升。"""
        record = next((item for item in self._records if item.memory_id == memory_id), None)
        if record is None or record.source_task_id == task_id:
            self.metrics.group_isolation_violations += 1
            raise ValueError("memory reuse violates isolation")
        record.reuse_count += 1
        record.last_used_at = str(int(time.time()))
        self.metrics.memory_reuse_count += 1
        if task_success:
            self.metrics.memory_effective_reuse_count += 1

    def trace(self) -> dict[str, Any]:
        """返回公开元数据和指标，不包含私有任务材料。"""
        return {"schema_version": "2.0", "scope": {"dataset": self.dataset, "task_group": self.task_group, "seed": self.seed, "experiment_id": self.experiment_id}, "records": [asdict(record) for record in self._records], "metrics": self.metrics.as_dict()}
