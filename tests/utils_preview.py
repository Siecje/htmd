from collections.abc import Generator
from contextlib import contextmanager
import threading
import time
from unittest.mock import patch

from click.testing import CliRunner
from flask import Flask
import htmd.cli.preview as preview_module
import requests
from werkzeug.serving import BaseWSGIServer, make_server


BASE_URL = 'http://[::1]:9090'


WEBSERVER: None | BaseWSGIServer = None
WEBSERVER_THREADED = False
def start_webserver(app: Flask, host: str, port: int) -> None:
    # global keyword is required for tests to pass
    global WEBSERVER # noqa: PLW0603
    WEBSERVER = make_server(
        host,
        port,
        app,
        threaded=WEBSERVER_THREADED,
    )
    assert WEBSERVER is not None
    WEBSERVER.serve_forever()


@contextmanager
def run_preview(
    runner: CliRunner,
    args: list[str] | None = None,
    *,
    max_tries: int = 1_000,
    threaded:  bool = False,
) -> Generator[str]:
    # global keyword is required for tests to pass
    global WEBSERVER_THREADED  # noqa: PLW0603
    global WEBSERVER  # noqa: PLW0603
    WEBSERVER = None

    if threaded:
        WEBSERVER_THREADED = True

    # start_webserver is replaced so it can be stopped for the thread to stop
    # since we can't send signals (ctrl+c) to a thread
    # setup_stop_thread_on_signal is replaced because threads can't receive signals
    with (
        patch(
            'htmd.cli.preview.start_webserver',
            side_effect=start_webserver,
        ),
        patch(
            'htmd.cli.preview.setup_stop_thread_on_signal',
            side_effect=lambda _x: None,
        ),
    ):
        thread = threading.Thread(
            target=runner.invoke,
            args=(preview_module.preview, args or []),
            kwargs={'catch_exceptions': False},
            daemon=True,
        )
        thread.start()

        for _ in range(max_tries):  # pragma: no branch
            if WEBSERVER is not None:
                try:
                    requests.head(BASE_URL, timeout=1)
                    break
                except requests.exceptions.ConnectionError:  # pragma: no cover
                    pass
            time.sleep(0.1)

        try:
            yield BASE_URL
        finally:
            if WEBSERVER:  # pragma: no branch
                WEBSERVER.shutdown()
            thread.join(timeout=1.0)
