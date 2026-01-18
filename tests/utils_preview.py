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


@contextmanager
def run_preview(
    runner: CliRunner,
    args: list[str] | None = None,
    *,
    max_tries: int = 1_000,
    threaded:  bool = False,
    webserver_collector: list | None = None,
) -> Generator[str]:
    def create_webserver(app: Flask, host: str, port: int) -> BaseWSGIServer:
        webserver = make_server(
            host,
            port,
            app,
            threaded=threaded,
        )
        assert webserver is not None
        if webserver_collector is not None:
            webserver_collector.append(webserver)
        return webserver

    stop_event = threading.Event()
    with (
        # start_webserver is replaced so it can handle each request in a thread
        patch(
            'htmd.cli.preview.create_webserver',
            side_effect=create_webserver,
        ),
        # create_stop_event is replace so we can stop preview
        # since we can't send signals (ctrl+c) to a thread
        patch(
            'htmd.cli.preview.create_stop_event',
            return_value=stop_event,
        ),
        # setup_stop_thread_on_signal is replaced because threads can't receive signals
        patch(
            'htmd.cli.preview.set_stop_event_on_signal',
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
        try:
            for _ in range(max_tries):  # pragma: no branch
                try:
                    requests.head(BASE_URL, timeout=1)
                    break
                except (
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                ):  # pragma: no cover
                    pass

                time.sleep(0.1)

            yield BASE_URL
        finally:
            # Trigger preview to stop
            stop_event.set()
            # Give time for the watchdog thread inside preview
            # to stop, it won't know to stop right away
            thread.join(timeout=2.0)
