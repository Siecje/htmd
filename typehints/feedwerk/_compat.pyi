from _typeshed import Incomplete
from io import BytesIO as BytesIO, StringIO

PY2: Incomplete
WIN: Incomplete
unichr = chr
text_type = str
string_types: Incomplete
integer_types: Incomplete
iterkeys: Incomplete
itervalues: Incomplete
iteritems: Incomplete
iterlists: Incomplete
iterlistvalues: Incomplete
int_to_byte: Incomplete
iter_bytes: Incomplete

def reraise(tp, value, tb: Incomplete | None = None) -> None: ...

fix_tuple_repr: Incomplete
implements_iterator: Incomplete
implements_to_string: Incomplete
implements_bool: Incomplete
native_string_result: Incomplete
imap = map
izip = zip
ifilter = filter
range_type = range
NativeStringIO = StringIO

def make_literal_wrapper(reference): ...
def normalize_string_tuple(tup): ...

try_coerce_native: Incomplete
wsgi_get_bytes: Incomplete

def wsgi_decoding_dance(s, charset: str = 'utf-8', errors: str = 'replace'): ...
def wsgi_encoding_dance(s, charset: str = 'utf-8', errors: str = 'replace'): ...
def to_bytes(x, charset=..., errors: str = 'strict'): ...
def to_native(x, charset=..., errors: str = 'strict'): ...
def to_unicode(x, charset=..., errors: str = 'strict', allow_none_charset: bool = False): ...
