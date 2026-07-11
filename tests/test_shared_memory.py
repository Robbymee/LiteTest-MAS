import json
import pytest
from memory.shared_memory import SharedMemory
def test_disabled_and_fifo_are_deterministic():
 off=SharedMemory(enabled=False);assert off.write(source_task_id='1',source_round_index=1,category='x',key='g',safe_summary='safe') is None and off.read('g')==[]
 m=SharedMemory(dataset='d',group_id='g',seed=42,max_records=2,max_serialized_bytes=1000)
 for i in range(3):m.write(source_task_id=str(i),source_round_index=i,category='x',key='g',safe_summary=f'safe {i}',tags=('g',))
 assert [x.memory_id for x in m.read('g')]==['m0002','m0003'] and m.metrics.eviction_count==1
 assert json.dumps(m.trace(),sort_keys=True)==json.dumps(m.trace(),sort_keys=True)
def test_limits_reset_and_leakage():
 m=SharedMemory(dataset='d',group_id='g',seed=1,max_records=2,max_serialized_bytes=1000)
 with pytest.raises(ValueError):m.write(source_task_id='x',source_round_index=1,category='x',key='k',safe_summary='canonical_solution')
 with pytest.raises(ValueError):m.write(source_task_id='x',source_round_index=1,category='x',key='k',safe_summary='x'*1000)
 m.write(source_task_id='x',source_round_index=1,category='x',key='k',safe_summary='safe');assert m.read('none')==[];m.reset();assert m.trace()['memory_record_count']==0
