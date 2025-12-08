from _typeshed import Incomplete
from functools import cached_property


class Page:
    path: Incomplete
    body: Incomplete
    html_renderer: Incomplete
    folder: Incomplete
    meta: dict
    def __init__(self, path, meta, body, html_renderer, folder) -> None: ...
    def __getitem__(self, name): ...
    def __html__(self): ...
    @cached_property
    def html(self) -> str: ...
