import pytest
from state.vector import StateVector,StateMetrics
def test_state_vector_stable_safe_and_limited():
 s=StateVector(task_phase='generation',agent_role='testgen',progress_flags=('ok',),memory_reference_ids=('m0001',));assert s.stable()==s.stable() and len(s.stable())<512
 with pytest.raises(ValueError):StateVector(task_phase='bad').stable()
 with pytest.raises(ValueError):StateVector(progress_flags=('canonical_solution',)).stable()
 with pytest.raises(ValueError):StateVector(progress_flags=('x'*100,)*10).stable()
