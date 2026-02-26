from _typeshed import Incomplete
from io import BytesIO as BytesIO, StringIO
from typing import Any, Type

PY2: bool
WIN: bool
unichr = chr
text_type = str
string_types: tuple[Type[Any], ...]
integer_types: tuple[Type[Any], ...]

# Type everything as Any/Incomplete if it's just legacy glue
iterkeys: Any
itervalues: Any
iteritems: Any
iterlists: Any
iterlistvalues: Any
int_to_byte: Any
iter_bytes: Any

def reraise(tp: Any, value: Any, tb: Any | None = None) -> None: ...

fix_tuple_repr: Any
implements_iterator: Any
implements_to_string: Any
implements_bool: Any
native_string_result: Any
imap = map
izip = zip
ifilter = filter
range_type = range
NativeStringIO = StringIO

def make_literal_wrapper(reference: Any) -> Any: ...
def normalize_string_tuple(tup: tuple[Any, ...]) -> tuple[str, ...]: ...

try_coerce_native: Any
wsgi_get_bytes: Any

# The "Dancing" functions usually handle bytes/str conversion
def wsgi_decoding_dance(s: Any, charset: str = 'utf-8', errors: str = 'replace') -> str: ...
def wsgi_encoding_dance(s: Any, charset: str = 'utf-8', errors: str = 'replace') -> str: ...

def to_bytes(x: Any, charset: Any = ..., errors: str = 'strict') -> bytes: ...
def to_native(x: Any, charset: Any = ..., errors: str = 'strict') -> str: ...
def to_unicode(x: Any, charset: Any = ..., errors: str = 'strict', allow_none_charset: bool = False) -> str: ...
