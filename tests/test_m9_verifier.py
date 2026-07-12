import json
from scripts.verify_m9_run import verify
def test_expected_count_is_strict(tmp_path):
 p=tmp_path/'public'/'tasks';p.mkdir(parents=True);(p/'a.json').write_text(json.dumps({'task_id':'a','final_status':'failed_official_tests'}))
 assert verify(tmp_path,[{'task_id':'a'}],expected_count=1)['valid']
 assert not verify(tmp_path,[{'task_id':'a'}],expected_count=10)['valid']
