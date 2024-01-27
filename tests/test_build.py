import os
from pathlib import Path
import re
import shutil

from click.testing import CliRunner
from htmd.cli import build, start

from utils import remove_fields_from_example_post


SUCCESS_REGEX = (
    'All posts are correctly formatted.\n'
    r'Static site was created in [\w\/\\]*build\n'
)


def test_build() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_verify_fails() -> None:
    expected_output = 'Post "example" does not have field title.\n'
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        remove_fields_from_example_post(('title',))
        result = runner.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_js_minify() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)

        with (Path('static') / 'app.js').open('w') as js_file:
            js_file.write('console.log("htmd");')

        result = runner.invoke(build, ['--js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_js_minify_no_js_files() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(build, ['--js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_no_js_minify() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(build, ['--no-js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_css_minify() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(build, ['--css-minify'])
        with (Path('build') / 'index.html').open('r') as built_index:
            contents = built_index.read()
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    assert 'combined.min.css' in contents


def test_build_no_css_minify() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(build, ['--no-css-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_css_minify_no_css_files() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        (Path('static') / 'style.css').unlink()
        (Path('static') / '_reset.css').unlink()
        result = runner.invoke(build, ['--css-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_html_pretty_true() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        with Path('config.toml').open('r') as config_file:
            lines = config_file.readlines()

        with Path('config.toml').open('w') as config_file:
            for line in lines:
                if 'pretty =' in line:
                    config_file.write('pretty = true\n')
                else:
                    config_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_html_minify_true() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        with Path('config.toml').open('r') as config_file:
            lines = config_file.readlines()

        with Path('config.toml').open('w') as config_file:
            for line in lines:
                if 'minify =' in line:
                    config_file.write('minify = true\n')
                else:
                    config_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_page_404() -> None:
    # Linking to a page that doesn't exist
    # will cause a 404 status code
    # and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /dne/\n"
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)

        with (Path('pages') / 'about.html').open('r') as about_file:
            lines = about_file.readlines()

        new_line = '''<p><a href="{{ url_for('pages.page', path='dne') }}">DNE link</a></p>\n'''  # noqa: E501
        with (Path('pages') / 'about.html').open('w') as about_file:
            for line in lines:
                if '<p>This is the about page.</p>' in line:
                    about_file.write(new_line)
                else:
                    about_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_multiple_posts() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        shutil.copyfile(
            Path('posts') / 'example.md',
            Path('posts') / 'sample.md',
        )
        result = runner.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_from_sub_directory() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(start)
        current_directory = Path.cwd()
        os.chdir(Path(current_directory) / 'posts')
        result = runner.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_feed_dot_atom() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(start)
        result = runner.invoke(build)
        assert result.exit_code == 0
        current_directory = Path.cwd()
        assert (Path(current_directory) / 'build' / 'feed.atom').is_file


def test_build_page_without_link() -> None:
    page_lines = (
        "{% extends '_layout.html' %}\n",
        '\n',
        '{% block title %}New{% endblock title %}\n',
        '\n',
        '{% block content %}\n',
        '  <article>\n',
        '    <h1>New</h1>\n',
        '    <p>Totally new</p>\n',
        '  </article>\n',
        '{% endblock content %}\n',
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(start)
        # Create page that is doesn't have a link in the site
        with (Path('pages') / 'new.html').open('w') as page_file:
            for line in page_lines:
                page_file.write(line)
        result = runner.invoke(build)
        assert result.exit_code == 0
        with (Path('build') / 'new' / 'index.html').open('r') as page_file:
            assert 'Totally new' in page_file.read()
