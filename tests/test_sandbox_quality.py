from sandbox.quality import extract_python,evaluate
def test_extract_and_execute_without_importing_candidate():
 assert extract_python('text') is None
 assert extract_python('```python\ndef f(): return 1\n```').startswith('def')
 ok=evaluate('def f(): return 1');assert ok['task_success'] and ok['syntax_valid']
 bad=evaluate('def broken(:');assert bad['runtime_error'] and not bad['task_success']
 timeout=evaluate('def loop():\n while True: pass\nloop()',timeout=.1);assert timeout['timeout']
