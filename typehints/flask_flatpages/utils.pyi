from typing import Any
from io import StringIO
from _typeshed import Incomplete

class NamedStringIO(StringIO):
    name: Any
    # Even __init__ arguments (besides self) need types
    def __init__(self, content: str | bytes, name: str) -> None: ...

# value: Any is required if it can be str or bytes
def force_unicode(value: Any, encoding: str = 'utf-8', errors: str = 'strict') -> str: ...

# Adding return type -> str (or whatever markdown returns)
def pygmented_markdown(text: str, flatpages: Any | None = None) -> str: ...

def pygments_style_defs(style: str = 'default') -> str: ...
