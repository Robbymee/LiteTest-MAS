from pathlib import Path
from experiments.m9_runner import plan,verify_inventory,atomic_write
def test_plan_is_fixed_240_and_atomic(tmp_path):
 items=plan(Path('.'));assert len(items)==240 and len({(x['seed'],x['experiment_group'],x['dataset'],x['task_id']) for x in items})==240
 atomic_write(tmp_path/'task.json',{'status':'completed'});assert (tmp_path/'task.json').exists() and not (tmp_path/'task.tmp').exists()
