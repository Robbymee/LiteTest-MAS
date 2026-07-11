from __future__ import annotations

class LLMBackendError(RuntimeError):
    error_type="backend_error"; retryable=False
    def __init__(self, message: str, request_id: str|None=None, status_code: int|None=None): self.safe_message=message;self.request_id=request_id;self.status_code=status_code;super().__init__(message)
class LLMConfigurationError(LLMBackendError): error_type="configuration_error"
class LLMAuthenticationError(LLMBackendError): error_type="authentication_error"
class LLMRateLimitError(LLMBackendError): error_type="rate_limit";retryable=True
class LLMTimeoutError(LLMBackendError): error_type="timeout";retryable=True
class LLMConnectionError(LLMBackendError): error_type="connection";retryable=True
class LLMInvalidRequestError(LLMBackendError): error_type="invalid_request"
class LLMInvalidResponseError(LLMBackendError): error_type="invalid_response"
class LLMServerError(LLMBackendError): error_type="server_error";retryable=True
