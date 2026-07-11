from __future__ import annotations
import ast,hashlib,re
VERSION='candidate_parser_v1'
def parse_candidate(response,target):
 if not response or not response.strip():return {'parser_version':VERSION,'parse_status':'empty_response','candidate_code':None}
 blocks=re.findall(r'```(python)?\s*(.*?)```',response,re.S|re.I); candidates=[b[1] for b in blocks] or [response]
 valid=[]
 for i,code in enumerate(candidates):
  try:
   tree=ast.parse(code); funcs=[x.name for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]
   if target in funcs:valid.append((i,code.strip()))
  except SyntaxError:pass
 if not valid:
  if not any('def ' in x or 'import ' in x for x in candidates):status='no_code_found'
  else:
   try:ast.parse(candidates[0]);status='target_function_missing'
   except SyntaxError:status='syntax_error'
  return {'parser_version':VERSION,'parse_status':status,'candidate_code':None,'target_function_found':False}
 i,code=valid[0]
 return {'parser_version':VERSION,'parse_status':'success','candidate_code':code,'candidate_sha256':hashlib.sha256(code.encode()).hexdigest(),'target_function_found':True,'syntax_valid':True,'selected_block_index':i,'warning_codes':['multiple_candidates'] if len(valid)>1 else []}
