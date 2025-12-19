from pathlib import Path

from click.testing import CliRunner
from htmd.cli.verify import verify

from utils import remove_fields_from_post


def test_verify(run_start: CliRunner) -> None:
    result = run_start.invoke(verify)
    assert result.exit_code == 0
    expected_output = 'All posts are correctly formatted.\n'
    assert result.output == expected_output


def test_verify_author_missing(run_start: CliRunner) -> None:
    # Remove author from example post
    remove_fields_from_post('example', ('author',))

    result = run_start.invoke(verify)
    assert result.exit_code == 1
    expected_output = 'Post "example" does not have field author.\n'
    assert result.stderr == expected_output


def test_verify_title_missing(run_start: CliRunner) -> None:
    # Remove title from example post
    remove_fields_from_post('example', ('title',))

    result = run_start.invoke(verify)
    assert result.exit_code == 1
    expected_output = 'Post "example" does not have field title.\n'
    assert result.stderr == expected_output


def test_verify_published_missing(run_start: CliRunner) -> None:
    # Remove published from example post
    remove_fields_from_post('example', ('published',))

    result = run_start.invoke(verify)
    # verify doesn't check for published
    # since it will be added on build.
    expected_output = 'All posts are correctly formatted.\n'
    assert result.output == expected_output
    assert result.exit_code == 0


def test_verify_published_invalid_year(run_start: CliRunner) -> None:
    example_post_path = Path('posts') / 'example.md'
    with example_post_path.open('r') as post:
        lines = post.readlines()
    with example_post_path.open('w') as post:
        for line in lines:
            if 'published' in line:
                post.write('published: 14-10-30\n')
            else:
                post.write(line)

    result = run_start.invoke(verify)
    assert result.exit_code == 1
    expected_output = (
        'Published date 14-10-30 for example'
        ' is not in the format YYYY-MM-DD.\n'
    )
    assert result.output == expected_output


def test_verify_published_invalid_month(run_start: CliRunner) -> None:
    example_post_path = Path('posts') / 'example.md'
    with example_post_path.open('r') as post:
        lines = post.readlines()
    with example_post_path.open('w') as post:
        for line in lines:
            if 'published' in line:
                post.write('published: 2014-1-30\n')
            else:
                post.write(line)

    result = run_start.invoke(verify)
    assert result.exit_code == 1
    expected_output = (
        'Published date 2014-1-30 for example'
        ' is not in the format YYYY-MM-DD.\n'
    )
    assert result.output == expected_output


def test_verify_published_invalid_day(run_start: CliRunner) -> None:
    example_post_path = Path('posts') / 'example.md'
    with example_post_path.open('r') as post:
        lines = post.readlines()
    with example_post_path.open('w') as post:
        for line in lines:
            if 'published' in line:
                post.write('published: 2014-01-3\n')
            else:
                post.write(line)

    result = run_start.invoke(verify)
    assert result.exit_code == 1
    expected_output = (
        'Published date 2014-01-3 for example'
        ' is not in the format YYYY-MM-DD.\n'
    )
    assert result.output == expected_output


def test_verify_site_name_empty(run_start: CliRunner) -> None:
    expected_output = (
        'All posts are correctly formatted.\n'
        '[site] name is not set in config.toml.\n'
    )

    config_path = Path('config.toml')
    with config_path.open('r') as post:
        lines = post.readlines()
    with config_path.open('w') as post:
        seen = False
        for line in lines:
            if 'name' in line and not seen:
                # [site] name is the first name
                seen = True
                post.write("name = ''\n")
            else:
                post.write(line)

    result = run_start.invoke(verify)
    # [site] name isn't required
    assert result.exit_code == 0
    assert result.output == expected_output


def test_verify_site_name_missing(run_start: CliRunner) -> None:
    expected_output = (
        'All posts are correctly formatted.\n'
        '[site] name is not set in config.toml.\n'
    )
    config_path = Path('config.toml')
    with config_path.open('r') as post:
        lines = post.readlines()
    with config_path.open('w') as post:
        for line in lines:
            if 'name' not in line:
                post.write(line)

    result = run_start.invoke(verify)

    assert result.exit_code == 0
    assert result.output == expected_output


def test_verify_no_config(run_start: CliRunner) -> None:
    expected_output = 'Can not find config.toml\n'
    Path('config.toml').unlink()
    result = run_start.invoke(verify)

    assert result.exit_code == 1
    assert result.output == expected_output
