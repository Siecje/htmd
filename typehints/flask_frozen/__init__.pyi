import collections
import datetime
import os
import pathlib
import threading
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Callable, ContextManager, NamedTuple, TypeVar, Union

from flask import Flask


__all__ = ['Freezer', 'walk_directory', 'relative_url_for']


# A type alias for the various things a generator can yield:
# 1. A simple URL string
# 2. A url_for kwargs (endpoint defaults to function name)
# 3. A 2-tuple: (endpoint, url_for kwargs)
# 4. A 3-tuple: (endpoint, url_for kwargs, last_modified)
URLGeneratorResult = Union[
    str,
    Mapping[str, Any],
    tuple[str, Mapping[str, Any]],
    tuple[str, Mapping[str, Any], datetime.datetime]
]


F = TypeVar("F", bound=Callable[..., Iterable[URLGeneratorResult]])


class FrozenFlaskWarning(Warning): ...
class MissingURLGeneratorWarning(FrozenFlaskWarning): ...
class MimetypeMismatchWarning(FrozenFlaskWarning): ...
class NotFoundWarning(FrozenFlaskWarning): ...
class RedirectWarning(FrozenFlaskWarning): ...

class Page(NamedTuple):
    url: str
    path: pathlib.Path

class Freezer:
    app: Flask | None
    url_generators: list[Callable[[], Iterable[URLGeneratorResult]]]
    log_url_for: bool
    url_for_logger: UrlForLogger

    def __init__(
        self,
        app: Flask | None = None,
        with_static_files: bool = True,
        with_no_argument_rules: bool = True,
        log_url_for: bool = True,
    ) -> None: ...

    def init_app(self, app: Flask | None) -> None: ...
    
    def register_generator(self, function: F) -> F: ...

    @property
    def root(self) -> pathlib.Path: ...

    def freeze_yield(self) -> Iterator[Page]: ...
    def freeze(self) -> set[str]: ...
    def all_urls(self) -> Iterator[str]: ...
    def urlpath_to_filepath(self, path: str) -> str: ...
    def serve(self, **options: Any) -> None: ...
    def run(self, **options: Any) -> None: ...
    def make_static_app(self) -> Flask: ...
    
    def static_files_urls(self) -> Iterator[tuple[str, dict[str, Any]]]: ...
    def no_argument_rules_urls(self) -> Iterator[tuple[str, dict[str, Any]]]: ...

def walk_directory(root: str | os.PathLike[str], ignore: Iterable[str] = ()) -> Iterator[str]: ...

def relative_url_for(endpoint: str, **values: Any) -> str: ...

def patch_url_for(app: Flask) -> ContextManager[None]: ...

class UrlForLogger:
    app: Flask
    logged_calls: collections.deque[tuple[str, dict[str, Any]]]
    _enabled: bool
    _lock: threading.Lock
    
    def __init__(self, app: Flask) -> None: ...
    def __enter__(self) -> UrlForLogger: ...
    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None: ...
    def iter_calls(self) -> Iterator[tuple[str, dict[str, Any]]]: ...
