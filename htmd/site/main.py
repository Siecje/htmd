from collections.abc import Callable, Generator
from pathlib import Path
import threading

from bs4 import BeautifulSoup
from flask import (
    Blueprint,
    current_app,
    make_response,
    render_template,
    Response,
    send_from_directory,
)
from flask.typing import ResponseReturnValue
from flask_flatpages import pygments_style_defs
from htmlmin import minify

from .posts import get_posts


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


def event_stream(event: threading.Event | None) -> Generator[str]:
    if not event:
        return
    while True:
        event.wait(timeout=1.0)
        if event.is_set():
            yield 'data: refresh\n\n'
            event.clear()


@main_bp.route('/changes')
def changes() -> Response:
    """To cause browser refresh on file changes."""
    event = current_app.config.get('refresh_event')
    return Response(event_stream(event), mimetype='text/event-stream')


# Will end up in the static directory
@main_bp.route('/static/pygments.css')
def pygments_css() -> ResponseReturnValue:
    response = make_response(pygments_style_defs('tango'))
    response.headers['Content-Type'] = 'text/css'
    # Tells browser to cache for 1 year
    response.cache_control.max_age = 31536000
    response.cache_control.public = True
    return response


@main_bp.route('/static/password-protect.js')
def static_password_protect() -> ResponseReturnValue:
    this_dir = Path(__file__).parent
    return send_from_directory(
        this_dir / '..' / 'example_site' / 'static',
        'password-protect.js',
    )


@main_bp.route('/static/htmd.css')
def static_htmd_styles() -> ResponseReturnValue:
    this_dir = Path(__file__).parent
    return send_from_directory(
        this_dir / '..' / 'example_site' / 'static',
        'htmd.css',
    )


@main_bp.route('/static/htmd.js')
def static_htmd_js() -> ResponseReturnValue:
    this_dir = Path(__file__).parent
    return send_from_directory(
        this_dir / '..' / 'example_site' / 'static',
        'htmd.js',
    )


@main_bp.route('/')
def index() -> ResponseReturnValue:
    posts = get_posts()
    latest = sorted(
        posts.published_posts,
        reverse=True,
        key=lambda p: p.meta['published'],
    )
    return render_template('index.html', active='home', posts=latest[:4])


# Used during preview
@main_bp.app_errorhandler(404)
def page_not_found(_e: Exception | int) -> ResponseReturnValue:
    return render_template('404.html'), 404


def create_redirect_view(destination_url: str) -> Callable[[], ResponseReturnValue]:
    def view() -> ResponseReturnValue:
        return render_template(
            'redirect.html',
            destination_url=destination_url,
        )
    return view
