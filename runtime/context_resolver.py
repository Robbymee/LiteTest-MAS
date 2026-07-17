"""Resolve compact state and memory references at the executor boundary."""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from typing import Any, Iterable

from memory.gated_shared_memory_v2 import GatedSharedMemoryV2, MemoryV2Record
from state.vector_v2 import StateVectorError, StateVectorV2


class ExecutionContextError(ValueError):
    """Raised when an execution-context reference is invalid or unsafe."""


@dataclass(frozen=True)
class ResolvedExecutionContext:
    """Public state and memory content resolved for one executor request."""

    state: dict[str, Any] | None
    reusable_public_memory: tuple[dict[str, Any], ...]

    def state_json(self) -> str | None:
        """Return the compact state block inserted into the executor prompt."""
        if self.state is None:
            return None
        return json.dumps(self.state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def memory_json(self) -> str | None:
        """Return the exact public-memory block inserted into the prompt."""
        if not self.reusable_public_memory:
            return None
        return json.dumps(
            list(self.reusable_public_memory),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def prompt_suffix(self) -> str:
        """Render each resolved semantic block once for the executor."""
        sections: list[str] = []
        state_json = self.state_json()
        memory_json = self.memory_json()
        if state_json is not None:
            sections.append("resolved_state:\n" + state_json)
        if memory_json is not None:
            sections.append("reusable_public_memory:\n" + memory_json)
        return "\n".join(sections)

    @property
    def memory_injected_bytes(self) -> int:
        """Return UTF-8 bytes of the exact injected memory JSON block."""
        memory_json = self.memory_json()
        return len(memory_json.encode("utf-8")) if memory_json is not None else 0

    @property
    def memory_injected_tokens(self) -> int:
        """Return the whitespace_v1 estimate for the injected memory block."""
        memory_json = self.memory_json()
        return len(memory_json.split()) if memory_json is not None else 0


class ExecutionContextRegistry:
    """Store state bytes and resolve state and accepted memory references."""

    def __init__(self) -> None:
        self._state_vectors: dict[str, bytes] = {}

    def register_state(self, state_vector_id: str, payload: bytes) -> None:
        """Register an encoded StateVector under a unique public reference."""
        if not state_vector_id or not isinstance(payload, bytes):
            raise ExecutionContextError("invalid state vector registration")
        existing = self._state_vectors.get(state_vector_id)
        if existing is not None and existing != payload:
            raise ExecutionContextError("state vector id collision")
        self._state_vectors[state_vector_id] = payload

    def resolve(
        self,
        *,
        state_vector_id: str | None,
        memory_ids: Iterable[str],
        memory: GatedSharedMemoryV2 | None,
        task_id: str,
        expected_phase: str = "generation",
        expected_target_role: str = "executor",
    ) -> ResolvedExecutionContext:
        """Resolve and validate references for one isolated executor request."""
        state = self._resolve_state(
            state_vector_id,
            expected_phase=expected_phase,
            expected_target_role=expected_target_role,
        )
        ids = tuple(memory_ids)
        if ids and memory is None:
            raise ExecutionContextError("memory references require an isolated memory store")
        try:
            records = memory.resolve_accepted(ids, task_id=task_id) if memory is not None else []
        except ValueError as error:
            raise ExecutionContextError("invalid memory reference") from error
        public_memory = tuple(self._public_memory(record) for record in records)
        return ResolvedExecutionContext(state=state, reusable_public_memory=public_memory)

    def _resolve_state(
        self,
        state_vector_id: str | None,
        *,
        expected_phase: str,
        expected_target_role: str,
    ) -> dict[str, Any] | None:
        if state_vector_id is None:
            return None
        try:
            payload = self._state_vectors[state_vector_id]
        except KeyError as error:
            raise ExecutionContextError("unknown state vector id") from error
        try:
            state = StateVectorV2.decode(payload)
        except (StateVectorError, struct.error) as error:
            raise ExecutionContextError("invalid state vector bytes") from error
        if state.phase != expected_phase or state.target_role != expected_target_role:
            raise ExecutionContextError("state vector is not valid for this executor boundary")
        return {
            "error_code": state.error_code,
            "phase": state.phase,
            "progress_code": state.progress_code,
            "retry_count": state.retry_count,
        }

    @staticmethod
    def _public_memory(record: MemoryV2Record) -> dict[str, Any]:
        GatedSharedMemoryV2.check_public(
            (record.memory_id, record.summary, record.provenance)
        )
        return {
            "confidence": record.confidence,
            "memory_id": record.memory_id,
            "provenance": record.provenance,
            "summary": record.summary,
        }
