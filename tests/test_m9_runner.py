from pathlib import Path
from experiments.m9_runner import plan,verify_inventory,atomic_write,validate_spec,completed_tasks,task_key,rebuild_inventory
def test_plan_is_fixed_240_and_atomic(tmp_path):
 items=plan(Path('.'));assert len(items)==240 and len({(x['seed'],x['experiment_group'],x['dataset'],x['task_id']) for x in items})==240
 atomic_write(tmp_path/'task.json',{'status':'completed'});assert (tmp_path/'task.json').exists() and not (tmp_path/'task.tmp').exists()
def test_spec_validation_and_resume_inventory(tmp_path):
 spec={'schema_version':'1','experiment_id':'x','result_scope':'formal_real_llm_ablation','conclusion_scope':'fixed_task_fixed_model_ablation','implementation_git_sha':'sha','model':'local-llama31-8b-instruct','backend':'openai_compatible','seeds':[42,43,44],'experiment_groups':['G1','G2','G3','G4'],'generation_parameters':{},'parser_version':'candidate_parser_v1','sandbox_version':'private_subprocess_v1'}
 validate_spec(spec,'sha'); atomic_write(tmp_path/'tasks'/'a.json',{'status':'completed'});assert completed_tasks(tmp_path)=={'a'} and len(task_key(plan(Path('.'))[0]))==24
def test_rebuild_inventory_from_public_files(tmp_path):
 atomic_write(tmp_path/'tasks'/'x.json',{'task_id':'a','final_status':'completed_success'})
 inv=rebuild_inventory(tmp_path,[{'task_id':'a'},{'task_id':'b'}])
 assert inv['final_count']==1 and inv['missing_task_ids']==['b'] and not inv['duplicate_task_ids']
