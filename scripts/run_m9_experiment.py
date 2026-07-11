from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.m9_runner import verify_inventory,stable_hash,validate_spec,completed_tasks,task_key,execute_task
def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',required=True);p.add_argument('--output-root',required=True);p.add_argument('--combination');p.add_argument('--task-id');p.add_argument('--dry-run',action='store_true');p.add_argument('--execute-one',action='store_true');p.add_argument('--strict',action='store_true');a=p.parse_args();spec=json.loads(Path(a.spec).read_text());validate_spec(spec,spec['implementation_git_sha']);items=verify_inventory(ROOT,spec)
 selected=items
 if a.combination:
  try:g,d,s=a.combination.split(':');selected=[x for x in selected if x['experiment_group']==g and x['dataset']==d and x['seed']==int(s)]
  except ValueError: selected=[]
 if a.task_id:selected=[x for x in selected if x['task_id']==a.task_id]
 if (a.combination or a.task_id) and len(selected)!=1:raise SystemExit('combination/task selection must resolve exactly one task')
 if a.execute_one:
  if len(selected)!=1:raise SystemExit('--execute-one requires --combination and --task-id')
  from llm.config import LLMConfig,create_backend
  record=execute_task(ROOT,selected[0],a.output_root,create_backend(LLMConfig.from_env()));print(json.dumps({'final_status':record['final_status'],'task_id':record['task_id']},sort_keys=True));return
 print(json.dumps({'planned':len(items),'selected':len(selected),'duplicates':len(items)-len({tuple(sorted(x.items())) for x in items}),'spec_sha256':stable_hash({k:v for k,v in spec.items() if k!='created_at'}),'dry_run':a.dry_run},sort_keys=True))
if __name__=='__main__':main()
