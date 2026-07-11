from __future__ import annotations
import json,time,urllib.request,urllib.error
from llm.errors import *
from llm.models import LLMRequest,LLMResponse,LLMUsage
class OpenAICompatibleBackend:
    backend_name="openai_compatible"
    def __init__(self,base_url,model,api_key=None,timeout_seconds=30,max_retries=2,retry_backoff_seconds=0,transport=None):
        if not base_url or not model: raise LLMConfigurationError("base_url and model are required")
        self.base_url=base_url.rstrip('/');self.model=model;self.api_key=api_key;self.timeout_seconds=timeout_seconds;self.max_retries=max_retries;self.retry_backoff_seconds=retry_backoff_seconds;self.transport=transport
    def generate(self,request):
        payload={"model":request.model,"messages":[{"role":m.role,"content":m.content} for m in request.messages],"temperature":request.temperature,"max_tokens":request.max_tokens,"stream":False}
        if request.seed is not None: payload["seed"]=request.seed
        for attempt in range(self.max_retries+1):
            try:
                started=time.perf_counter()
                raw=self.transport(payload) if self.transport else self._http(payload)
                choice=raw.get("choices",[None])[0] or {};content=(choice.get("message") or {}).get("content")
                if not isinstance(content,str): raise LLMInvalidResponseError("response content missing",request.request_id)
                u=raw.get("usage") or {}; available=bool(u); usage=LLMUsage(u.get("prompt_tokens"),u.get("completion_tokens"),u.get("total_tokens"),available,"provider" if available else "unavailable")
                return LLMResponse(content,raw.get("model",self.model),self.backend_name,request.request_id,choice.get("finish_reason"),usage,time.perf_counter()-started,True,None)
            except LLMBackendError as e:
                if not e.retryable or attempt>=self.max_retries: raise
                if self.retry_backoff_seconds: time.sleep(self.retry_backoff_seconds*(attempt+1))
    def _http(self,payload):
        headers={"Content-Type":"application/json"};
        if self.api_key: headers["Authorization"]="Bearer "+self.api_key
        req=urllib.request.Request(self.base_url+"/chat/completions",data=json.dumps(payload).encode(),headers=headers,method="POST")
        try:
            with urllib.request.urlopen(req,timeout=self.timeout_seconds) as response: return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            mapping={401:LLMAuthenticationError,403:LLMAuthenticationError,429:LLMRateLimitError}
            raise mapping.get(e.code,LLMServerError if e.code>=500 else LLMInvalidRequestError)(f"HTTP {e.code}",status_code=e.code)
        except TimeoutError as e: raise LLMTimeoutError("request timed out") from e
        except urllib.error.URLError as e: raise LLMConnectionError("connection failed") from e
    def close(self): pass
