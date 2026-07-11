"""Small, validated, platform-stable StateVector for protocol experiments."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import json,time
PHASES={'planning','generation','validation','complete','failed'}; ROLES={'planner','testgen','executor','summarizer'}; ERRORS={'none','parse','timeout','runtime','sandbox','backend'}
@dataclass(frozen=True)
class StateVector:
 schema_version:str='1.0';task_phase:str='planning';agent_role:str='planner';progress_flags:tuple[str,...]=();validation_state:str='pending';artifact_state:str='none';error_category:str='none';retry_count:int=0;confidence_bucket:str='unknown';memory_reference_ids:tuple[str,...]=();generated_artifact_count:int=0;protocol_event_count:int=0;completion_flag:bool=False
 def __post_init__(self):
  if self.task_phase not in PHASES or self.agent_role not in ROLES or self.error_category not in ERRORS or self.retry_count<0:raise ValueError('invalid state vector enum')
  if any(len(x)>64 or any(b in x.lower() for b in ('hidden','canonical','api_key','authorization')) for x in self.progress_flags+self.memory_reference_ids):raise ValueError('unsafe state vector')
 def stable(self):
  raw=json.dumps(asdict(self),sort_keys=True,separators=(',',':'))
  if len(raw.encode())>512:raise ValueError('state vector exceeds 512 bytes')
  return raw
@dataclass
class StateMetrics:
 enabled:bool;count:int=0;valid:int=0;invalid:int=0;serialized_bytes:int=0;updates:int=0;transitions:int=0;serialization_time:float=0.;validation_time:float=0.
 def trace(self):return {'state_enabled':self.enabled,'state_vector_count':self.count,'valid_state_count':self.valid,'invalid_state_count':self.invalid,'state_serialized_bytes':self.serialized_bytes,'average_state_vector_bytes':self.serialized_bytes/self.count if self.count else None,'state_update_count':self.updates,'state_transition_count':self.transitions,'state_serialization_time':self.serialization_time,'state_validation_time':self.validation_time}
