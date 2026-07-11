"""Minimal local-only OpenAI-compatible Transformers service for M5 smoke tests."""
from __future__ import annotations
import argparse, asyncio, os, secrets
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

class Message(BaseModel): role:str; content:str
class ChatRequest(BaseModel):
    model:str; messages:list[Message]; temperature:float=0; max_tokens:int=Field(default=256,gt=0); stream:bool=False; seed:int|None=None
class ServiceState:
    def __init__(self,model_name,max_new_tokens,max_context,loader=None): self.model_name=model_name;self.max_new_tokens=max_new_tokens;self.max_context=max_context;self.loader=loader;self.model=None;self.tokenizer=None;self.lock=asyncio.Lock()
    def load(self):
        if self.loader: self.tokenizer,self.model=self.loader(); return
        from transformers import AutoModelForCausalLM,AutoTokenizer
        path=Path(os.environ['LOCAL_TRANSFORMERS_MODEL_PATH'])
        self.tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True)
        self.model=AutoModelForCausalLM.from_pretrained(path,local_files_only=True,torch_dtype='auto',device_map='auto',low_cpu_mem_usage=True);self.model.eval()
    def generate(self,messages,max_tokens,temperature,seed):
        import torch
        prompt=self.tokenizer.apply_chat_template([m.model_dump() for m in messages],tokenize=False,add_generation_prompt=True)
        inputs=self.tokenizer(prompt,return_tensors='pt')
        if hasattr(self.model,'device'): inputs={k:v.to(self.model.device) for k,v in inputs.items()}
        kwargs={'max_new_tokens':min(max_tokens,self.max_new_tokens),'do_sample':temperature>0}
        if temperature>0: kwargs['temperature']=temperature
        if seed is not None: torch.manual_seed(seed)
        with torch.inference_mode(): out=self.model.generate(**inputs,**kwargs)
        new=out[0][inputs['input_ids'].shape[1]:]; text=self.tokenizer.decode(new,skip_special_tokens=True)
        return text,int(inputs['input_ids'].shape[1]),int(new.shape[0])
def create_app(state:ServiceState)->FastAPI:
 @asynccontextmanager
 async def lifespan(app): state.load();yield
 app=FastAPI(lifespan=lifespan)
 @app.get('/health')
 async def health(): return {'status':'ok','model':state.model_name}
 @app.get('/v1/models')
 async def models(): return {'object':'list','data':[{'id':state.model_name,'object':'model'}]}
 @app.post('/v1/chat/completions')
 async def chat(request:ChatRequest):
  if request.stream: raise HTTPException(400,'stream is not supported')
  if not request.messages: raise HTTPException(400,'messages must not be empty')
  if request.max_tokens>state.max_new_tokens: raise HTTPException(400,'max_tokens exceeds service limit')
  async with state.lock:
   try: text,prompt_tokens,completion_tokens=state.generate(request.messages,request.max_tokens,request.temperature,request.seed)
   except Exception: raise HTTPException(500,'local generation failed')
  return {'id':'chatcmpl-'+secrets.token_hex(8),'object':'chat.completion','model':state.model_name,'choices':[{'index':0,'message':{'role':'assistant','content':text},'finish_reason':'stop'}],'usage':{'prompt_tokens':prompt_tokens,'completion_tokens':completion_tokens,'total_tokens':prompt_tokens+completion_tokens}}
 return app
def main():
 p=argparse.ArgumentParser();p.add_argument('--model-path',required=True);p.add_argument('--model-name',default='local-llama31-8b-instruct');p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8000);p.add_argument('--max-context',type=int,default=4096);p.add_argument('--max-new-tokens',type=int,default=1024);p.add_argument('--device',default='auto');p.add_argument('--log-level',default='warning');a=p.parse_args()
 path=Path(a.model_path)
 if not path.is_dir(): raise SystemExit('model path does not exist')
 os.environ['LOCAL_TRANSFORMERS_MODEL_PATH']=str(path)
 import uvicorn;uvicorn.run(create_app(ServiceState(a.model_name,a.max_new_tokens,a.max_context)),host=a.host,port=a.port,log_level=a.log_level)
if __name__=='__main__': main()
