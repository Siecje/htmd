from collections.abc import Generator
from contextlib import contextmanager
import socket
import threading
from unittest.mock import patch

from click.testing import CliRunner
from flask import Flask
import htmd.cli.preview as preview_module
from werkzeug.serving import BaseWSGIServer, make_server


@contextmanager
def run_preview(
    runner: CliRunner,
    args: list[str] | None = None,
    *,
    threaded:  bool = False,
    webserver_collector: list | None = None,
) -> Generator[str]:
    preview_ready = threading.Event()

    # A list is used to "leak" the dynamic URL out of the inner function
    actual_url_container = []

    def create_webserver(app: Flask, host: str, port: int) -> BaseWSGIServer:
        webserver = make_server(
            host,
            port,
            app,
            threaded=threaded,
        )
        assert webserver is not None
        # Prevent "Address already in use" errors when running tests back-to-back
        # by bypassing the OS's TCP TIME_WAIT cooldown period.
        webserver.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):  # pragma: no cover
            webserver.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        # Capture the actual port assigned by the OS
        real_host, real_port = webserver.server_address[:2]
        if isinstance(real_host, bytes):  # pragma: no branch
            real_host = real_host.decode('utf-8')  # pragma: no cover
        # Format for IPv6 if necessary
        url_host = f'[{real_host}]' if ':' in real_host else real_host
        actual_url_container.append(f'http://{url_host}:{real_port}')

        # Replace serve_forever() so our event is set
        # as close to when the webserver is available
        original_serve_forever = webserver.serve_forever
        def _serve_forever(poll_interval: float = 0.5) -> None:
            preview_ready.set()
            original_serve_forever(poll_interval=poll_interval)
        webserver.serve_forever = _serve_forever  # type: ignore[method-assign]

        if webserver_collector is not None:
            webserver_collector.append(webserver)
        return webserver

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
        thread = threading.Thread(
            target=runner.invoke,
            args=(preview_module.preview, args),
            kwargs={'catch_exceptions': False},
            daemon=True,
        )
        thread.start()

        try:
            # This is set right before the webserver starts
            is_ready = preview_ready.wait(timeout=30.0)
            if not is_ready and not thread.is_alive():  # pragma: no branch
                msg = 'Preview thread died before starting.'  # pragma: no cover
                raise RuntimeError(msg)  # pragma: no cover
            yield actual_url_container[0]
        finally:
            # Trigger preview to stop
            stop_event.set()
            # Give time for the watchdog thread inside preview
            # to stop, it won't know to stop right away
            thread.join(timeout=2.0)
