from pathlib import Path
import time
from types import TracebackType

from click.testing import CliRunner
from htmd.cli import preview
import pytest
import requests
import subprocess
import sys


def invoke_preview(run_start: CliRunner, args: list[str]) -> None:
    """
    run_start.invoke(preview) fails but it is used to track test coverage.

    I get a message that the path I pass to pytest is not found.
    I've track it down to this subprocess call.
    https://github.com/pallets/werkzeug/blob/d3dd65a27388fbd39d146caacf2563639ba622f0/src/werkzeug/_reloader.py#L273
    str(args) is "['/path/to/venv/bin/python', '-m', 'pytest', 'tests']"
    ERROR: file or directory not found: tests
    Which is how I'm running my tests.
    If I pass tests/test_preview.py then I see
    ERROR: file or directory not found: tests/test_preview.py
    """
    run_start.invoke(preview, args)


class run_preview:  # noqa: N801
    def __init__(
        self: 'run_preview',
        args: list[str] | None = None,
        max_tries: int = 10,
    ) -> None:
        self.args = args
        self.max_tries = max_tries

    def __enter__(self: 'run_preview') -> None:
        cmd = [sys.executable, '-m', 'htmd', 'preview']
        if self.args:
            cmd += self.args
        self.task = subprocess.Popen(cmd)  # noqa: S603
        url = 'http://localhost:9090/'
        count = 0
        while count < self.max_tries:  # pragma: no branch
            try:
                requests.get(url, timeout=1)
            except requests.exceptions.ConnectionError:
                count += 1
                time.sleep(0.1)
            else:
                break

    def __exit__(
        self: 'run_preview',
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.task.terminate()


def test_preview(run_start: CliRunner) -> None:  # noqa: ARG001
    url = 'http://localhost:9090/'
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get(url, timeout=1)
    success = 200
    with run_preview():
        response = requests.get(url, timeout=0.01)
        assert response.status_code == success


def test_preview_css_minify_js_minify(run_start: CliRunner) -> None:
    args = ['--css-minify', '--js-minify']
    invoke_preview(run_start, args)
    urls = (
        (200, 'http://localhost:9090/static/combined.min.css'),
        (200, 'http://localhost:9090/static/combined.min.js'),
    )
    js_path = Path('static') / 'scripts.js'
    with js_path.open('w') as js_file:
        js_file.write('document.getElementsByTagName("body");')

    with run_preview(args):
        for status, url in urls:
            response = requests.get(url, timeout=0.01)
            assert response.status_code == status


def test_preview_no_css_minify(run_start: CliRunner) -> None:
    args = ['--no-css-minify', '--js-minify']
    invoke_preview(run_start, args)
    urls = (
        (404, 'http://localhost:9090/static/combined.min.css'),
        (200, 'http://localhost:9090/static/combined.min.js'),
    )
    js_path = Path('static') / 'scripts.js'
    with js_path.open('w') as js_file:
        js_file.write('document.getElementsByTagName("body");')

    with run_preview(args):
        for status, url in urls:
            response = requests.get(url, timeout=0.01)
            assert response.status_code == status


def test_preview_css_minify_no_js_minify(run_start: CliRunner) -> None:
    args = ['--css-minify', '--no-js-minify']
    invoke_preview(run_start, args)
    urls = (
        (200, 'http://localhost:9090/static/combined.min.css'),
        (404, 'http://localhost:9090/static/combined.min.js'),
    )
    with run_preview(args):
        for status, url in urls:
            response = requests.get(url, timeout=0.01)
            assert response.status_code == status


def test_preview_no_css_minify_no_js_minify(run_start: CliRunner) -> None:
    args = ['--no-css-minify', '--no-js-minify']
    invoke_preview(run_start, args)
    urls = (
        (404, 'http://localhost:9090/static/combined.min.css'),
        (404, 'http://localhost:9090/static/combined.min.js'),
    )
    with run_preview(args):
        for status, url in urls:
            response = requests.get(url, timeout=0.01)
            assert response.status_code == status
