from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from llm.config import LLMConfig, create_backend
from runtime.real_llm_runner import approved_tasks, run_tasks
def main():
 p=argparse.ArgumentParser(description='M5 real local-LLM integration validation');p.add_argument('--dataset',choices=['mbpp','humaneval'],required=True);p.add_argument('--group-index',type=int,default=0);p.add_argument('--limit',type=int);p.add_argument('--output-dir',required=True);p.add_argument('--seed',type=int,default=42);p.add_argument('--max-tokens',type=int,default=256);a=p.parse_args()
 paths={'mbpp':('datasets/manifests/mbpp_selected_groups.json','datasets/processed/mbpp/mbpp_tasks.jsonl'),'humaneval':('datasets/manifests/humaneval_selected_groups.json','datasets/processed/humaneval_plus/humaneval_plus_tasks.jsonl')}
 selection,tasks=(ROOT/part for part in paths[a.dataset]);config=LLMConfig.from_env()
 if config.backend!='openai_compatible': raise SystemExit('M5 requires LLM_BACKEND=openai_compatible; Mock fallback is forbidden')
 summary=run_tasks(approved_tasks(selection,tasks,a.group_index,a.limit),create_backend(config),config.model,ROOT/a.output_dir,seed=a.seed,max_tokens=a.max_tokens)
 print(json.dumps(summary,sort_keys=True));return 0 if not summary['failed_rounds'] else 1
if __name__=='__main__': raise SystemExit(main())
