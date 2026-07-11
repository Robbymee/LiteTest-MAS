"""Private-only official-test executor. Never serialize bundles into public results."""
from __future__ import annotations
import json,os,subprocess,sys,tempfile,time
def static_risk(code):
 bad=('subprocess','os.system','socket','requests','httpx','urllib','shutil.rmtree','ctypes','multiprocessing','eval(','exec(')
 return next((x for x in bad if x in code),'clear')
def evaluate_private(task, code, timeout=10):
 risk=static_risk(code)
 public={'task_id':task['task_id'],'dataset':task['source_dataset'],'candidate_sha256':__import__('hashlib').sha256(code.encode()).hexdigest(),'static_risk_status':risk,'sandbox_started':False,'sandbox_completed':False,'official_test_count':None,'official_test_pass_count':None,'official_test_fail_count':None,'official_test_pass_rate':None,'task_success':False,'timeout':False,'error_category':None,'exit_code':None,'execution_time_seconds':None,'stdout_bytes':0,'stderr_bytes':0}
 if risk!='clear':return public|{'error_category':'static_rejected'}
 hidden=task['hidden_reference_tests']; tests=[]
 if task['source_dataset']=='mbpp_sanitized':tests=hidden
 else:
  h=hidden[0]; tests=[h['test']]
 with tempfile.TemporaryDirectory() as d:
  open(os.path.join(d,'candidate.py'),'w',encoding='utf8').write(code)
  testcode='from candidate import *\n'+ '\n'.join(tests)
  open(os.path.join(d,'private_tests.py'),'w',encoding='utf8').write(testcode)
  start=time.perf_counter()
  try:p=subprocess.run([sys.executable,'-I','private_tests.py'],cwd=d,capture_output=True,timeout=timeout,shell=False,env={'PYTHONIOENCODING':'utf-8'})
  except subprocess.TimeoutExpired:return public|{'sandbox_started':True,'timeout':True,'error_category':'sandbox_timeout','execution_time_seconds':time.perf_counter()-start}
  count=len(tests);ok=p.returncode==0
  return public|{'sandbox_started':True,'sandbox_completed':True,'official_test_count':count,'official_test_pass_count':count if ok else 0,'official_test_fail_count':0 if ok else count,'official_test_pass_rate':1. if ok else 0.,'task_success':ok,'error_category':None if ok else 'official_test_failure','exit_code':p.returncode,'execution_time_seconds':time.perf_counter()-start,'stdout_bytes':len(p.stdout),'stderr_bytes':len(p.stderr)}
