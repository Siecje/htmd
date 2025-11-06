from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import TracebackType

from click.testing import CliRunner
from htmd.cli import preview
import pytest
import requests

from utils import set_example_to_draft, set_example_to_draft_build


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
            response = requests.get(url, timeout=0.1)
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
            response = requests.get(url, timeout=0.1)
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
            response = requests.get(url, timeout=0.1)
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
            response = requests.get(url, timeout=0.1)
            assert response.status_code == status


@pytest.mark.parametrize('static_dir', [
    'static',
    'foo',
])
def test_preview_reload_css(run_start: CliRunner, static_dir: str) -> None:  # noqa: ARG001
    if static_dir != 'static':
        # Change static directory in config.toml
        config_path = Path('config.toml')
        with config_path.open('r') as config_file:
            lines = config_file.readlines()

        with config_path.open('w') as config_file:
            for line in lines:
                if 'static = ' in line:
                    config_file.write(f'static = "{static_dir}"\n')
                else:
                    config_file.write(line)

        # Ensure directory exists
        Path(static_dir).mkdir(exist_ok=True)

        css_path = Path(static_dir) / 'style.css'
        with css_path.open('w') as css_file:
            css_file.write('')

    url = 'http://localhost:9090/static/combined.min.css'
    new_style = 'p {color: red;}'
    expected = new_style.replace(' ', '').replace(';', '')
    with run_preview():
        response = requests.get(url, timeout=0.01)
        before = response.text
        assert expected not in before

        css_path = Path(static_dir) / 'style.css'
        with css_path.open('a') as css_file:
            css_file.write('\n' + new_style + '\n')

        # Ensure new style is available after reload
        read_timeout = False
        after = before
        max_attempts = 50_000
        attempts = 1
        while after == before and attempts < max_attempts:
            try:
                response = requests.get(url, timeout=0.1)
            except (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
            ):
                # happens during restart
                read_timeout = True
            else:
                after = response.text

            attempts += 1

        assert read_timeout, 'Preview did not reload.'
        assert before != after
        assert expected in after


@pytest.mark.parametrize('static_dir', [
    'static',
    'foo',
])
def test_preview_reload_js(run_start: CliRunner, static_dir: str) -> None:  # noqa: ARG001
    # Change static directory in config.toml
    config_path = Path('config.toml')
    with config_path.open('r') as config_file:
        lines = config_file.readlines()

    with config_path.open('w') as config_file:
        for line in lines:
            if 'static = ' in line:
                config_file.write(f'static = "{static_dir}"\n')
            else:
                config_file.write(line)

    # Ensure directory exists
    Path(static_dir).mkdir(exist_ok=True)

    url = 'http://localhost:9090/static/combined.min.js'
    new_js = 'document.getElementByTagName("body");'
    expected = new_js
    # Need to create before running preview since no .js files exist
    js_path = Path(static_dir) / 'script.js'
    with js_path.open('w') as js_file:
        js_file.write('document.getElementByTagName("div");')

    with run_preview():
        response = requests.get(url, timeout=0.01)
        before = response.text
        assert expected not in before

        with js_path.open('w') as js_file:
            js_file.write('\n' + new_js + '\n')

        # Ensure new script is available after reload
        read_timeout = False
        after = before
        max_attempts = 50_000
        attempts = 1
        while after == before and attempts < max_attempts:
            try:
                response = requests.get(url, timeout=0.1)
            except (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
            ):
                # happens during restart
                read_timeout = True
            else:
                after = response.text

            attempts += 1

        assert read_timeout, 'Preview did not reload.'
        assert before != after
        assert expected in after


@pytest.mark.parametrize('posts_dir', [
    'posts',
    'bar',
])
def test_preview_reload_when_posts_change(run_start: CliRunner, posts_dir: str) -> None:  # noqa: ARG001
    if posts_dir != 'posts':
        # Change static directory in config.toml
        config_path = Path('config.toml')
        with config_path.open('r') as config_file:
            lines = config_file.readlines()

        with config_path.open('w') as config_file:
            for line in lines:
                if 'posts = ' in line:
                    config_file.write(f'posts = "{posts_dir}"\n')
                else:
                    config_file.write(line)

        # Ensure directory exists
        Path(posts_dir).mkdir(exist_ok=True)
        # Move example post into new posts folder
        shutil.copy(Path('posts') / 'example.md', Path(posts_dir))

    url = 'http://localhost:9090/'
    expected = 'This is a new post.'
    with run_preview():
        response = requests.get(url, timeout=0.01)
        before = response.text
        assert expected not in before

        post_path = Path(posts_dir) / 'example.md'
        with post_path.open('w') as post_file:
            post_file.write('---\n')
            post_file.write('title: New\n')
            post_file.write('published: 2025-11-05\n')
            post_file.write('...\n')
            post_file.write(f'{expected}\n')

        # Ensure new sentence is available after reload
        read_timeout = False
        after = before
        max_attempts = 50_000
        attempts = 1
        while after == before and attempts < max_attempts:
            try:
                response = requests.get(url, timeout=0.1)
            except (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
            ):
                # happens during restart
                read_timeout = True
            else:
                after = response.text

            attempts += 1

        assert read_timeout, 'Preview did not reload.'
        assert before != after
        assert expected in after


