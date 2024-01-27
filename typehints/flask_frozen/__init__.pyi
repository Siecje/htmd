from _typeshed import Incomplete
from collections.abc import Generator
import types
from typing import NamedTuple


__all__ = ['Freezer', 'walk_directory', 'relative_url_for']

class FrozenFlaskWarning(Warning): ...
class MissingURLGeneratorWarning(FrozenFlaskWarning): ...
class MimetypeMismatchWarning(FrozenFlaskWarning): ...
class NotFoundWarning(FrozenFlaskWarning): ...
class RedirectWarning(FrozenFlaskWarning): ...

class Page(NamedTuple):
    url: Incomplete
    path: Incomplete

class Freezer:
    url_generators: Incomplete
    log_url_for: Incomplete
    def __init__(self, app: Incomplete | None = None, with_static_files: bool = True, with_no_argument_rules: bool = True, log_url_for: bool = True) -> None: ...
    app: Incomplete
    url_for_logger: Incomplete
    def init_app(self, app) -> None: ...
    def register_generator(self, function): ...
    @property
    def root(self): ...
    def freeze_yield(self) -> Generator[Incomplete, None, None]: ...
    def freeze(self): ...
    def all_urls(self) -> Generator[Incomplete, None, None]: ...
    def urlpath_to_filepath(self, path): ...
    def serve(self, **options) -> None: ...
    def run(self, **options) -> None: ...
    def make_static_app(self): ...
    def static_files_urls(self) -> Generator[Incomplete, None, None]: ...
    def no_argument_rules_urls(self) -> Generator[Incomplete, None, None]: ...

def walk_directory(root, ignore=()) -> Generator[Incomplete, None, None]: ...
def relative_url_for(endpoint, **values): ...

class UrlForLogger:
    app: Incomplete
    logged_calls: Incomplete
    def __init__(self, app) -> None: ...
    def __enter__(self) -> None: ...
    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: types.TracebackType | None) -> None: ...
    def iter_calls(self) -> Generator[Incomplete, None, None]: ...