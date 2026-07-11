import re
def redact(value: str|None)->str|None:
    if value is None:return None
    value=re.sub(r"(?i)(authorization\s*[:=]\s*)([^\s]+)",r"\1***REDACTED***",value)
    return re.sub(r"(?i)(api[_-]?key\s*[:=]\s*)([^\s]+)",r"\1***REDACTED***",value)
