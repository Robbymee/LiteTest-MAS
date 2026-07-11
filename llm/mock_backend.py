from __future__ import annotations
import hashlib
from llm.errors import LLMAuthenticationError,LLMConnectionError,LLMRateLimitError,LLMTimeoutError,LLMInvalidResponseError
from llm.models import LLMRequest,LLMResponse,LLMUsage
class MockLLMBackend:
    backend_name="mock"
    def __init__(self,model="mock-deterministic-v1",fixed_response=None,simulate_error=None,return_usage=True): self.model=model;self.fixed_response=fixed_response;self.simulate_error=simulate_error;self.return_usage=return_usage
    def generate(self,request:LLMRequest)->LLMResponse:
        errors={"timeout":LLMTimeoutError,"rate_limit":LLMRateLimitError,"authentication":LLMAuthenticationError,"connection":LLMConnectionError,"invalid_response":LLMInvalidResponseError}
        if self.simulate_error: raise errors[self.simulate_error](f"mock {self.simulate_error}",request.request_id)
        digest=hashlib.sha256((str(request.seed)+request.model+"|".join(m.content for m in request.messages)).encode()).hexdigest()
        text=self.fixed_response if self.fixed_response is not None else f"mock:{digest[:16]}"
        usage=LLMUsage(len("".join(m.content for m in request.messages))//4,len(text)//4, (len("".join(m.content for m in request.messages))+len(text))//4,True,"mock") if self.return_usage else LLMUsage()
        return LLMResponse(text,self.model,self.backend_name,request.request_id,"stop",usage,0.0,False,None)
    def close(self): pass
