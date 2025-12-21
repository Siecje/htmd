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
    # ensure page is from pages directory
    # otherwise this will load any templates in the template folder
    pages_folder = pages.template_folder
    if not isinstance(pages_folder, Path) or not pages_folder.is_dir():
        abort(404)
    for page_path in pages_folder.iterdir():
        if path == page_path.stem:
            break
    else:
        abort(404)
    ret = render_template(path + '.html', active=path)
    return ret
