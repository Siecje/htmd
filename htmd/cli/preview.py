from abc import abstractmethod
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


class BaseHandler(FileSystemEventHandler):
    def __init__(self, event: threading.Event, skips: list[str] | None = None) -> None:
        super().__init__()
        self._seen_mtimes: dict[str, int] = {}
        self.event = event
        self.skips = ['.swp', '.tmp'] + (skips or [])

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        if event.is_directory:
            return
        self.handle_event(event.src_path, is_new=True)

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if event.is_directory:
            return
        self.handle_event(event.src_path, is_new=False)

    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        if event.is_directory:
            return
        # A move/replace is essentially an update to the destination file
        self.handle_event(event.dest_path, is_new=False)

    @abstractmethod
    def handle_file(self, file_path: str, *, is_new: bool) -> None:
        """Handle a file event."""

    def handle_event(self, file_path: str | bytes, *, is_new: bool) -> None:
        if isinstance(file_path, bytes):
            file_path = file_path.decode('utf-8')
        for ending in self.skips:
            if file_path.endswith(ending):
                return

        path_obj = Path(file_path)
        new_mtime = path_obj.stat().st_mtime_ns
        if self._seen_mtimes.get(file_path) == new_mtime:
            # This was likely a metadata event or a double-trigger
            return
        self.handle_file(file_path, is_new=is_new)
        try:
            # Set new mtime if the file is changed in self.handle_file()
            self._seen_mtimes[file_path] = path_obj.stat().st_mtime_ns
        except FileNotFoundError:  # pragma: no cover
            # File was deleted before we could stat it
            with contextlib.suppress(KeyError):
                del self._seen_mtimes[file_path]


class StaticHandler(BaseHandler):
    def __init__(
        self,
        event: threading.Event,
        skips: list[str],
        static_directory: Path,
        *,
        css_minify: bool,
        js_minify: bool,
    ) -> None:
        super().__init__(event, skips)
        self.static_directory = static_directory
        self.css_minify = css_minify
        self.js_minify = js_minify

    def handle_file(
        self,
        file_path: str,
        *,
        is_new: bool,  # noqa: ARG002
    ) -> None:
        if (
            file_path.endswith('.css')
            and self.css_minify
            and combine_and_minify_css(self.static_directory)
        ):
            self.event.set()
            dst_css = 'combined.min.css'
            click.echo(f'Changes in {file_path}. Recreating {dst_css}...')
        elif (
            file_path.endswith('.js')
            and self.js_minify
            and combine_and_minify_js(self.static_directory)
        ):
            self.event.set()
            dst_js = 'combined.min.js'
            click.echo(f'Changes in {file_path}. Recreating {dst_js}...')


class PostsCreatedHandler(BaseHandler):
    def __init__(
        self,
        event: threading.Event,
        app: Flask,
    ) -> None:
        super().__init__(event)
        self.app = app

    def handle_file(self, file_path: str, *, is_new: bool) -> None:
        if not file_path.endswith('.md'):
            return
        with self.app.app_context():
            site.reload_posts(self.app)
        sync_posts(self.app)
        posts = self.app.extensions['flatpages'][None]
        for post in list(posts.pages.values()):
            validate_post(post, [])

        self.event.set()

        action = 'created' if is_new else 'updated'
        click.echo(f'Post {action} {file_path}.')


def watch_disk(  # noqa: PLR0913
    exit_event: threading.Event,
    start_event: threading.Event,
    refresh_event: threading.Event,
    # Static
    static_folder: str,
    css_minify: bool,  # noqa: FBT001
    js_minify: bool,  # noqa: FBT001
    # Posts
    app: Flask,
    posts_path: Path,
) -> None:
    """
    Watch static and posts folders for changes.

    When changes are detected:
        - combine and minify CSS and JS as needed.
        - sync posts as needed.
        - trigger refresh_event to notify browser to refresh.

    Args:
        exit_event: Event to signal thread to exit.
        start_event: Event to signal thread has started.
        refresh_event: Event to signal browser refresh.
        static_folder: Path to static files.
        css_minify: Whether to minify CSS on changes.
        js_minify: Whether to minify JS on changes.
        app: Flask application instance.
        posts_path: Path to posts files.

    """
    static_directory = Path(static_folder)

    observer = Observer()
    observer.daemon = True

    try:
        if static_directory.exists():
            skips = ['combined.min.css', 'combined.min.js']
            static_handler = StaticHandler(
                refresh_event,
                skips,
                static_directory,
                css_minify=css_minify,
                js_minify=js_minify,
            )
            observer.schedule(
                static_handler,
                path=str(static_directory),
                recursive=True,
            )
        posts_handler = PostsCreatedHandler(
            refresh_event,
            app,
        )
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
        if css_minify:
            combine_and_minify_css(static_directory)
        if js_minify:
            combine_and_minify_js(static_directory)
        start_event.set()

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
    host: str,
    port: int,
    *,
    css_minify: bool,
    js_minify: bool,
    drafts: bool,
) -> None:
    stop_event = create_stop_event()
    set_stop_event_on_signal(stop_event)

    app = site.create_app(show_drafts=drafts)

    ##
    # Thread: Watchdog on file changes
    ##
    # event to signal browser refresh during preview
    watch_thread_started = threading.Event()
    refresh_event = threading.Event()
    app.config['refresh_event'] = refresh_event
    watch_thread = threading.Thread(
        target=watch_disk,
        args=(
            stop_event,
            watch_thread_started,
            refresh_event,
            # static files
            app.static_folder,
            css_minify,
            js_minify,
            # posts files
            app,
            app.config['FLATPAGES_ROOT'],
        ),
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
    # -- Thread: Main Thread
    ##
    try:
        watch_thread.start()
        parent_pid_thread.start()
        watch_thread_started.wait()
        webserver_thread.start()

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
