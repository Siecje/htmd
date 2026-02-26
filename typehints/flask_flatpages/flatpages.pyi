from collections.abc import Iterator
from typing import Any
from flask import Flask
from .page import Page as Page
from _typeshed import Incomplete

class FlatPages:
    default_config: Incomplete
    name: Incomplete
    config_prefix: str
    def __init__(self, app: Flask | None = None, name: str | None = None) -> None: ...
    
    # Must return an Iterator (usually of Page objects)
    def __iter__(self) -> Iterator[Page]: ...
    
    # Args and return types must be explicit
    def config(self, key: str) -> Any: ...
    
    def get(self, path: str, default: Any | None = None) -> Page | None: ...
    
    def get_or_404(self, path: str) -> Page: ...
    
    app: Flask | None
    def init_app(self, app: Flask) -> None: ...
    
    def reload(self) -> None: ...
    
    @property
    def root(self) -> str: ...
    
    @property
    def _pages(self) -> dict[str, Page]: ...
