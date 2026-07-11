from __future__ import annotations
import os
from dataclasses import dataclass
from llm.errors import LLMConfigurationError
from llm.mock_backend import MockLLMBackend
from llm.openai_compatible import OpenAICompatibleBackend
from llm.redaction import redact
@dataclass(frozen=True)
class LLMConfig:
    backend:str='mock';base_url:str|None=None;model:str='mock-deterministic-v1';api_key:str|None=None;timeout_seconds:float=30;max_retries:int=2
    @classmethod
    def from_env(cls): return cls(os.getenv('LLM_BACKEND','mock'),os.getenv('LLM_BASE_URL'),os.getenv('LLM_MODEL','mock-deterministic-v1'),os.getenv('LLM_API_KEY'),float(os.getenv('LLM_TIMEOUT_SECONDS','30')),int(os.getenv('LLM_MAX_RETRIES','2')))
    def safe_dict(self): return {'backend':self.backend,'base_url':self.base_url,'model':self.model,'api_key':'***REDACTED***' if self.api_key else None,'timeout_seconds':self.timeout_seconds,'max_retries':self.max_retries}
def create_backend(config):
    if config.backend=='mock': return MockLLMBackend(config.model)
    if config.backend=='openai_compatible': return OpenAICompatibleBackend(config.base_url,config.model,config.api_key,config.timeout_seconds,config.max_retries)
    raise LLMConfigurationError('unknown backend')
