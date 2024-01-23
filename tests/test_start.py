from pathlib import Path

from click.testing import CliRunner
from htmd.cli import start


def test_start() -> None:
    runner = CliRunner()
    expected_output = (
        'templates/ was created.\n'
        'templates/_layout.html was created.\n'
        'static/ was created.\n'
        'static/_reset.css was created.\n'
        'static/style.css was created.\n'
        'pages/ was created.\n'
        'pages/about.html was created.\n'
        'posts/ was created.\n'
        'posts/example.md was created.\n'
        'config.toml was created.\n'
        'Add the site name and edit settings in config.toml\n'
    )
    with runner.isolated_filesystem():
        result = runner.invoke(start)
    assert result.exit_code == 0
    assert result.output == expected_output


def test_start_all_templates() -> None:
    runner = CliRunner()
    expected_output = (
        'templates/ was created.\n'
        'templates/404.html was created.\n'
        'templates/_layout.html was created.\n'
        'templates/_list.html was created.\n'
        'templates/all_posts.html was created.\n'
        'templates/all_tags.html was created.\n'
        'templates/author.html was created.\n'
        'templates/day.html was created.\n'
        'templates/index.html was created.\n'
        'templates/month.html was created.\n'
        'templates/post.html was created.\n'
        'templates/tag.html was created.\n'
        'templates/year.html was created.\n'
        'static/ was created.\n'
        'static/_reset.css was created.\n'
        'static/style.css was created.\n'
        'pages/ was created.\n'
        'pages/about.html was created.\n'
        'posts/ was created.\n'
        'posts/example.md was created.\n'
        'config.toml was created.\n'
        'Add the site name and edit settings in config.toml\n'
    )
    with runner.isolated_filesystem():
        result = runner.invoke(start, ['--all-templates'])
    assert result.exit_code == 0
    assert result.output == expected_output


def test_start_with_existing_template() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('templates').mkdir()
        with (Path('templates') / '_layout.html').open('w') as layout:
            pass
        result = runner.invoke(start)
        with (Path('templates') / '_layout.html').open('r') as layout:
            # _layout.html was not replaced
            assert layout.read() == ''
    assert result.exit_code == 0
    assert 'templates/ already exists and was not created.' in result.output
    expected2 = 'templates/_layout.html already exists and was not created.'
    assert expected2 in result.output
