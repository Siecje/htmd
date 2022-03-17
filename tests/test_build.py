import os
import re

from click.testing import CliRunner
from htmd.cli import build, start

from test_verify import remove_field_from_example_post


SUCCESS_REGEX = (
    'All posts are correctly formatted.\n'
    r'Static site was created in [\w\/\\]*build\n'
)

def test_build():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_verify_fails():
    expected_output = (
        'Post "example" does not have field title.\n'
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        remove_field_from_example_post('title')
        result = runner.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_js_minify():
    expected_output = (
        'All posts are correctly formatted.\n'
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)

        with open(os.path.join('static', 'app.js'), 'w') as js_file:
            js_file.write('console.log("htmd");')

        result = runner.invoke(build, ['--js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_js_minify_no_js_files():
    expected_output = (
        'All posts are correctly formatted.\n'
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(build, ['--js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_no_js_minify():
    expected_output = (
        'All posts are correctly formatted.\n'
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(build, ['--no-js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_css_minify():
    expected_output = (
        'All posts are correctly formatted.\n'
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(build, ['--css-minify'])
        with open(os.path.join('build', 'index.html'), 'r') as built_index:
            contents = built_index.read()
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    assert 'combined.min.css' in contents


def test_build_no_css_minify():
    expected_output = (
        'All posts are correctly formatted.\n'
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(build, ['--no-css-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_css_minify_no_css_files():
    expected_output = (
        'All posts are correctly formatted.\n'
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        os.remove(os.path.join("static", "style.css"))
        os.remove(os.path.join("static", "_reset.css"))
        result = runner.invoke(build, ['--css-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
