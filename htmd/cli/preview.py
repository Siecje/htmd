import contextlib
import os
from pathlib import Path
import signal
import threading
import time
import types

import click
from flask import Flask
from watchdog.events import (
    DirCreatedEvent,
    DirModifiedEvent,
    FileCreatedEvent,
    FileModifiedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer
from werkzeug.serving import BaseWSGIServer, make_server

from .. import site
from ..utils import (
    combine_and_minify_css,
    combine_and_minify_js,
    sync_posts,
    validate_post,
)


def create_stop_event() -> threading.Event:
    """
    Provide event which when set will cause all threads to stop.

    This is a function so that tests can patch it
    and set the event to make preview stop.
    """
    return threading.Event()  # pragma: no cover


def set_stop_event_on_signal(
    stop_event: threading.Event,
) -> None:  # pragma: no cover
    def handle_signal(
        _signum: int,
        _frame: types.FrameType | None,
    ) -> None:
        stop_event.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)


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
    def __init__(self, app: Flask, event: threading.Event) -> None:
        super().__init__()
        self.app = app
        self.event = event

    def handle_event(self, event: FileSystemEvent, *, is_new_post: bool) -> None:
        if event.is_directory:
            return
        src_path = event.src_path
        if isinstance(src_path, bytes):
            src_path = src_path.decode('utf-8')
        if not src_path.endswith('.md'):
            return

        with self.app.app_context():
            site.reload_posts()
        sync_posts(self.app, site.posts)
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
    app: Flask,
    static_folder: str,
    posts_path: Path,
    exit_event: threading.Event,
    refresh_event: threading.Event,
) -> None:
    static_directory = Path(static_folder)

    observer = Observer()
    observer.daemon = True

    try:
        if static_directory.exists():
            static_handler = StaticHandler(static_directory, refresh_event)
            observer.schedule(
                static_handler,
                path=str(static_directory),
                recursive=True,
            )
        posts_handler = PostsCreatedHandler(app, refresh_event)
        observer.schedule(
            posts_handler,
            path=str(posts_path),
            recursive=True,
        )
        observer.start()
        while not exit_event.is_set():
            observer.join(timeout=0.1)
    finally:
        observer.stop()
        # Stop other threads
        exit_event.set()
        with contextlib.suppress(RuntimeError):
            observer.join(timeout=0.2)
        with contextlib.suppress(Exception):
            observer.unschedule_all()


def create_webserver(
        app: Flask,
        host: str,
        port: int,
) -> BaseWSGIServer:  # pragma: no cover
    webserver = make_server(
        host,
        port,
        app,
    )
    return webserver


def exit_if_parent_pid_changes() -> None:
    """
    Insurance if the tests don't cleanup preview as a subprocess.

    If the tests didn't call .terminate()
    this was being re-parented to PID 1.
    If that happens the process will exit.
    """
    parent_pid = os.getppid()
    while os.getppid() == parent_pid: # pragma: no branch
        time.sleep(1)
    os._exit(0)  # pragma: no cover


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
    *,
    css_minify: bool,
    js_minify: bool,
    drafts: bool,
) -> None:
    app = site.create_app(drafts)

    assert app.static_folder is not None
    if css_minify and combine_and_minify_css(Path(app.static_folder)):
        app.config['INCLUDE_CSS'] = app.jinja_env.globals['INCLUDE_CSS'] = True

    if js_minify and combine_and_minify_js(Path(app.static_folder)):
        app.config['INCLUDE_JS'] = app.jinja_env.globals['INCLUDE_JS'] = True

    sync_posts(app, site.posts)

    stop_event = create_stop_event()
    set_stop_event_on_signal(stop_event)

    ##
    # Thread: Watchdog on file changes
    ##
    refresh_event = threading.Event()
    app.config['refresh_event'] = refresh_event
    watch_thread = threading.Thread(
        target=watch_disk,
        args=(
            app,
            app.static_folder,
            app.config['FLATPAGES_ROOT'],
            stop_event,
            refresh_event,
        ),
        daemon=True,
    )

    ##
    # -- Thread: Webserver
    ##
    app.jinja_env.globals['PREVIEW'] = True
    app.jinja_env.auto_reload = True
    webserver = create_webserver(app, host, port)
    webserver_thread = threading.Thread(
        target=webserver.serve_forever,
        daemon=True,
    )

    ##
    # -- Thread: Force exit if parent process changes
    ##
    parent_pid_thread = threading.Thread(
        target=exit_if_parent_pid_changes,
        daemon=True,
    )

    ##
    # -- Thread: Main Thread
    ##
    try:
        watch_thread.start()
        webserver_thread.start()
        parent_pid_thread.start()

        while not stop_event.is_set():
            if not webserver_thread.is_alive():
                click.echo('Webserver crashed! Restarting...')
                webserver = create_webserver(app, host, port)
                webserver_thread = threading.Thread(
                    target=webserver.serve_forever,
                    daemon=True,
                )
                webserver_thread.start()

            # Wait a bit before checking again
            stop_event.wait(timeout=1)

    finally:
        webserver.shutdown()
        # Trigger watch_thread to stop
        stop_event.set()
        # Wait for threads to stop
        with contextlib.suppress(RuntimeError):  # if a thread didn't start
            webserver_thread.join()
            watch_thread.join()
        click.echo('Preview stopped.')
