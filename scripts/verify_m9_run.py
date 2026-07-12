from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.m9_runner import rebuild_inventory,stable_hash
FORBIDDEN={'candidate_code','raw_response','hidden_reference_tests','canonical_solution','reference_solution','official_tests','contract','expected_output','api_key','authorization'}
def verify(run_root, planned, strict=False, expected_count=None, expected_spec_sha=None, expected_freeze_sha=None, expected_model=None):
 public=Path(run_root)/'public'; tasks=list((public/'tasks').glob('*.json'))
 errors=[]; rows=[]
 for path in tasks:
  try: row=json.loads(path.read_text(encoding='utf8'));rows.append(row)
  except Exception: errors.append('invalid_json:'+path.name);continue
  if FORBIDDEN & set(row): errors.append('forbidden_field:'+path.name)
  if not row.get('final_status','').startswith(('completed_','failed_')): errors.append('non_final:'+path.name)
  if expected_spec_sha is not None and row.get('spec_sha256')!=expected_spec_sha: errors.append('spec_sha_mismatch')
  if expected_freeze_sha is not None and row.get('freeze_git_sha')!=expected_freeze_sha: errors.append('freeze_sha_mismatch')
  if expected_model is not None and row.get('model')!=expected_model: errors.append('model_mismatch')
 inventory=rebuild_inventory(public,planned)
 if inventory['missing_task_ids']:errors.append('missing_tasks')
 if inventory['duplicate_task_ids']:errors.append('duplicate_tasks')
 if expected_count is not None and len(rows)!=expected_count: errors.append('unexpected_final_count')
 result={'valid':not errors,'errors':errors,'final_count':len(rows),'inventory':inventory}
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--run-root',required=True);p.add_argument('--strict',action='store_true');p.add_argument('--json-output',action='store_true');p.add_argument('--expected-count',type=int);p.add_argument('--expected-spec-sha');p.add_argument('--expected-freeze-sha');p.add_argument('--expected-model');a=p.parse_args();planned=[]
 if not (Path(a.run_root)/'public'/'tasks').exists(): raise SystemExit(2)
 for path in (Path(a.run_root)/'public'/'tasks').glob('*.json'):
  row=json.loads(path.read_text(encoding='utf8'));planned.append({'task_id':row.get('task_id')})
 result=verify(a.run_root,planned,a.strict,a.expected_count,a.expected_spec_sha,a.expected_freeze_sha,a.expected_model);print(json.dumps(result,sort_keys=True));return 0 if result['valid'] else 1
if __name__=='__main__':raise SystemExit(main())
