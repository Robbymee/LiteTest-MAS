from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.m9_runner import verify_inventory,stable_hash,validate_spec,completed_tasks,task_key,execute_task
def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',required=True);p.add_argument('--output-root',required=True);p.add_argument('--dry-run',action='store_true');p.add_argument('--strict',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args();spec=json.loads(Path(a.spec).read_text());validate_spec(spec,spec['implementation_git_sha']);items=verify_inventory(ROOT,spec);done=completed_tasks(a.output_root) if a.resume else set();print(json.dumps({'planned':len(items),'duplicates':len(items)-len({tuple(sorted(x.items())) for x in items}),'completed':sum(task_key(x) in done for x in items),'spec_sha256':stable_hash({k:v for k,v in spec.items() if k!='created_at'}), 'dry_run':a.dry_run},sort_keys=True))
if __name__=='__main__':main()
