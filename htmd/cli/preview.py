from abc import abstractmethod
import contextlib
import dataclasses
import hashlib
import os
from pathlib import Path
import signal
import socket
import threading
import time
import types
import typing

import click
from flask import Flask
from watchdog.events import (
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    DirMovedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer
from werkzeug.serving import BaseWSGIServer, make_server

from .. import site
from ..utils import (
    get_post_hash,
    get_static_files,
    minify_css_file,
    minify_css_files,
    minify_js_file,
    minify_js_files,
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


class EventUpdates(typing.TypedDict):
    src_path: str
    dest_path: str


class BaseHandler(FileSystemEventHandler):
    def __init__(
        self,
        event: threading.Event,
        extensions: tuple[str, ...] | None = None,
        skips: list[str] | None = None,
    ) -> None:
        super().__init__()
        self._file_hashes: dict[str, str] = {}
        self.event = event
        self.extensions = extensions or ()
        self.skips = ['.swp', '.tmp', '.swx'] + (skips or [])

    def _remove_file_hash(self, path: Path) -> None:
        file_hash_key = str(path.resolve())
        self._file_hashes.pop(file_hash_key, None)

    def dispatch(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        # Ensure paths are str
        updates: EventUpdates = {
            'src_path': os.fsdecode(event.src_path),
            'dest_path': os.fsdecode(event.dest_path),
        }
        event = dataclasses.replace(event, **updates)
        super().dispatch(event)

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        path_obj = Path(typing.cast('str', event.src_path))
        self.handle_event(path_obj, event.event_type)

    def on_deleted(self, event: DirDeletedEvent | FileDeletedEvent) -> None:
        path_obj = Path(typing.cast('str', event.src_path))
        if path_obj.exists():
            return
        self.handle_event(path_obj, event.event_type)
        self._remove_file_hash(path_obj)

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        path_obj = Path(typing.cast('str', event.src_path))
        self.handle_event(path_obj, event.event_type)

    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        path_obj = Path(typing.cast('str', event.src_path))
        self._remove_file_hash(path_obj)

        dst_path = Path(typing.cast('str', event.dest_path))
        self.handle_event(dst_path, event.event_type)

    @abstractmethod
    def handle_file(self, file_path: Path, event_type: str) -> None:
        """Handle a file event."""

    def get_file_hash(self, file_path: Path) -> str:
        with file_path.open('rb') as f:
            digest = hashlib.file_digest(f, 'sha256')
        return digest.hexdigest()

    def handle_event(self, file_path: Path, event_type: str) -> None:
        if file_path.name in self.skips or file_path.suffix in self.skips:
            return

        if self.extensions and file_path.suffix not in self.extensions:
            return

        if event_type == 'deleted':
            self.handle_file(file_path, event_type)
            return

        try:
            # Ignore empty files
            if file_path.stat().st_size == 0:
                return
            file_hash = self.get_file_hash(file_path)
        except FileNotFoundError:  # pragma: no cover
            self._remove_file_hash(file_path)
            return

        hash_key = str(file_path.resolve())
        if self._file_hashes.get(hash_key) == file_hash:
            # This was likely a metadata event or a double-trigger
            return

        self.handle_file(file_path, event_type)

        # Set mtime from before processing so we don't miss events
        # even though it means we will try to handle the same file again
        # if it is modified in self.handle_file()
        self._file_hashes[hash_key] = file_hash


class StaticHandler(BaseHandler):
    def __init__(
        self,
        event: threading.Event,
        static_directory: Path,
        minify_css_dir: Path | None,
        minify_js_dir: Path | None,
    ) -> None:
        super().__init__(event, ('.css', '.js'))
        self.static_directory = static_directory
        self.minify_css_dir = minify_css_dir
        self.minify_js_dir = minify_js_dir

    @typing.override
    def handle_file(
        self,
        file_path: Path,
        event_type: str,
    ) -> None:
        # Determine which minification directory to use
        target_dir = None
        if file_path.suffix == '.css' and '.min.css' not in file_path.name:
            target_dir = self.minify_css_dir
        elif file_path.suffix == '.js' and '.min.js' not in file_path.name:
            target_dir = self.minify_js_dir

        if not target_dir:
            return

        # Construct the path where the minified file lives/would live
        # This mirrors the logic inside your minify functions
        relative_path = file_path.relative_to(self.static_directory)
        min_suffix = f'.min{file_path.suffix}'
        minify_path = target_dir / relative_path.with_suffix(min_suffix)

        if event_type == 'deleted':
            try:
                minify_path.unlink()
            except FileNotFoundError:
                pass
            else:
                self.event.set()
                click.echo(f'Source deleted. Removed minified file: {minify_path.name}')
            return

        if file_path.suffix == '.css':
            minify_css_file(self.static_directory, file_path, target_dir)
        else:
            minify_js_file(self.static_directory, file_path, target_dir)

        self.event.set()
        click.echo(f'Changes in {file_path.name}. Updated {minify_path.name}')


class PostHandler(BaseHandler):
    def __init__(
        self,
        event: threading.Event,
        app: Flask,
    ) -> None:
        super().__init__(event, ('.md',))
        self.app = app

    @typing.override
    def get_file_hash(self, file_path: Path) -> str:
        posts = site.posts.get_posts(self.app)
        posts.reload()
        sync_posts(self.app)
        post = posts.get(file_path.stem)
        if not post:  # pragma: no cover
            msg = f'Post {file_path.stem} does not exist'
            raise FileNotFoundError(msg)
        with self.app.app_context():
            post_hash = get_post_hash(post)
        return post_hash

    @typing.override
    def handle_file(self, file_path: Path, event_type: str) -> None:
        if event_type == 'deleted':
            posts = site.posts.get_posts(self.app)
            posts.reload()
            sync_posts(self.app)
            self.event.set()
            click.echo(f'Post {event_type} {file_path.name}.')
            return

        posts = site.posts.get_posts(self.app)
        post = posts.get(file_path.stem)
        if not post:  # pragma: no cover
            return

        validate_post(post, [])
        self.event.set()
        click.echo(f'Post {event_type} {file_path.name}.')


class TemplateHandler(BaseHandler):
    def __init__(self, event: threading.Event, app: Flask) -> None:

        super().__init__(event, ('.html',))
        self.app = app

    @typing.override
    def handle_file(self, file_path: Path, event_type: str) -> None:
        self.app.jinja_env.cache.clear()  # type: ignore[union-attr]
        self.event.set()
        click.echo(f'Template {event_type} {file_path.name}.')


def watch_disk(
    exit_event: threading.Event,
    start_event: threading.Event,
    refresh_event: threading.Event,
    app: Flask,
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
        app: Flask application instance.

    """
    minify_css = app.config['MINIFY_CSS']
    minify_js = app.config['MINIFY_JS']
    assert app.static_folder is not None
    static_directory = Path(app.static_folder)
    if minify_css:
        minify_css_dir = app.config.get('static_dir_css', static_directory)
    else:
        minify_css_dir = None
    if minify_js:
        minify_js_dir = app.config.get('static_dir_js', static_directory)
    else:
        minify_js_dir = None

    posts_path = app.config['FLATPAGES_ROOT']
    template_path = Path(app.config['TEMPLATE_FOLDER'])

    observer = Observer()
    observer.daemon = True

    try:
        if static_directory.exists():
            static_handler = StaticHandler(
                refresh_event,
                static_directory,
                minify_css_dir,
                minify_js_dir,
            )
            observer.schedule(
                static_handler,
                path=str(static_directory),
                recursive=True,
            )
        posts_handler = PostHandler(
            refresh_event,
            app,
        )
        observer.schedule(
            posts_handler,
            path=str(posts_path),
            recursive=True,
        )
        if template_path.exists():
            template_handler = TemplateHandler(refresh_event, app)
            observer.schedule(
                template_handler,
                path=str(template_path),
            )
        observer.start()

        # If webserver starts before watchdog then updates can be missed
        # Ensure everything is current now that watchdogs are running
        posts = site.posts.get_posts(app)
        posts.reload()
        sync_posts(app)
        if minify_css:
            files_css = get_static_files(static_directory, '.css')
            minify_css_files(static_directory, files_css, minify_css_dir)
        if minify_js:
            files_js = get_static_files(static_directory, '.js')
            minify_js_files(static_directory, files_js, minify_js_dir)
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
        threaded=True,
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
    while os.getppid() == parent_pid:  # pragma: no branch
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
    '--drafts',
    default=False,
    help='Show draft posts in the preview.',
    is_flag=True,
)
@click.option(
    '--minify-css/--no-minify-css',
    default=True,
    help='If CSS should be minified',
    is_flag=True,
    show_default=True,
)
@click.option(
    '--css-minify/--no-css-minify',
    'minify_css',
    default=None,
    help='Alias for --minify-css/--no-minify-css',
)
@click.option(
    '--minify-js/--no-minify-js',
    default=True,
    help='If JavaScript should be minified',
    is_flag=True,
    show_default=True,
)
@click.option(
    '--js-minify/--no-js-minify',
    'minify_js',
    default=None,
    help='Alias for --minify-js/--no-minify-js',
)
def preview(
    host: str,
    port: int,
    *,
    drafts: bool,
    minify_css: bool,
    minify_js: bool,
) -> None:
    stop_event = create_stop_event()
    set_stop_event_on_signal(stop_event)

    app = site.create_app(
        show_drafts=drafts,
        minify_css=minify_css,
        minify_js=minify_js,
    )

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
            app,
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
                click.secho('Webserver crashed! Restarting...', fg='red')
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
