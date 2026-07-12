import json
from scripts.verify_m9_run import verify
def test_expected_count_is_strict(tmp_path):
 p=tmp_path/'public'/'tasks';p.mkdir(parents=True);(p/'a.json').write_text(json.dumps({'task_id':'a','final_status':'failed_official_tests'}))
 assert verify(tmp_path,[{'task_id':'a'}],expected_count=1)['valid']
 assert not verify(tmp_path,[{'task_id':'a'}],expected_count=10)['valid']
def test_identity_checks(tmp_path):
 p=tmp_path/'public'/'tasks';p.mkdir(parents=True);(p/'a.json').write_text(json.dumps({'task_id':'a','final_status':'completed_success','spec_sha256':'s','freeze_git_sha':'f','model':'m'}))
 assert verify(tmp_path,[{'task_id':'a'}],expected_spec_sha='s',expected_freeze_sha='f',expected_model='m')['valid']
 assert not verify(tmp_path,[{'task_id':'a'}],expected_model='other')['valid']
