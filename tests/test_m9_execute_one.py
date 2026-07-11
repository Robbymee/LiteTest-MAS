import json,subprocess,sys
from pathlib import Path
from experiments.m9_runner import group_config
ROOT=Path(__file__).resolve().parents[1]
def spec():return {'schema_version':'1','experiment_id':'x','result_scope':'formal_real_llm_ablation','conclusion_scope':'fixed_task_fixed_model_ablation','implementation_git_sha':'x','model':'local-llama31-8b-instruct','backend':'openai_compatible','seeds':[42,43,44],'experiment_groups':['G1','G2','G3','G4'],'generation_parameters':{},'parser_version':'candidate_parser_v1','sandbox_version':'private_subprocess_v1'}
def test_groups_and_cli_dry_run(tmp_path):
 assert group_config('G1')['mode']=='text' and not group_config('G1')['state_enabled']
 assert group_config('G2')['mode']=='protocol' and not group_config('G2')['memory_enabled']
 assert group_config('G3')['state_enabled'] and not group_config('G3')['memory_enabled']
 assert group_config('G4')['state_enabled'] and group_config('G4')['memory_enabled']
 p=tmp_path/'spec.json';p.write_text(json.dumps(spec()));r=subprocess.run([sys.executable,'scripts/run_m9_experiment.py','--spec',str(p),'--output-root',str(tmp_path/'out'),'--dry-run'],cwd=ROOT,text=True,capture_output=True)
 assert r.returncode==0 and json.loads(r.stdout)['planned']==240
