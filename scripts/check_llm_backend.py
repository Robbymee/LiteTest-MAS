from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from llm.config import LLMConfig,create_backend
from llm.models import LLMMessage,LLMRequest
def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',required=True);p.add_argument('--model',required=True);p.add_argument('--prompt',default='Return OK');p.add_argument('--seed',type=int,default=42);p.add_argument('--dry-run',action='store_true');p.add_argument('--show-config',action='store_true');a=p.parse_args();c=LLMConfig(a.backend,None if a.backend=='mock' else __import__('os').getenv('LLM_BASE_URL'),a.model,__import__('os').getenv('LLM_API_KEY'))
 try:
  if a.dry_run: create_backend(c);out={'dry_run':True,'config':c.safe_dict()}
  else:
   if a.backend!='mock': raise ValueError('real calls are forbidden in M4')
   r=create_backend(c).generate(LLMRequest((LLMMessage('user',a.prompt),),a.model,seed=a.seed));out={'text':r.text,'backend':r.backend,'usage':r.usage.__dict__,'request_id':r.request_id}
  print(json.dumps(out,sort_keys=True));return 0
 except Exception as e: print(json.dumps({'error':type(e).__name__,'message':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())
