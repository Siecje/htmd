from pathlib import Path

from click.testing import CliRunner
from htmd.cli.start import start


def test_start() -> None:
    runner = CliRunner()
    expected_output = (
        'templates/ was created.\n'
        'templates/_layout.html was created.\n'
        'static/ was created.\n'
        'static/_reset.css was created.\n'
        'static/style.css was created.\n'
        'static/favicon.svg was created.\n'
        'pages/ was created.\n'
        'pages/about.html was created.\n'
        'posts/ was created.\n'
        'posts/example.md was created.\n'
        'posts/password-protect/ was created.\n'
        'config.toml was created.\n'
        'Add the site name and edit settings in config.toml\n'
    )
    with runner.isolated_filesystem():
        result = runner.invoke(start)

        expected_files = (
            'config.toml',
            'pages/about.html',
            'posts/example.md',
            'static/_reset.css',
            'static/style.css',
            'static/favicon.svg',
            'templates/_layout.html',
        )
        expected_dirs = (
            'pages',
            'posts',
            'static',
            'templates',
        )

        for file in expected_files:
            file_path = Path(file)
            assert file_path.exists()
            assert file_path.is_file()

        for folder in expected_dirs:
            dir_path = Path(folder)
            assert dir_path.exists()

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
        'static/favicon.svg was created.\n'
        'pages/ was created.\n'
        'pages/about.html was created.\n'
        'posts/ was created.\n'
        'posts/example.md was created.\n'
        'posts/password-protect/ was created.\n'
        'config.toml was created.\n'
        'Add the site name and edit settings in config.toml\n'
    )
    with runner.isolated_filesystem():
        result = runner.invoke(start, ['--all-templates'])
        expected_files = (
            'config.toml',
            'pages/about.html',
            'posts/example.md',
            'static/_reset.css',
            'static/style.css',
            'static/favicon.svg',
            'templates/404.html',
            'templates/_layout.html',
            'templates/_list.html',
            'templates/all_posts.html',
            'templates/all_tags.html',
            'templates/author.html',
            'templates/day.html',
            'templates/index.html',
            'templates/month.html',
            'templates/post.html',
            'templates/tag.html',
            'templates/year.html',
        )
        expected_dirs = (
            'pages',
            'posts',
            'static',
            'templates',
        )
        for file in expected_files:
            file_path = Path(file)
            assert file_path.exists()
            assert file_path.is_file()

        for folder in expected_dirs:
            dir_path = Path(folder)
            assert dir_path.exists()

    assert result.exit_code == 0
    assert result.output == expected_output


def test_start_with_existing_template() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path('templates').mkdir()
        layout_path = Path('templates') / '_layout.html'
        with layout_path.open('w') as layout:
            pass
        result = runner.invoke(start)
        with layout_path.open('r') as layout:
            # _layout.html was not replaced
            assert layout.read() == ''
    assert result.exit_code == 0
    assert 'templates/ already exists and was not created.' in result.output
    expected2 = 'templates/_layout.html already exists and was not created.'
    assert expected2 in result.output
