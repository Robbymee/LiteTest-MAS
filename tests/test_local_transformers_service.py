import importlib.util,sys
from pathlib import Path
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('service',ROOT/'scripts/serve_local_transformers.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
class Tok:
 def apply_chat_template(self,x,**k):return 'prompt'
 def __call__(self,*a,**k):return {'input_ids':__import__('torch').tensor([[1,2]])}
 def decode(self,*a,**k):return 'OK'
class Model:
 device='cpu'
 def eval(self):pass
 def generate(self,**k):return __import__('torch').tensor([[1,2,3]])
def test_fake_service_endpoints():
 app=m.create_app(m.ServiceState('local',16,32,loader=lambda:(Tok(),Model())))
 with TestClient(app) as c:
  assert c.get('/health').status_code==200
  assert c.get('/v1/models').json()['data'][0]['id']=='local'
  assert c.post('/v1/chat/completions',json={'model':'local','messages':[{'role':'user','content':'x'}],'max_tokens':1}).json()['choices'][0]['message']['content']=='OK'
  assert c.post('/v1/chat/completions',json={'model':'local','messages':[{'role':'user','content':'x'}],'stream':True}).status_code==400