@pytest.mark.parametrize('pages_dir', [
    'pages',
    'bar',
])
def test_preview_shows_pages_change_without_reload(
    run_start: CliRunner,  # noqa: ARG001
    pages_dir: str,
) -> None:
    if pages_dir != 'pages':
        # Change static directory in config.toml
        config_path = Path('config.toml')
        with config_path.open('r') as config_file:
            lines = config_file.readlines()

        with config_path.open('w') as config_file:
            for line in lines:
                if 'pages = ' in line:
                    config_file.write(f'pages = "{pages_dir}"\n')
                else:
                    config_file.write(line)

        # Ensure directory exists
        Path(pages_dir).mkdir(exist_ok=True)
        # Move example post into new posts folder
        shutil.copy(Path('pages') / 'about.html', Path(pages_dir))

    url = 'http://localhost:9090/about/'
    expected = 'This is new.'
    page_path = Path(pages_dir) / 'about.html'
    with page_path.open('r') as page_file:
        contents = page_file.read()

    contents = contents.replace(
        '</p>',
        f' {expected}</p>',
    )
    with run_preview():
        response = requests.get(url, timeout=0.01)
        before = response.text
        assert expected not in before

        with page_path.open('w') as page_file:
            page_file.write(contents)

        # Ensure new sentence is available after change
        read_timeout = False
        after = before
        max_attempts = 50_000
        attempts = 1

        # Since HTML changes can be seen without reloading
        while before == after and attempts < max_attempts:
            try:
                response = requests.get(url, timeout=0.1)
            except (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
            ):  # pragma: no cover
                # happens during restart
                read_timeout = True  # pragma: no cover
            else:
                after = response.text

            attempts += 1

        assert read_timeout is False, 'Preview did reload.'
        assert before != after
        assert expected in after


def test_preview_drafts(run_start: CliRunner) -> None:
    args = ['--drafts']
    invoke_preview(run_start, args)
    set_example_to_draft()
    success = 200

    urls = (
        (404, '/2014/'),
        (404, '/2014/10/'),
        (404, '/2014/10/30/'),
        (404, '/2014/10/30/example/'),
        (404, '/tags/first/'),
        (404, '/author/Taylor/'),
    )
    not_in = (
        '/',
        '/all/',
    )
    # drafts should not appear
    with run_preview():
        for status, url in urls:
            response = requests.get('http://localhost:9090' + url, timeout=1)
            assert response.status_code == status

        for url in not_in:
            response = requests.get('http://localhost:9090' + url, timeout=0.01)
            assert response.status_code == success
            assert 'Example Post' not in response.text

    # drafts should appear
    with run_preview(args):
        for _status, url in urls:
            response = requests.get('http://localhost:9090' + url, timeout=1)
            assert response.status_code == success

        for url in not_in:
            response = requests.get('http://localhost:9090' + url, timeout=0.01)
            assert response.status_code == success
            assert 'Example Post' in response.text

    set_example_to_draft_build()
    urls = (
        (404, '/2014/'),
        (404, '/2014/10/'),
        (404, '/2014/10/30/'),
        (200, '/2014/10/30/example/'),
        (200, '/tags/first/'),
        (200, '/author/Taylor/'),
    )
    not_in = (
        '/',
        '/all/',
    )
    with run_preview():
        for status, url in urls:
            response = requests.get('http://localhost:9090' + url, timeout=1)
            assert response.status_code == status

        for url in not_in:
            response = requests.get('http://localhost:9090' + url, timeout=0.01)
            assert response.status_code == success
            assert 'Example Post' not in response.text


def test_preview_when_static_folder_does_not_exist(run_start: CliRunner) -> None:  # noqa: ARG001
    static_path = Path('static')
    for file_in_dir in static_path.iterdir():
        file_in_dir.unlink()

    static_path.rmdir()

    assert static_path.exists() is False

    url = 'http://localhost:9090/'
    success = 200
    with run_preview():
        response = requests.get(url, timeout=0.01)
        assert static_path.exists() is False
        assert response.status_code == success
