"""Restricted subprocess quality evaluator; not a container security boundary."""
from __future__ import annotations
import os,re,subprocess,sys,tempfile,time
from dataclasses import dataclass,asdict
def extract_python(text):
 blocks=re.findall(r'```(?:python)?\s*(.*?)```',text,re.S|re.I)
 candidate=blocks[0] if blocks else text
 return candidate.strip() if ('def ' in candidate or 'import ' in candidate) else None
def evaluate(candidate, *, timeout=5, output_limit=8192):
 result={'syntax_valid':False,'import_valid':False,'execution_started':False,'execution_completed':False,'official_test_count':None,'official_test_pass_count':None,'official_test_fail_count':None,'test_pass_rate':None,'task_success':False,'timeout':False,'runtime_error':False,'assertion_error':False,'import_error':False,'syntax_error':False,'sandbox_error':False,'exit_code':None,'execution_time_seconds':None,'stdout_bytes':0,'stderr_bytes':0}
 code=extract_python(candidate)
 if not code:return {**result,'parse_status':'no_python_code'}
 with tempfile.TemporaryDirectory() as d:
  path=os.path.join(d,'candidate.py');open(path,'w',encoding='utf-8').write(code)
  started=time.perf_counter()
  try:
   p=subprocess.run([sys.executable,'-I',path],cwd=d,capture_output=True,timeout=timeout,env={'PYTHONIOENCODING':'utf-8'},shell=False)
   result.update(execution_started=True,execution_completed=True,exit_code=p.returncode,execution_time_seconds=time.perf_counter()-started,stdout_bytes=min(len(p.stdout),output_limit),stderr_bytes=min(len(p.stderr),output_limit),syntax_valid=p.returncode==0,import_valid=p.returncode==0,task_success=p.returncode==0,runtime_error=p.returncode!=0)
  except subprocess.TimeoutExpired:
   result.update(execution_started=True,timeout=True,execution_time_seconds=time.perf_counter()-started)
 return {**result,'parse_status':'python_code'}
