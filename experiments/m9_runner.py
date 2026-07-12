from __future__ import annotations
import hashlib,json,os
from pathlib import Path
GROUPS={'G1':(False,False),'G2':(False,False),'G3':(True,False),'G4':(True,True)}
DATA={'mbpp':('datasets/manifests/mbpp_selected_groups.json','datasets/processed/mbpp/mbpp_tasks.jsonl'),'humaneval':('datasets/manifests/humaneval_selected_groups.json','datasets/processed/humaneval_plus/humaneval_plus_tasks.jsonl')}
def stable_hash(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def plan(root):
 from runtime.real_llm_runner import approved_tasks
 out=[]
 for seed in (42,43,44):
  order=[['G1','G2','G3','G4'],['G2','G3','G4','G1'],['G3','G4','G1','G2']][seed-42]
  for group in order:
   for dataset in ('mbpp','humaneval'):
    s,t=(root/x for x in DATA[dataset]);
    for task in approved_tasks(s,t,0)+approved_tasks(s,t,1):out.append({'seed':seed,'experiment_group':group,'dataset':dataset,'task_id':task.task_id,'group_id':task.group_id})
 return out
def atomic_write(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,sort_keys=True)+'\n',encoding='utf8');os.replace(tmp,path)
def verify_inventory(root,spec):
 p=plan(root)
 if len(p)!=240 or len({(x['seed'],x['experiment_group'],x['dataset'],x['task_id']) for x in p})!=240:raise ValueError('invalid formal plan')
 return p
def validate_spec(spec, implementation_sha):
 required={'schema_version','experiment_id','result_scope','conclusion_scope','implementation_git_sha','model','backend','seeds','experiment_groups','generation_parameters','parser_version','sandbox_version'}
 missing=required-set(spec)
 if missing:raise ValueError('spec missing '+','.join(sorted(missing)))
 if spec['implementation_git_sha']!=implementation_sha:raise ValueError('implementation git SHA mismatch')
 if spec['result_scope']!='formal_real_llm_ablation' or spec['seeds']!=[42,43,44] or spec['experiment_groups']!=['G1','G2','G3','G4']:raise ValueError('invalid frozen experiment configuration')
def completed_tasks(output_root):
 tasks=Path(output_root)/'tasks'
 if not tasks.exists():return set()
 return {p.stem for p in tasks.glob('*.json') if json.loads(p.read_text()).get('status','').startswith(('completed','failed_'))}
def task_key(item):return stable_hash(item)[:24]
def rebuild_inventory(public_root, planned):
 files=list(Path(public_root).glob('tasks/*.json')); rows=[]
 for path in files:
  try: rows.append(json.loads(path.read_text(encoding='utf8')))
  except json.JSONDecodeError: continue
 final=[x for x in rows if x.get('final_status','').startswith(('completed_','failed_'))]
 ids=[x.get('task_id') for x in final];planned_ids=[x['task_id'] for x in planned]
 payload={'schema_version':'1.0','planned_count':len(planned),'final_count':len(final),'final_task_ids':ids,'missing_task_ids':[x for x in planned_ids if x not in ids],'duplicate_task_ids':sorted({x for x in ids if ids.count(x)>1}),'status_counts':{s:sum(x.get('final_status')==s for x in final) for s in sorted({x.get('final_status') for x in final})},'task_result_checksums':{p.stem:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
 payload['inventory_sha256']=stable_hash(payload);return payload

def write_inventory(public_root, planned):
 inventory=rebuild_inventory(public_root,planned)
 atomic_write(Path(public_root)/'inventory.json',inventory)
 return inventory
def final_record(output_root,item):
 path=Path(output_root)/'public'/'tasks'/(task_key(item)+'.json')
 if not path.is_file(): return None
 value=json.loads(path.read_text(encoding='utf8'))
 return value if value.get('final_status','').startswith(('completed_','failed_')) else None

def group_config(group):
 if group not in GROUPS:raise ValueError('unknown experiment group')
 state,memory=GROUPS[group]
 return {'mode':'text' if group=='G1' else 'protocol','state_enabled':state,'memory_enabled':memory}
def execute_task(root,item,out,backend):
 from runtime.real_llm_runner import approved_tasks
 from generation.candidate_prompt import build_prompt
 from generation.candidate_parser import parse_candidate
 from sandbox.private_eval import evaluate_private
 from llm.models import LLMMessage,LLMRequest
 sel,data=(root/x for x in DATA[item['dataset']]);tasks=approved_tasks(sel,data,0)+approved_tasks(sel,data,1);task=next(x for x in tasks if x.task_id==item['task_id']);private={x['task_id']:x for x in map(json.loads,data.read_text(encoding='utf8').splitlines())}[task.task_id]
 key=task_key(item);pub=Path(out)/'public'/'tasks';priv=Path(out)/'private';attempts=priv/'attempts';attempts.mkdir(parents=True,exist_ok=True);attempt_no=len(list(attempts.glob(key+'-attempt-*.json')))+1;atomic_write(attempts/(f'{key}-attempt-{attempt_no}.json'),{'task_id':task.task_id,'attempt':attempt_no,'status':'running'});atomic_write(pub/(key+'.json'),{'status':'running','task_id':task.task_id,'attempt_count':attempt_no})
 system,prompt,ph=build_prompt(task);r=backend.generate(LLMRequest((LLMMessage('system',system),LLMMessage('user',prompt)),backend.model,temperature=0,max_tokens=256,seed=item['seed']));art=parse_candidate(r.text,task.function_name);priv.mkdir(parents=True,exist_ok=True);(priv/(key+'.txt')).write_text(r.text,encoding='utf8')
 ev=evaluate_private(private,art['candidate_code']) if art['parse_status']=='success' else {'task_success':False,'official_test_count':None,'error_category':art['parse_status']}
 record={'schema_version':'1.0',**item,**group_config(item['experiment_group']),'prompt_version':'candidate_codegen_v1','prompt_sha256':ph,'parser_version':art['parser_version'],'candidate_sha256':art.get('candidate_sha256'),'parse_status':art['parse_status'],'request_ids':[r.request_id],'request_count':1,'finish_reason':r.finish_reason,'prompt_tokens':r.usage.prompt_tokens,'completion_tokens':r.usage.completion_tokens,'total_tokens':r.usage.total_tokens,'usage_available':r.usage.usage_available,'latency_seconds':r.latency_seconds,'retry_count':0,'result_scope':'formal_real_llm_ablation','final_status':'completed_success' if ev['task_success'] else 'failed_official_tests',**{k:v for k,v in ev.items() if k not in {'task_id','dataset','candidate_sha256'}},'infrastructure_failure':False,'model_quality_failure':not ev['task_success']}
 atomic_write(attempts/(f'{key}-attempt-{attempt_no}.json'),{'task_id':task.task_id,'attempt':attempt_no,'status':record['final_status']})
 atomic_write(pub/(key+'.json'),record)
 write_inventory(pub.parent,[item])
 return record
