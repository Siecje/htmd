import os
from pathlib import Path
import re
import shutil

from click.testing import CliRunner
from htmd.cli import build

from utils import remove_fields_from_post, SUCCESS_REGEX


def test_build(run_start: CliRunner) -> None:
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_verify_fails(run_start: CliRunner) -> None:
    expected_output = 'Post "example" does not have field title.\n'
    remove_fields_from_post('example', ('title',))
    result = run_start.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_js_minify(run_start: CliRunner) -> None:
    with (Path('static') / 'app.js').open('w') as js_file:
        js_file.write('console.log("htmd");')

    result = run_start.invoke(build, ['--js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_js_minify_no_js_files(run_start: CliRunner) -> None:
    result = run_start.invoke(build, ['--js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_no_js_minify(run_start: CliRunner) -> None:
    result = run_start.invoke(build, ['--no-js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_css_minify(run_start: CliRunner) -> None:
    result = run_start.invoke(build, ['--css-minify'])
    with (Path('build') / 'index.html').open('r') as built_index:
        contents = built_index.read()
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    assert 'combined.min.css' in contents


def test_build_no_css_minify(run_start: CliRunner) -> None:
    result = run_start.invoke(build, ['--no-css-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_css_minify_no_css_files(run_start: CliRunner) -> None:
    (Path('static') / 'style.css').unlink()
    (Path('static') / '_reset.css').unlink()
    result = run_start.invoke(build, ['--css-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_no_css_minify_no_js_minify(run_start: CliRunner) -> None:
    result = run_start.invoke(build, ['--no-css-minify', '--no-js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_html_pretty_true(run_start: CliRunner) -> None:
    config_path = Path('config.toml')
    with config_path.open('r') as config_file:
        lines = config_file.readlines()

    with config_path.open('w') as config_file:
        for line in lines:
            if 'pretty =' in line:
                config_file.write('pretty = true\n')
            else:
                config_file.write(line)

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_html_minify_true(run_start: CliRunner) -> None:
    config_path = Path('config.toml')
    with config_path.open('r') as config_file:
        lines = config_file.readlines()

    with config_path.open('w') as config_file:
        for line in lines:
            if 'minify =' in line:
                config_file.write('minify = true\n')
            else:
                config_file.write(line)

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_page_404(run_start: CliRunner) -> None:
    # Linking to a page that doesn't exist
    # will cause a 404 status code
    # and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /dne/\n"
    )
    about_path = Path('pages') / 'about.html'
    with about_path.open('r') as about_file:
        lines = about_file.readlines()

    new_line = '''<p><a href="{{ url_for('pages.page', path='dne') }}">DNE link</a></p>\n'''  # noqa: E501
    with about_path.open('w') as about_file:
        for line in lines:
            if '<p>This is the about page.</p>' in line:
                about_file.write(new_line)
            else:
                about_file.write(line)

    result = run_start.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_multiple_posts(run_start: CliRunner) -> None:
    shutil.copyfile(
        Path('posts') / 'example.md',
        Path('posts') / 'sample.md',
    )
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_from_sub_directory(run_start: CliRunner) -> None:
    current_directory = Path.cwd()
    os.chdir(Path(current_directory) / 'posts')
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_feed_dot_atom(run_start: CliRunner) -> None:
    result = run_start.invoke(build)
    assert result.exit_code == 0
    current_directory = Path.cwd()
    assert (Path(current_directory) / 'build' / 'feed.atom').is_file()


def test_build_page_without_link(run_start: CliRunner) -> None:
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
    # Create page that is doesn't have a link in the site
    with (Path('pages') / 'new.html').open('w') as page_file:
        for line in page_lines:
            page_file.write(line)
    result = run_start.invoke(build)
    assert result.exit_code == 0
    with (Path('build') / 'new' / 'index.html').open('r') as page_file:
        assert 'Totally new' in page_file.read()


def test_build_empty_directory() -> None:
    expected = 'Can not find config.toml\n'
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(build)
        assert result.exit_code == 1
        assert result.output == expected


def test_build_without_static(run_start: CliRunner) -> None:
    path = Path('static')
    shutil.rmtree(path)
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_without_posts(run_start: CliRunner) -> None:
    path = Path('posts')
    shutil.rmtree(path)
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_without_pages(run_start: CliRunner) -> None:
    path = Path('pages')
    shutil.rmtree(path)

    result = run_start.invoke(build)
    assert result.exit_code == 1
    assert "Unexpected status '404 NOT FOUND' on URL /about/" in result.output

    # Remove link from _layout.html
    layout_path = Path('templates') / '_layout.html'
    with layout_path.open('r') as layout_file:
        lines = layout_file.readlines()
    with layout_path.open('w') as layout_file:
        for line in lines:
            if 'about' in line:
                continue
            layout_file.write(line)

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_without_templates(run_start: CliRunner) -> None:
    path = Path('templates')
    shutil.rmtree(path)
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
