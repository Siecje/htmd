from collections.abc import Generator
from concurrent.futures import Future
from contextlib import contextmanager
import socket
import threading
from unittest.mock import patch

import click
from click.testing import CliRunner
from flask import Flask
import htmd.cli.preview as preview_module
from werkzeug.serving import BaseWSGIServer, make_server


def _make_test_webserver(  # noqa: PLR0913
    app: Flask,
    host: str,
    port: int,
    *,
    threaded: bool,
    url_future: Future[str],
    preview_ready: threading.Event,
    webserver_collector: list | None,
) -> BaseWSGIServer:
    webserver = make_server(host, port, app, threaded=threaded)
    webserver.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Capture URL
    addr, actual_port = webserver.server_address[:2]
    host_str = addr.decode('utf-8') if isinstance(addr, bytes) else addr
    url_host = f'[{host_str}]' if ':' in host_str else host_str
    # If webserver is restarted, the future may already be set
    if not url_future.done():
        url_future.set_result(f'http://{url_host}:{actual_port}')

    original_serve_forever = webserver.serve_forever

    def _serve_forever(poll_interval: float = 0.5) -> None:
        preview_ready.set()
        return original_serve_forever(poll_interval=poll_interval)

    webserver.serve_forever = _serve_forever  # type: ignore[method-assign]

    if webserver_collector is not None:
        webserver_collector.append(webserver)
    return webserver


def _wrapped_invoke(
    runner: CliRunner,
    cmd: click.Command,
    args: list[str],
    result_future: Future[None],
) -> None:
    """Run Click and capture exceptions for the main thread."""
    try:
        runner.invoke(cmd, args, catch_exceptions=False)
        if not result_future.done():  # pragma: no cover
            result_future.set_result(None)
    except Exception as e:  # noqa: BLE001  # pragma: no cover
        result_future.set_exception(e)


@contextmanager
def run_preview(
    runner: CliRunner,
    args: list[str] | None = None,
    *,
    threaded:  bool = False,
    webserver_collector: list | None = None,
) -> Generator[str]:
    preview_ready = threading.Event()

    # Stores the URL
    url_future: Future[str] = Future()
    def create_webserver(app: Flask, host: str, port: int) -> BaseWSGIServer:
        return _make_test_webserver(
            app,
            host,
            port,
            threaded=threaded,
            url_future=url_future,
            preview_ready=preview_ready,
            webserver_collector=webserver_collector,
        )

    stop_event = threading.Event()

    with (
        # start_webserver is replaced
        # so it can handle each request in a thread
        # and we get an event on server_forever()
        patch(
            'htmd.cli.preview.create_webserver',
            side_effect=create_webserver,
        ),
        # create_stop_event is replaced so we can stop preview
        # since we can't send signals (ex. ctrl+c) to a thread
        patch(
            'htmd.cli.preview.create_stop_event',
            return_value=stop_event,
        ),
        # setup_stop_thread_on_signal is replaced
        # because threads can't receive signals
        patch(
            'htmd.cli.preview.set_stop_event_on_signal',
            side_effect=lambda _x: None,
        ),
    ):
        if args and '--port' not in args:
            args += ['--port', '0']
        elif not args:
            args = ['--port', '0']

        preview_result: Future[None] = Future()
        thread = threading.Thread(
            target=_wrapped_invoke,
            args=(runner, preview_module.preview, args, preview_result),
            daemon=True,
        )
        thread.start()

        try:
            # This is set right before the webserver starts
            is_ready = preview_ready.wait(timeout=30.0)
            if not is_ready and not thread.is_alive():  # pragma: no cover
                exception = preview_result.exception()
                if exception:
                    raise exception
                msg = 'Preview thread died before starting.'
                raise RuntimeError(msg)
            yield url_future.result(timeout=5.0)
        finally:
            # Trigger preview to stop
            stop_event.set()
            # Give time for the watchdog thread inside preview
            # to stop, it won't know to stop right away
            thread.join(timeout=5.0)
            # Display tracebacks if exceptions occurred
            preview_result.result()
