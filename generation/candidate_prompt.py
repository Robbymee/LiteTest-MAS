from __future__ import annotations
import hashlib,json
VERSION='candidate_codegen_v1'
SYSTEM='You are a Python programming benchmark solver. Implement the requested function using only the public task description. Return a complete executable Python implementation. Do not discuss testing strategy. Do not generate test cases. Do not include explanations outside the code.'
def build_prompt(task):
 d={'prompt_schema_version':'1.0','prompt_template_version':VERSION,'task_id':task.task_id,'function_name':task.function_name,'signature':task.signature,'description':task.task_description}
 text=f"Implement this Python function. Return code only.\nFunction: {d['function_name']}\nSignature: {d['signature']}\nDescription: {d['description']}"
 return SYSTEM,text,hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
