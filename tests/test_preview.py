from click.testing import CliRunner
from htmd.cli import preview


def test_preview(run_start: CliRunner) -> None:
    result = run_start.invoke(preview)
    # Why is this 5?
    expected_exit_code = 5
    assert result.exit_code == expected_exit_code


def test_preview_css_minify_js_minify(run_start: CliRunner) -> None:
    run_start.invoke(preview, ['--css-minify', '--js-minify'])


def test_preview_no_css_minify(run_start: CliRunner) -> None:
    run_start.invoke(preview, ['--no-css-minify', '--js-minify'])


def test_preview_css_minify_no_js_minify(run_start: CliRunner) -> None:
    run_start.invoke(preview, ['--css-minify', '--no-js-minify'])


def test_preview_no_css_minify_no_js_minify(run_start: CliRunner) -> None:
    run_start.invoke(preview, ['--no-css-minify', '--no-js-minify'])
