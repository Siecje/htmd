from .page import Page as Page
from .utils import NamedStringIO as NamedStringIO, force_unicode as force_unicode, pygmented_markdown as pygmented_markdown
from _typeshed import Incomplete

START_TOKENS: Incomplete

class FlatPages:
    default_config: Incomplete
    name: Incomplete
    config_prefix: str
    def __init__(self, app: Incomplete | None = None, name: Incomplete | None = None) -> None: ...
    def __iter__(self): ...
    def config(self, key): ...
    def get(self, path, default: Incomplete | None = None): ...
    def get_or_404(self, path): ...
    app: Incomplete
    def init_app(self, app) -> None: ...
    def reload(self) -> None: ...
    @property
    def root(self): ...