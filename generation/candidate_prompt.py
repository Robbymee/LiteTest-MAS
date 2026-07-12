from __future__ import annotations
import hashlib,json
from protocol.adapters import ProtocolAdapter
from protocol.messages import AgentMessage
VERSION='candidate_codegen_v1'
SYSTEM='You are a Python programming benchmark solver. Implement the requested function using only the public task description. Return a complete executable Python implementation. Do not discuss testing strategy. Do not generate test cases. Do not include explanations outside the code.'
def build_prompt(task):
 d={'prompt_schema_version':'1.0','prompt_template_version':VERSION,'task_id':task.task_id,'function_name':task.function_name,'signature':task.signature,'description':task.task_description}
 text=f"Implement this Python function. Return code only.\nFunction: {d['function_name']}\nSignature: {d['signature']}\nDescription: {d['description']}"
 return SYSTEM,text,hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def build_group_prompt(task, group, *, state_vector=None, memory_records=()):
 system,text,_=build_prompt(task)
 if group=='G1':
  payload={'communication_mode':'text','message_count':1,'text_character_count':len(text),'protocol_event_count':0,'state_vector_count':0,'state_vector_bytes':0,'memory_reference_ids':[]}
  return system,text,hashlib.sha256(json.dumps({'group':group,'text':text},sort_keys=True,separators=(',',':')).encode()).hexdigest(),payload
 summaries=[record.safe_summary for record in memory_records]
 ids=[record.memory_id for record in memory_records]
 message=AgentMessage('PlannerAgent','TestGenAgent','candidate_generation',text,{'task_id':task.task_id,'group':group,'state_vector':state_vector,'memory_summaries':summaries},'1970-01-01T00:00:00+00:00')
 encoded=ProtocolAdapter().encode(message)
 user='Use this structured protocol message as the complete public task context. Return code only.\n'+encoded
 payload={'communication_mode':'protocol','message_count':1,'text_character_count':len(encoded),'protocol_event_count':1,'state_vector_count':1 if state_vector else 0,'state_vector_bytes':len(state_vector.encode()) if state_vector else 0,'memory_reference_ids':ids}
 return system,user,hashlib.sha256(json.dumps({'group':group,'payload':encoded},sort_keys=True,separators=(',',':')).encode()).hexdigest(),payload
