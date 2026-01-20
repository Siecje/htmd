from collections.abc import Generator
from pathlib import Path

from bs4 import BeautifulSoup
from flask import (
    Blueprint,
    current_app,
    render_template,
    Response,
    send_from_directory,
)
from flask.typing import ResponseReturnValue
from flask_flatpages import pygments_style_defs
from htmlmin import minify


main_bp = Blueprint('main', __name__)


@main_bp.after_request
def format_html(response: Response) -> Response:
    if response.mimetype == 'text/html':
        if current_app.config.get('PRETTY_HTML', False):
            response.data = BeautifulSoup(
                response.data,
                'html.parser',
            ).prettify()
        elif current_app.config.get('MINIFY_HTML', False):
            response.data = minify(response.data.decode('utf-8'))
    return response


@main_bp.route('/changes')
def changes() -> Response:
    """To cause browser refresh on file changes."""
    event = current_app.config.get('refresh_event')
    def event_stream() -> Generator[str]:
        if not event:
            return
        while True:
            event.wait()
            yield 'data: refresh\n\n'
            event.clear()

    return Response(event_stream(), mimetype='text/event-stream')


# Will end up in the static directory
@main_bp.route('/static/pygments.css')
def pygments_css() -> ResponseReturnValue:
    return pygments_style_defs('tango'), 200, {'Content-Type': 'text/css'}


@main_bp.route('/static/password-protect.js')
def static_password_protect() -> ResponseReturnValue:
    this_dir = Path(__file__).parent
    return send_from_directory(
        this_dir / '..' / 'example_site' / 'static',
        'password-protect.js',
    )


@main_bp.route('/')
def index() -> ResponseReturnValue:
    _posts = current_app.extensions['flatpages'][None]
    latest = sorted(
        _posts.published_posts,
        reverse=True,
        key=lambda p: p.meta['published'],
    )
    return render_template('index.html', active='home', posts=latest[:4])


# Used during preview
@main_bp.app_errorhandler(404)
def page_not_found(_e: Exception | int) -> ResponseReturnValue:
    return render_template('404.html'), 404
