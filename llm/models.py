from __future__ import annotations
from dataclasses import dataclass, field
import json, uuid
from typing import Any
from llm.errors import LLMInvalidRequestError

@dataclass(frozen=True)
class LLMMessage:
    role:str; content:str
    def __post_init__(self):
        if self.role not in {"system","user","assistant","tool"} or not isinstance(self.content,str): raise LLMInvalidRequestError("invalid message")
@dataclass(frozen=True)
class LLMRequest:
    messages:tuple[LLMMessage,...]; model:str; temperature:float=0.0; max_tokens:int=256; seed:int|None=None; stop:tuple[str,...]=(); request_id:str=field(default_factory=lambda:uuid.uuid4().hex); metadata:dict[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not self.messages or not self.model or not 0<=self.temperature<=2 or self.max_tokens<=0: raise LLMInvalidRequestError("invalid request")
        try: json.dumps(self.metadata)
        except TypeError as e: raise LLMInvalidRequestError("metadata must be JSON serializable") from e
@dataclass(frozen=True)
class LLMUsage:
    prompt_tokens:int|None=None; completion_tokens:int|None=None; total_tokens:int|None=None; usage_available:bool=False; usage_source:str="unavailable"
@dataclass(frozen=True)
class LLMResponse:
    text:str; model:str; backend:str; request_id:str; finish_reason:str|None; usage:LLMUsage; latency_seconds:float|None; raw_response_available:bool=False; error:dict|None=None
