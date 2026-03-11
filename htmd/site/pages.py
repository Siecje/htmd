from pathlib import Path

from flask import (
    abort,
    Blueprint,
    render_template,
)
from flask.typing import ResponseReturnValue


pages = Blueprint('pages', __name__)


@pages.route('/<path:path>/')
def page(path: str) -> ResponseReturnValue:
    assert pages.template_folder is not None
    pages_folder = Path(pages.template_folder)
    target_file = pages_folder / f'{path}.html'

    try:
        target_file.resolve().relative_to(pages_folder.resolve())
    except ValueError:
        abort(404)

    if not target_file.is_file():
        abort(404)

    ret = render_template(f'{path}.html', active=path)
    return ret
