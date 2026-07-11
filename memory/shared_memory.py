"""Deterministic, bounded, in-process memory scoped to one experiment group."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import json, time

BLOCKED = {"hidden_reference_tests","canonical_solution","reference_solution","official_tests","challenge_tests","contract","expected_output","api_key","authorization"}

@dataclass(frozen=True)
class MemoryRecord:
 schema_version:str; memory_id:str; dataset:str; group_id:str; seed:int; source_task_id:str; source_round_index:int; category:str; key:str; safe_summary:str; tags:tuple[str,...]; created_order:int; last_access_order:int; read_count:int=0; reuse_count:int=0
 def stable(self): return json.dumps(asdict(self),sort_keys=True,separators=(',',':'),ensure_ascii=False)
 @property
 def serialized_bytes(self): return len(self.stable().encode())

@dataclass
class MemoryMetrics:
 enabled:bool; write_count:int=0; read_count:int=0; hit_count:int=0; miss_count:int=0; reuse_count:int=0; eviction_count:int=0; reset_count:int=0; peak_record_count:int=0; peak_serialized_bytes:int=0; read_latency_seconds:float=0.; write_latency_seconds:float=0.
 def as_dict(self, records, bytes_):
  d=asdict(self);d.update(memory_record_count=len(records),memory_serialized_bytes=bytes_,memory_hit_rate=(self.hit_count/self.read_count if self.read_count else None),memory_reuse_rate=(self.reuse_count/self.hit_count if self.hit_count else None));return d

class SharedMemory:
 """FIFO memory; instances are intentionally group/dataset/seed scoped."""
 def __init__(self, *, enabled=True, dataset:str='', group_id:str='', seed:int=42, max_records:int=32, max_serialized_bytes:int=8192):
  if max_records<1 or max_serialized_bytes<1: raise ValueError('memory limits must be positive')
  self.enabled=enabled;self.dataset=dataset;self.group_id=group_id;self.seed=seed;self.max_records=max_records;self.max_serialized_bytes=max_serialized_bytes;self._records=[];self._order=0;self.metrics=MemoryMetrics(enabled)
 def _check(self, value):
  if not isinstance(value,str) or not value.strip(): raise ValueError('memory text must be nonempty')
  if any(word in value.lower() for word in BLOCKED): raise ValueError('unsafe memory content')
 def write(self, *, source_task_id, source_round_index, category, key, safe_summary, tags=()):
  if not self.enabled:return None
  started=time.perf_counter(); self._check(safe_summary);self._check(key);self._order+=1
  record=MemoryRecord('1.0',f'm{self._order:04d}',self.dataset,self.group_id,self.seed,str(source_task_id),int(source_round_index),str(category),key,safe_summary,tuple(sorted(map(str,tags))),self._order,self._order)
  if record.serialized_bytes>self.max_serialized_bytes: raise ValueError('memory record exceeds byte limit')
  self._records.append(record);self.metrics.write_count+=1;self._evict();self.metrics.write_latency_seconds+=time.perf_counter()-started;self._peaks();return record.memory_id
 def read(self, key):
  if not self.enabled:return []
  started=time.perf_counter();self._check(key);self.metrics.read_count+=1
  matches=[r for r in self._records if r.key==key or key in r.tags]
  if matches:self.metrics.hit_count+=1;self.metrics.reuse_count+=len(matches)
  else:self.metrics.miss_count+=1
  self.metrics.read_latency_seconds+=time.perf_counter()-started;return matches
 def reset(self): self._records.clear();self.metrics.reset_count+=1
 def close(self): self.reset()
 def trace(self): return {'schema_version':'1.0','eviction_policy':'fifo_v1','records':[json.loads(r.stable()) for r in self._records],**self.metrics.as_dict(self._records,self._bytes())}
 def _bytes(self): return sum(r.serialized_bytes for r in self._records)
 def _evict(self):
  while len(self._records)>self.max_records or self._bytes()>self.max_serialized_bytes:self._records.pop(0);self.metrics.eviction_count+=1
 def _peaks(self): self.metrics.peak_record_count=max(self.metrics.peak_record_count,len(self._records));self.metrics.peak_serialized_bytes=max(self.metrics.peak_serialized_bytes,self._bytes())
