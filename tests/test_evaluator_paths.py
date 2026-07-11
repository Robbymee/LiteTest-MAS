import json
from pathlib import Path

from evaluator.core import evaluate


def make_run(root: Path):
    root.mkdir(parents=True)
    plan={"source_dataset":"demo","mode":"text","seed":42,"total_rounds":1,"task_plan_sha256":"plan","rounds":[{"global_round_index":1,"task_id":"demo:1"}]}
    summary={"run_id":"demo","mode":"text","seed":42,"task_plan_sha256":"plan","deterministic_result_sha256":"result","planned_rounds":1,"executed_rounds":1,"skipped_rounds":0}
    round_={"schema_version":"1.0","global_round_index":1,"task_id":"demo:1","function_name":"f","group_id":"g","status":"succeeded","emitted_message_count":1,"emitted_event_count":1}
    for name,value in (("sequence_plan.json",plan),("run_summary.json",summary)):
        (root/name).write_text(json.dumps(value),encoding='utf-8')
    (root/'rounds.jsonl').write_text(json.dumps(round_)+"\n",encoding='utf-8')


def test_evaluation_paths_are_posix_relative_and_hashes_ignore_output_path(tmp_path):
    input_root=tmp_path/'runs'/'m2_5'; make_run(input_root/'mbpp'/'text')
    first=evaluate(input_root,tmp_path/'C_user_output',strict=True)
    second=evaluate(input_root,tmp_path/'home_oa_output',strict=True)
    assert first['source_run_paths']==['mbpp/text']
    assert '\\' not in first['source_run_paths'][0]
    assert first['evaluation_input_sha256']==second['evaluation_input_sha256']
    assert first['deterministic_evaluation_sha256']==second['deterministic_evaluation_sha256']
