from pathlib import Path
import signal
import threading
import types

import click
from watchdog.events import (
    DirCreatedEvent,
    DirModifiedEvent,
    FileCreatedEvent,
    FileModifiedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from .. import site
from ..utils import (
    combine_and_minify_css,
    combine_and_minify_js,
    validate_post,
)


class StaticHandler(FileSystemEventHandler):
    def __init__(self, static_directory: Path, event: threading.Event) -> None:
        super().__init__()
        self.static_directory = static_directory
        self.event = event

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if event.is_directory:
            return
        src_path = event.src_path
        if isinstance(src_path, bytes):
            src_path = src_path.decode('utf-8')
        dst_css = 'combined.min.css'
        dst_js = 'combined.min.js'
        if dst_css in src_path or dst_js in src_path or '.swp' in src_path:
            return

        if src_path.endswith('.css') and combine_and_minify_css(self.static_directory):
            self.event.set()
            click.echo(f'Changes in {src_path}. Recreating {dst_css}...')
        elif src_path.endswith('.js') and combine_and_minify_js(self.static_directory):
            self.event.set()
            click.echo(f'Changes in {src_path}. Recreating {dst_js}...')


class PostsCreatedHandler(FileSystemEventHandler):
    def __init__(self, event: threading.Event) -> None:
        super().__init__()
        self.event = event

    def handle_event(self, event: FileSystemEvent, is_new_post: bool) -> None:  # noqa: FBT001
        if event.is_directory:
            return
        src_path = event.src_path
        if isinstance(src_path, bytes):
            src_path = src_path.decode('utf-8')
        if not src_path.endswith('.md'):
            return

        site.reload_posts()
        for post in site.posts:
            validate_post(post, [])

        self.event.set()

        action = 'created' if is_new_post else 'updated'
        click.echo(f'Post {action} {src_path}.')

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        self.handle_event(event, is_new_post=True)

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        self.handle_event(event, is_new_post=False)


def watch_disk(
    static_folder: str,
    posts_path: Path,
    exit_event: threading.Event,
    refresh_event: threading.Event,
) -> None:
    observer = Observer()

    static_directory = Path(static_folder)
    static_handler = StaticHandler(static_directory, refresh_event)
    observer.schedule(
        static_handler,
        path=str(static_directory),
        recursive=True,
    )

    posts_handler = PostsCreatedHandler(refresh_event)
    observer.schedule(
        posts_handler,
        path=str(posts_path),
        recursive=True,
    )

    observer.start()

    try:
        while not exit_event.is_set():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()


@click.command('preview', short_help='Serve files to preview site.')
@click.pass_context
@click.option(
    '--host', '-h',
    default='::1',
    help='Location to access the files.',
)
@click.option(
    '--port', '-p',
    default=9090,
    help='Port on which to serve the files.',
)
@click.option(
    '--css-minify/--no-css-minify',
    default=True,
    help='If CSS should be minified',
)
@click.option(
    '--js-minify/--no-js-minify',
    default=True,
    help='If JavaScript should be minified',
)
@click.option(
    '--drafts',
    default=False,
    help='Show draft posts in the preview.',
    is_flag=True,
)
def preview(
    _ctx: click.Context,
    host: str,
    port: int,
    css_minify: bool,  # noqa: FBT001
    js_minify: bool,  # noqa: FBT001
    drafts: bool,  # noqa: FBT001
) -> None:
    app = site.init_app(drafts)

    assert site.app.static_folder is not None
    if css_minify and combine_and_minify_css(Path(site.app.static_folder)):
        app.config['INCLUDE_CSS'] = app.jinja_env.globals['INCLUDE_CSS'] = True

    if js_minify and combine_and_minify_js(Path(site.app.static_folder)):
        app.config['INCLUDE_JS'] = app.jinja_env.globals['INCLUDE_JS'] = True

    stop_event = threading.Event()

    def handle_sigterm(
        _signum: int,
        _frame: types.FrameType | None,
    ) -> None:  # pragma: no cover
        stop_event.set()
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    refresh_event = threading.Event()
    app.config['refresh_event'] = refresh_event
    watch_thread = threading.Thread(
        target=watch_disk,
        args=(
            app.static_folder,
            app.config['FLATPAGES_ROOT'],
            stop_event,
            refresh_event,
        ),
    )
    watch_thread.start()

    app.jinja_env.globals['PREVIEW'] = True
    try:
        app.run(debug=True, host=host, port=port)
    finally:
        # After Flask has been stopped stop watchdog
        stop_event.set()
