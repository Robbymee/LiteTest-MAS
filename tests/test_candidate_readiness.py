from generation.candidate_prompt import build_prompt
from generation.candidate_parser import parse_candidate
from runtime.sequence_runner import SelectedTask
from sandbox.private_eval import evaluate_private
def task():return SelectedTask('d:1','1','g','f','f(x)','public description')
def test_prompt_and_parser_are_safe_deterministic():
 s,u,h=build_prompt(task());assert 'hidden_reference_tests' not in s+u and h==build_prompt(task())[2]
 assert parse_candidate('```python\ndef f(x): return x\n```','f')['parse_status']=='success'
 assert parse_candidate('text','f')['parse_status']=='no_code_found'
 assert parse_candidate('def g(): pass','f')['parse_status']=='target_function_missing'
def test_private_adapters_execute_candidate_and_humaneval_check():
 mbpp={'task_id':'m:1','source_dataset':'mbpp_sanitized','hidden_reference_tests':['assert f(1)==2']}
 human={'task_id':'h:1','source_dataset':'humaneval_plus','entry_point':'f','hidden_reference_tests':[{'test':'def check(fn):\n assert fn(1)==2'}]}
 for task in (mbpp,human):
  assert evaluate_private(task,'def f(x): return x+1')['task_success'] is True
  assert evaluate_private(task,'def f(x): return None')['error_category']=='official_test_failure'
 assert parse_candidate('','f')['parse_status']=='empty_response'
