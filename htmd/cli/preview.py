import contextlib
import os
from pathlib import Path
import signal
import socket
import threading
import time
import types

import click
from flask import Flask
from watchdog.events import (
    DirCreatedEvent,
    DirModifiedEvent,
    DirMovedEvent,
    FileCreatedEvent,
    FileModifiedEvent,
    FileMovedEvent,
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
        self._seen_mtimes: dict[str, int] = {}

    def handle_event(self, file_path: str | bytes) -> None:
        if isinstance(file_path, bytes):
            file_path = file_path.decode('utf-8')
        dst_css = 'combined.min.css'
        dst_js = 'combined.min.js'
        skips = [dst_css, dst_js, '.swp', '.tmp']
        for ending in skips:
            if file_path.endswith(ending):
                return

        new_mtime = Path(file_path).stat().st_mtime_ns
        if self._seen_mtimes.get(file_path) == new_mtime:
            # This was likely a metadata event or a double-trigger
            return

        if file_path.endswith('.css') and combine_and_minify_css(self.static_directory):
            self.event.set()
            click.echo(f'Changes in {file_path}. Recreating {dst_css}...')
        elif file_path.endswith('.js') and combine_and_minify_js(self.static_directory):
            self.event.set()
            click.echo(f'Changes in {file_path}. Recreating {dst_js}...')
        self._seen_mtimes[file_path] = new_mtime

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        if event.is_directory:
            return
        self.handle_event(event.src_path)

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if event.is_directory:
            return
        self.handle_event(event.src_path)

    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        if event.is_directory:
            return
        self.handle_event(event.dest_path)


class PostsCreatedHandler(FileSystemEventHandler):
    def __init__(self, app: Flask, event: threading.Event) -> None:
        super().__init__()
        self.app = app
        self.event = event
        self._seen_mtimes: dict[str, int] = {}

    def handle_event(self, file_path: str | bytes, *, is_new_post: bool) -> None:
        if isinstance(file_path, bytes):
            file_path = file_path.decode('utf-8')
        if not file_path.endswith('.md'):
            return

        new_mtime = Path(file_path).stat().st_mtime_ns
        if self._seen_mtimes.get(file_path) == new_mtime:
            # This was likely a metadata event or a double-trigger
            return

        with self.app.app_context():
            site.reload_posts(self.app)
        sync_posts(self.app)
        posts = self.app.extensions['flatpages'][None]
        for post in posts:
            validate_post(post, [])

        self._seen_mtimes[file_path] = new_mtime
        self.event.set()

        action = 'created' if is_new_post else 'updated'
        click.echo(f'Post {action} {file_path}.')

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        if event.is_directory:
            return
        self.handle_event(event.src_path, is_new_post=True)

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if event.is_directory:
            return
        self.handle_event(event.src_path, is_new_post=False)

    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        if event.is_directory:
            return
        # A move/replace is essentially an update to the destination file
        self.handle_event(event.dest_path, is_new_post=False)


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

        # If webserver starts before watchdog then updates can be missed
        # Ensure everything is current now that watchdogs are running
        with app.app_context():
            site.reload_posts(app)
        sync_posts(app)
        if app.config.get('INCLUDE_CSS'):
            combine_and_minify_css(static_directory)
        if app.config.get('INCLUDE_JS'):
            combine_and_minify_js(static_directory)

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
    # Allows immediate restart on the same port without OS lock-out
    webserver.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
    app = site.create_app(show_drafts=drafts)

    assert app.static_folder is not None
    if css_minify and combine_and_minify_css(Path(app.static_folder)):
        app.config['INCLUDE_CSS'] = app.jinja_env.globals['INCLUDE_CSS'] = True

    if js_minify and combine_and_minify_js(Path(app.static_folder)):
        app.config['INCLUDE_JS'] = app.jinja_env.globals['INCLUDE_JS'] = True

    sync_posts(app)

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
    if port == 0:
        port = webserver.server_port
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
