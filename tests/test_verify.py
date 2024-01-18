import os

from click.testing import CliRunner
from htmd.cli import start, verify

from utils import remove_fields_from_example_post


def test_verify():
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(start)
        result = runner.invoke(verify)
    assert result.exit_code == 0
    expected_output = 'All posts are correctly formatted.\n'
    assert result.output == expected_output


def test_verify_author_missing():
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(start)

        # Remove author from example post
        remove_fields_from_example_post(('author',))

        result = runner.invoke(verify)
    assert result.exit_code == 1
    expected_output = 'Post "example" does not have field author.\n'
    assert result.output == expected_output


def test_verify_title_missing():
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(start)

        # Remove title from example post
        remove_fields_from_example_post(('title',))

        result = runner.invoke(verify)
    assert result.exit_code == 1
    expected_output = 'Post "example" does not have field title.\n'
    assert result.output == expected_output


def test_verify_published_missing():
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(start)

        # Remove published from example post
        remove_fields_from_example_post(('published',))

        result = runner.invoke(verify)
    # verify doesn't check for published
    # since it will be added on build.
    expected_output = 'All posts are correctly formatted.\n'
    assert result.output == expected_output
    assert result.exit_code == 0


def test_verify_published_invalid_year():
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(start)

        with open(os.path.join('posts', 'example.md'), 'r') as post:
            lines = post.readlines()
        with open(os.path.join('posts', 'example.md'), 'w') as post:
            for line in lines:
                if 'published' in line:
                    post.write('published: 14-10-30\n')
                else:
                    post.write(line)

        result = runner.invoke(verify)
    assert result.exit_code == 1
    expected_output = (
        'Published date 14-10-30 for example'
        ' is not in the format YYYY-MM-DD.\n'
    )
    assert result.output == expected_output


def test_verify_published_invalid_month():
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(start)

        with open(os.path.join('posts', 'example.md'), 'r') as post:
            lines = post.readlines()
        with open(os.path.join('posts', 'example.md'), 'w') as post:
            for line in lines:
                if 'published' in line:
                    post.write('published: 2014-1-30\n')
                else:
                    post.write(line)

        result = runner.invoke(verify)
    assert result.exit_code == 1
    expected_output = (
        'Published date 2014-1-30 for example'
        ' is not in the format YYYY-MM-DD.\n'
    )
    assert result.output == expected_output


def test_verify_published_invalid_day():
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(start)

        with open(os.path.join('posts', 'example.md'), 'r') as post:
            lines = post.readlines()
        with open(os.path.join('posts', 'example.md'), 'w') as post:
            for line in lines:
                if 'published' in line:
                    post.write('published: 2014-01-3\n')
                else:
                    post.write(line)

        result = runner.invoke(verify)
    assert result.exit_code == 1
    expected_output = (
        'Published date 2014-01-3 for example'
        ' is not in the format YYYY-MM-DD.\n'
    )
    assert result.output == expected_output


def test_verify_site_name_empty():
    expected_output = (
        'All posts are correctly formatted.\n'
        '[site] name is not set in config.toml.\n'
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(start)

        with open('config.toml', 'r') as post:
            lines = post.readlines()
        with open('config.toml', 'w') as post:
            seen = False
            for line in lines:
                if 'name' in line and not seen:
                    # [site] name is the first name
                    seen = True
                    post.write("name = ''\n")
                else:
                    post.write(line)

        result = runner.invoke(verify)
    # [site] name isn't required
    assert result.exit_code == 0
    assert result.output == expected_output


def test_verify_site_name_missing():
    expected_output = (
        'All posts are correctly formatted.\n'
        '[site] name is not set in config.toml.\n'
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(start)

        with open('config.toml', 'r') as post:
            lines = post.readlines()
        with open('config.toml', 'w') as post:
            for line in lines:
                if 'name' not in line:
                    post.write(line)

        result = runner.invoke(verify)

    assert result.exit_code == 0
    assert result.output == expected_output


def test_verify_no_config():
    expected_output = 'Can not find config.toml\n'
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(start)

        os.remove('config.toml')

        result = runner.invoke(verify)

    assert result.exit_code == 1
    assert result.output == expected_output
