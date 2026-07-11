from generation.candidate_prompt import build_prompt
from generation.candidate_parser import parse_candidate
from runtime.sequence_runner import SelectedTask
def task():return SelectedTask('d:1','1','g','f','f(x)','public description')
def test_prompt_and_parser_are_safe_deterministic():
 s,u,h=build_prompt(task());assert 'hidden_reference_tests' not in s+u and h==build_prompt(task())[2]
 assert parse_candidate('```python\ndef f(x): return x\n```','f')['parse_status']=='success'
 assert parse_candidate('text','f')['parse_status']=='no_code_found'
 assert parse_candidate('def g(): pass','f')['parse_status']=='target_function_missing'
 assert parse_candidate('','f')['parse_status']=='empty_response'
