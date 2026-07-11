import json, subprocess, sys
from pathlib import Path
import pytest
from llm.config import LLMConfig,create_backend
from llm.errors import LLMAuthenticationError,LLMConfigurationError
from llm.models import LLMMessage,LLMRequest
from llm.openai_compatible import OpenAICompatibleBackend

ROOT=Path(__file__).resolve().parents[1]
def test_request_and_mock_are_deterministic():
 r=LLMRequest((LLMMessage('user','hello'),),'mock-deterministic-v1',seed=42)
 a=create_backend(LLMConfig()).generate(r);b=create_backend(LLMConfig()).generate(r)
 assert a.text==b.text and a.usage.usage_source=='mock'
 with pytest.raises(Exception): LLMRequest((), 'x')
def test_openai_parse_and_errors_without_network():
 backend=OpenAICompatibleBackend('http://example.invalid/v1','model',transport=lambda _: {'model':'model','choices':[{'message':{'content':'ok'},'finish_reason':'stop'}]})
 response=backend.generate(LLMRequest((LLMMessage('user','x'),),'model'))
 assert response.text=='ok' and response.latency_seconds is not None
 with pytest.raises(LLMConfigurationError): create_backend(LLMConfig(backend='unknown'))
def test_cli_mock_and_openai_dry_run_redact():
 cmd=[sys.executable,'scripts/check_llm_backend.py','--backend','mock','--model','mock-deterministic-v1','--prompt','Return exactly OK.','--seed','42']
 a=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True);b=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
 assert a.returncode==b.returncode==0 and json.loads(a.stdout)['text']==json.loads(b.stdout)['text']
 env={'LLM_BASE_URL':'http://127.0.0.1:11434/v1','LLM_API_KEY':'test-placeholder'}
 result=subprocess.run([sys.executable,'scripts/check_llm_backend.py','--backend','openai_compatible','--model','x','--dry-run','--show-config'],cwd=ROOT,text=True,capture_output=True,env={**__import__('os').environ,**env})
 assert result.returncode==0 and 'test-placeholder' not in result.stdout
