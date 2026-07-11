from __future__ import annotations
import argparse,json,sys
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(PROJECT_ROOT))
from evaluator.core import evaluate
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output-dir',required=True);p.add_argument('--scope',default='mock_validation');p.add_argument('--strict',action='store_true');p.add_argument('--format',default='json,csv,md');a=p.parse_args()
 if a.scope!='mock_validation': raise SystemExit('only mock_validation is supported in M3')
 try: print(json.dumps(evaluate(Path(a.input),Path(a.output_dir),a.strict),indent=2))
 except (OSError,ValueError,json.JSONDecodeError) as e: print(f'evaluation failed: {e}');return 2
 return 0
if __name__=='__main__': raise SystemExit(main())
