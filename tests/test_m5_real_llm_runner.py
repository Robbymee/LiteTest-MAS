import json
from llm.models import LLMResponse, LLMUsage
from runtime.real_llm_runner import approved_tasks, run_tasks, safe_prompt, RESULT_SCOPE
from tests.test_sequence_runner import write_fixture
class Backend:
 def generate(self,request):
  assert 'hidden_reference_tests' not in request.messages[-1].content
  assert 'canonical_solution' not in request.messages[-1].content
  return LLMResponse('strategy','model','openai_compatible',request.request_id,'stop',LLMUsage(1,2,3,True,'provider'),0.1,True)
def test_m5_runner_uses_fixed_safe_order_and_records_usage(tmp_path):
 selection,tasks=write_fixture(tmp_path); selected=approved_tasks(selection,tasks,0,limit=1)
 assert selected[0].task_id=='mbpp_sanitized:11' and 'hidden_reference_tests' not in safe_prompt(selected[0])
 summary=run_tasks(selected,Backend(),'model',tmp_path/'out'); row=json.loads((tmp_path/'out'/'rounds.jsonl').read_text())
 assert summary['succeeded_rounds']==1 and row['result_scope']==RESULT_SCOPE and row['usage_available'] is True and row['total_tokens']==3 and row['parse_result']=='nonempty_response'
