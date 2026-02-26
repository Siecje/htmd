from typing import Any, Callable
from _typeshed import Incomplete
from functools import cached_property


class Page:
    path: str
    body: str
    # The renderer receives the Page instance and returns rendered HTML
    html_renderer: Callable[["Page"], str]
    folder: str
    # Fixes: [type-arg]
    meta: dict[str, Any]

    # Fixes: [no-untyped-def]
    def __init__(
        self, 
        path: str, 
        meta: str, 
        body: str, 
    html_renderer: Callable[["Page"], str], 
        folder: str,
    ) -> None: ...

    # Fixes: [no-untyped-def]
    def __getitem__(self, name: str) -> Any: ...

    # Fixes: [no-untyped-def]
    def __html__(self) -> str: ...

    @cached_property
    def html(self) -> str: ...
