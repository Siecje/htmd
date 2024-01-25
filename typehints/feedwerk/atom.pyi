from ._compat import implements_to_string as implements_to_string, string_types as string_types
from _typeshed import Incomplete
from collections.abc import Generator

XHTML_NAMESPACE: str

def format_iso8601(obj): ...

class AtomFeed:
    default_generator: Incomplete
    title: Incomplete
    title_type: Incomplete
    url: Incomplete
    feed_url: Incomplete
    id: Incomplete
    updated: Incomplete
    author: Incomplete
    icon: Incomplete
    logo: Incomplete
    rights: Incomplete
    rights_type: Incomplete
    subtitle: Incomplete
    subtitle_type: Incomplete
    generator: Incomplete
    links: Incomplete
    entries: Incomplete
    def __init__(self, title: Incomplete | None = None, entries: Incomplete | None = None, **kwargs) -> None: ...
    def add(self, *args, **kwargs) -> None: ...
    def generate(self) -> Generator[Incomplete, None, None]: ...
    def to_string(self): ...
    def get_response(self): ...
    def __call__(self, environ, start_response): ...

class FeedEntry:
    title: Incomplete
    title_type: Incomplete
    content: Incomplete
    content_type: Incomplete
    url: Incomplete
    id: Incomplete
    updated: Incomplete
    summary: Incomplete
    summary_type: Incomplete
    author: Incomplete
    published: Incomplete
    rights: Incomplete
    links: Incomplete
    categories: Incomplete
    xml_base: Incomplete
    def __init__(self, title: Incomplete | None = None, content: Incomplete | None = None, feed_url: Incomplete | None = None, **kwargs) -> None: ...
    def generate(self) -> Generator[Incomplete, None, None]: ...
    def to_string(self): ...
