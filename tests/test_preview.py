from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
from types import TracebackType

from click.testing import CliRunner
from htmd.cli.preview import PostsCreatedHandler, preview, StaticHandler
import pytest
import requests
from watchdog.events import DirCreatedEvent, FileCreatedEvent, FileModifiedEvent

from utils import (
    set_example_contents,
    set_example_to_draft,
    set_example_to_draft_build,
)


BASE_URL = 'http://[::1]:9090'


def invoke_preview(run_start: CliRunner, args: list[str] | None = None) -> None:
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
        max_tries: int = 10_000,
    ) -> None:
        self.args = args
        self.max_tries = max_tries

    def __enter__(self: 'run_preview') -> str:
        cmd = [sys.executable, '-m', 'htmd', 'preview']
        if self.args:
            cmd += self.args

        self.task = subprocess.Popen(cmd)  # noqa: S603

        for _ in range(self.max_tries):  # pragma: no branch
            try:
                requests.head(BASE_URL, timeout=1)
            except requests.exceptions.ConnectionError:
                continue
            else:
                break
        return BASE_URL

    def __exit__(
        self: 'run_preview',
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.task.terminate()
        try:
            self.task.wait(5)
        except subprocess.TimeoutExpired:  # pragma: no cover
            if self.task.poll() is None:
                self.task.kill()


def test_preview(run_start: CliRunner) -> None:  # noqa: ARG001
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get(BASE_URL, timeout=1)
    success = 200
    with run_preview():
        response = requests.get(BASE_URL, timeout=1)
        assert response.status_code == success


def test_preview_css_minify_js_minify(run_start: CliRunner) -> None:
    args = ['--css-minify', '--js-minify']
    invoke_preview(run_start, args)
    urls = (
        (200, '/static/combined.min.css'),
        (200, '/static/combined.min.js'),
    )
    # Create the only JavaScript file
    js_path = Path('static') / 'scripts.js'
    with js_path.open('w') as js_file:
        js_file.write('document.getElementsByTagName("body");')

    combined_js_path = Path('static') / 'combined.min.js'
    assert not combined_js_path.exists()

    # When preview starts combined.min.js should be created
    with run_preview(args) as base_url:
        assert combined_js_path.exists()
        for status, url in urls:
            response = requests.get(base_url + url, timeout=1)
            assert response.status_code == status


def test_preview_no_css_minify(run_start: CliRunner) -> None:
    args = ['--no-css-minify', '--js-minify']
    invoke_preview(run_start, args)
    urls = (
        (404, '/static/combined.min.css'),
        (200, '/static/combined.min.js'),
    )
    js_path = Path('static') / 'scripts.js'
    with js_path.open('w') as js_file:
        js_file.write('document.getElementsByTagName("body");')

    with run_preview(args) as base_url:
        for status, url in urls:
            response = requests.get(base_url + url, timeout=1)
            assert response.status_code == status


def test_preview_css_minify_no_js_minify(run_start: CliRunner) -> None:
    args = ['--css-minify', '--no-js-minify']
    invoke_preview(run_start, args)
    urls = (
        (200, '/static/combined.min.css'),
        (404, '/static/combined.min.js'),
    )
    with run_preview(args) as base_url:
        for status, url in urls:
            response = requests.get(base_url + url, timeout=1)
            assert response.status_code == status


def test_preview_no_css_minify_no_js_minify(run_start: CliRunner) -> None:
    args = ['--no-css-minify', '--no-js-minify']
    invoke_preview(run_start, args)
    urls = (
        (404, '/static/combined.min.css'),
        (404, '/static/combined.min.js'),
    )
    with run_preview(args) as base_url:
        for status, url in urls:
            response = requests.get(base_url + url, timeout=1)
            assert response.status_code == status


@pytest.mark.parametrize('static_dir', [
    'static',
    'foo',
])
def test_preview_css_changes(run_start: CliRunner, static_dir: str) -> None:  # noqa: ARG001
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

    url = '/static/combined.min.css'
    new_style = 'p {color: red;}'
    expected = new_style.replace(' ', '').replace(';', '')
    with run_preview() as base_url:
        response = requests.get(base_url + url, timeout=1)
        before = response.text
        assert expected not in before

        css_path = Path(static_dir) / 'style.css'
        # When static_dir != 'static' this will be a new file
        if static_dir != 'static':
            assert css_path.exists() is False

        with css_path.open('a') as css_file:
            css_file.write('\n' + expected + '\n')

        # Ensure new style is served
        read_timeout = False
        after = before
        max_attempts = 50_000
        attempts = 1

        # CSS changes can be seen without stopping webserver
        # Require two responses to be the same because
        # response was missing the last few characters
        # AssertionError: assert 'p{color:red}' in '\np{color:red'
        previous_response = None
        consecutive_same_responses = 0
        same_response_goal = 2
        while (
            (before == after or consecutive_same_responses < same_response_goal)
            and attempts < max_attempts
        ):
            try:
                response = requests.get(base_url + url, timeout=1)
            except (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
            ):  # pragma: no cover
                # Can happen when file is being replaced
                # Verify webserver didn't restart
                try:
                    response = requests.get(base_url, timeout=1)
                except (
                    requests.exceptions.ChunkedEncodingError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.ReadTimeout,
                ):  # pragma: no cover
                    read_timeout = True  # pragma: no cover
            else:
                after = response.text

                if previous_response == after:
                    consecutive_same_responses += 1
                else:
                    consecutive_same_responses = 0
                previous_response = after
            attempts += 1

    assert read_timeout is False, 'Preview did reload.'
    assert before != after
    assert expected in after


@pytest.mark.parametrize('static_dir', [
    'static',
    'foo',
])
def test_preview_js_changes(run_start: CliRunner, static_dir: str) -> None:  # noqa: ARG001
    js_path = Path(static_dir) / 'script.js'
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

        # Create file to test modified files update
        with js_path.open('w') as js_file:
            js_file.write('document.getElementByTagName("div")')

    url = '/static/combined.min.js'
    expected = 'document.getElementByTagName("body")'

    with run_preview() as base_url:
        response = requests.get(base_url + url, timeout=1)
        before = response.text
        assert expected not in before

        if static_dir != 'static':
            assert js_path.exists()

        with js_path.open('w') as js_file:
            js_file.write(expected)

        # Ensure new script is served
        read_timeout = False
        after = before
        max_attempts = 50_000
        attempts = 1

        # JS changes can be seen without stopping webserver
        # Require two responses to be the same because
        # response was missing the last few characters
        # after == 'document.getElementByTagName("body"' # noqa: ERA001
        previous_response = None
        consecutive_same_responses = 0
        same_response_goal = 2
        while (
            (before == after or consecutive_same_responses < same_response_goal)
            and attempts < max_attempts
        ):
            try:
                response = requests.get(base_url + url, timeout=1)
            except (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
            ):  # pragma: no cover
                # Can happen when file is being replaced
                # Verify webserver didn't restart
                try:
                    response = requests.get(base_url, timeout=1)
                except (
                    requests.exceptions.ChunkedEncodingError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.ReadTimeout,
                ):  # pragma: no cover
                    read_timeout = True  # pragma: no cover
            else:
                after = response.text

                if previous_response == after:
                    consecutive_same_responses += 1
                else:
                    consecutive_same_responses = 0
                previous_response = after

            attempts += 1

    assert read_timeout is False, 'Preview did reload.'
    assert before != after
    assert expected in after


@pytest.mark.parametrize('posts_dir', [
    'posts',
    'bar',
])
def test_preview_when_posts_change(run_start: CliRunner, posts_dir: str) -> None:  # noqa: ARG001
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

    title = 'Test Title'
    expected = 'This is the content.'
    with run_preview() as base_url:
        response = requests.get(base_url, timeout=1)
        before = response.text
        assert expected not in before
        assert title not in before

        # file will be new when posts_dir != 'posts'
        post_path = Path(posts_dir) / 'example.md'
        with post_path.open('w') as post_file:
            post_file.write('---\n')
            post_file.write(f'title: {title}\n')
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
                response = requests.get(base_url, timeout=1)
            except (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
            ):  # pragma: no cover
                # happens during restart
                read_timeout = True
            else:
                after = response.text

            attempts += 1

        assert read_timeout is False, 'Preview did reload.'
        assert before != after
        assert expected in after
        assert title in after


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
        # Move example page into new pages folder
        shutil.copy(Path('pages') / 'about.html', Path(pages_dir))

    url = '/about/'
    expected = 'This is new.'
    page_path = Path(pages_dir) / 'about.html'
    with page_path.open('r') as page_file:
        contents = page_file.read()

    contents = contents.replace(
        '</p>',
        f' {expected}</p>',
    )
    with run_preview() as base_url:
        response = requests.get(base_url + url, timeout=1)
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
                response = requests.get(base_url + url, timeout=1)
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


def test_preview_shows_new_pages(run_start: CliRunner) -> None:  # noqa: ARG001
    page_path = Path('pages') / 'about.html'
    with page_path.open('r') as page_file:
        contents = page_file.read()

    new_path_path = Path('pages') / 'new.html'
    expected = 'This is new.'
    contents = contents.replace(
        '</p>',
        f' {expected}</p>',
    )
    url = '/new/'
    with run_preview() as base_url:
        response = requests.get(base_url + url, timeout=1)
        before = response.text
        assert response.status_code == 404  # noqa: PLR2004
        assert expected not in before

        with new_path_path.open('w') as page_file:
            page_file.write(contents)

        # Ensure new sentence is available after change
        read_timeout = False
        after = before
        max_attempts = 50_000
        attempts = 1

        # Since HTML changes can be seen without reloading
        while before == after and attempts < max_attempts:
            try:
                response = requests.get(base_url + url, timeout=1)
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
    with run_preview() as base_url:
        for status, url in urls:
            response = requests.get(base_url + url, timeout=1)
            assert response.status_code == status

        for url in not_in:
            response = requests.get(base_url + url, timeout=1)
            assert response.status_code == success
            assert 'Example Post' not in response.text

    # drafts should appear
    with run_preview(args) as base_url:
        for _status, url in urls:
            response = requests.get(base_url + url, timeout=1)
            assert response.status_code == success

        for url in not_in:
            response = requests.get(base_url + url, timeout=1)
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
    with run_preview() as base_url:
        for status, url in urls:
            response = requests.get(base_url + url, timeout=1)
            assert response.status_code == status

        for url in not_in:
            response = requests.get(base_url + url, timeout=1)
            assert response.status_code == success
            assert 'Example Post' not in response.text


def test_preview_when_static_folder_does_not_exist(run_start: CliRunner) -> None:
    static_path = Path('static')
    for file_in_dir in static_path.iterdir():
        file_in_dir.unlink()

    static_path.rmdir()

    assert static_path.exists() is False

    # invoke_preview is only used for test coverage
    invoke_preview(run_start)

    success = 200
    with run_preview() as base_url:
        assert static_path.exists() is False
        response = requests.get(base_url, timeout=1)
        assert response.status_code == success


def test_preview_when_combined_js_exists(run_start: CliRunner) -> None:
    combined_path = Path('static') / 'combined.min.js'

    with combined_path.open('w') as combined_js_file:
        combined_js_file.write('document.getElementByTagName("body");')

    new_path = Path('static') / 'new.js'
    new_js = 'console.log("new");'
    with new_path.open('w') as new_js_file:
        new_js_file.write(new_js)

    # invoke_preview is only used for test coverage
    invoke_preview(run_start)

    url = '/static/combined.min.js'
    success = 200
    with run_preview() as base_url:
        response = requests.get(base_url + url, timeout=1)
        assert response.status_code == success
        assert new_js in response.text

    # invoke again will exit combine_and_minify_js() early
    # since there is no change
    # invoke_preview is only used for test coverage
    invoke_preview(run_start)

    url = '/static/combined.min.js'
    success = 200
    with run_preview() as base_url:
        response = requests.get(base_url + url, timeout=1)
        assert response.status_code == success
        assert new_js in response.text


def test_static_handler(run_start: CliRunner) -> None:  # noqa: ARG001
    event = threading.Event()
    static_handler = StaticHandler(Path('static'), event)

    # Add new file to combined.min.css
    new_css = 'body { background-color: aqua;}'
    new_css_path = Path('static') / 'new.css'
    with new_css_path.open('w') as new_css_file:
        new_css_file.write(new_css)

    css_file_event = FileModifiedEvent(bytes(new_css_path), '', is_synthetic=True)
    static_handler.on_modified(css_file_event)
    assert event.is_set()
    event.clear()

    new_js = 'document.getElementByTag("body")'
    new_js_path = Path('static') / 'new.js'
    with new_js_path.open('w') as new_js_file:
        new_js_file.write(new_js)
    js_file_event = FileModifiedEvent(str(new_js_path), '', is_synthetic=True)
    static_handler.on_modified(js_file_event)
    assert event.is_set()
    event.clear()
    # Verify exit early when .js file event but no changes
    static_handler.on_modified(js_file_event)
    assert not event.is_set()


def test_posts_handler(run_start: CliRunner) -> None:  # noqa: ARG001
    event = threading.Event()
    posts_handler = PostsCreatedHandler(event)

    # Add non .md file
    non_md_path = Path('posts') / 'not_markdown.txt'
    with non_md_path.open('w') as non_md_file:
        non_md_file.write('This is not markdown.')

    new_file_event = FileCreatedEvent(bytes(non_md_path), '', is_synthetic=True)
    posts_handler.on_created(new_file_event)
    assert not event.is_set()

    posts_path = Path('posts')
    new_dir_event = DirCreatedEvent(bytes(posts_path), '', is_synthetic=True)
    posts_handler.on_created(new_dir_event)
    assert not event.is_set()


def test_favicon(run_start: CliRunner) -> None:  # noqa: ARG001
    url = '/static/favicon.svg'
    success = 200
    with run_preview() as base_url:
        response = requests.get(base_url + url, timeout=1)
    assert response.status_code == success
    assert response.headers['Content-Type'] == 'image/svg+xml; charset=utf-8'
    assert len(response.content) > 0
    with (Path('static') / 'favicon.svg').open('rb') as favicon_file:
        svg_content = favicon_file.read()
    assert response.content == svg_content


def test_sse(run_start: CliRunner) -> None:  # noqa: ARG001
    layout_path = Path('templates') / '_layout.html'
    with layout_path.open('r') as layout_file:
        contents = layout_file.read()

    expected_js = 'sse.onmessage'
    assert expected_js in contents

    def in_thread(
        start_event: threading.Event,
        end_event: threading.Event,
        url: str,
        changes: list[str],
    ) -> None:
        start_event.set()
        with requests.get(
            url,
            stream=True,
            timeout=30,
        ) as response:
            for line in response.iter_lines():  # pragma: no branch
                if line:
                    data = line.decode('utf-8')
                    changes.append(data)
                    start_event.clear()
                    if len(changes) >= 2:  # noqa: PLR2004
                        break

        end_event.set()

    changes: list[str] = []
    started = threading.Event()
    ended = threading.Event()
    with run_preview() as base_url:
        response = requests.get(base_url, timeout=1)
        assert expected_js in response.text

        thread = threading.Thread(
            target=in_thread,
            args=(started, ended, base_url + '/changes', changes),
        )
        thread.start()

        started.wait(timeout=10)

        # Trigger two events
        set_example_contents('Different1.')
        start_time = int(time.time())
        wait_s = 10
        while started.is_set() and (int(time.time()) - start_time) < wait_s:
            time.sleep(0.1)

        set_example_contents('Different2.')
        ended.wait(timeout=10)
    assert changes == ['data: refresh', 'data: refresh']
