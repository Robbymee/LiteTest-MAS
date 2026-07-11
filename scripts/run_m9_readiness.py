from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from llm.config import LLMConfig,create_backend
from llm.models import LLMMessage,LLMRequest
from runtime.real_llm_runner import approved_tasks
from generation.candidate_prompt import build_prompt
from generation.candidate_parser import parse_candidate
from sandbox.private_eval import evaluate_private
def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset',choices=['mbpp','humaneval'],required=True);p.add_argument('--limit',type=int,required=True);p.add_argument('--output-dir',required=True);p.add_argument('--seed',type=int,default=42);a=p.parse_args()
 paths={'mbpp':('datasets/manifests/mbpp_selected_groups.json','datasets/processed/mbpp/mbpp_tasks.jsonl'),'humaneval':('datasets/manifests/humaneval_selected_groups.json','datasets/processed/humaneval_plus/humaneval_plus_tasks.jsonl')};sel,data=(ROOT/x for x in paths[a.dataset]); tasks=approved_tasks(sel,data,0,a.limit); private={x['task_id']:x for x in map(json.loads,data.read_text(encoding='utf8').splitlines())};out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=False);raw=out/'private_candidates';raw.mkdir(); backend=create_backend(LLMConfig.from_env()); rows=[]
 for i,t in enumerate(tasks,1):
  system,prompt,ph=build_prompt(t);r=backend.generate(LLMRequest((LLMMessage('system',system),LLMMessage('user',prompt)),backend.model,temperature=0,max_tokens=256,seed=a.seed));art=parse_candidate(r.text,t.function_name);(raw/f'{i:02d}.txt').write_text(r.text,encoding='utf8');base={'task_id':t.task_id,'dataset':a.dataset,'group_id':t.group_id,'round_index':i,'prompt_hash':ph,'result_scope':'m9_readiness_pilot','parse_status':art['parse_status'],'parser_version':art['parser_version'],'request_id':r.request_id,'prompt_tokens':r.usage.prompt_tokens,'completion_tokens':r.usage.completion_tokens,'total_tokens':r.usage.total_tokens,'latency_seconds':r.latency_seconds}
  ev=evaluate_private(private[t.task_id],art['candidate_code']) if art['parse_status']=='success' else {'task_success':False,'official_test_count':None,'official_test_pass_count':None,'official_test_fail_count':None,'official_test_pass_rate':None,'error_category':art['parse_status']}
  rows.append(base|{k:v for k,v in art.items() if k!='candidate_code'}|{k:v for k,v in ev.items() if k not in ('task_id','dataset')})
 (out/'public_results.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in rows),encoding='utf8');print(json.dumps({'planned':len(tasks),'final_records':len(rows),'official_available':sum(x['official_test_count'] is not None for x in rows),'task_success':sum(x['task_success'] for x in rows)},sort_keys=True))
if __name__=='__main__':main()
