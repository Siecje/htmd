import os
import re
import shutil

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
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)

        with open(os.path.join('static', 'app.js'), 'w') as js_file:
            js_file.write('console.log("htmd");')

        result = runner.invoke(build, ['--js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_js_minify_no_js_files():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(build, ['--js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_no_js_minify():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(build, ['--no-js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_css_minify():
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
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(build, ['--no-css-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_css_minify_no_css_files():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        os.remove(os.path.join('static', 'style.css'))
        os.remove(os.path.join('static', '_reset.css'))
        result = runner.invoke(build, ['--css-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_html_pretty_true():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        with open('config.toml', 'r') as config_file:
            lines = config_file.readlines()

        with open('config.toml', 'w') as config_file:
            for line in lines:
                if 'pretty =' in line:
                    config_file.write('pretty = true\n')
                else:
                    config_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_html_minify_true():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        with open('config.toml', 'r') as config_file:
            lines = config_file.readlines()

        with open('config.toml', 'w') as config_file:
            for line in lines:
                if 'minify =' in line:
                    config_file.write('minify = true\n')
                else:
                    config_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_page_404():
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

        with open(os.path.join('pages', 'about.html'), 'r') as about_file:
            lines = about_file.readlines()

        new_line = '''<p><a href="{{ url_for('pages.page', path='dne') }}">DNE link</a></p>\n'''
        with open(os.path.join('pages', 'about.html'), 'w') as about_file:
            for line in lines:
                if '<p>This is the about page.</p>' in line:
                    about_file.write(new_line)
                else:
                    about_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_post_404_invalid_date_year():
    # Linking to a post with incorrect values
    # for dates will cause 404 and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /14/10/30/example/\n"
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)

        with open(os.path.join('pages', 'about.html'), 'r') as about_file:
            lines = about_file.readlines()

        new_line = '''<p><a href="{{ url_for('post', year=14, month='10', day='30', path='example') }}">DNE link</a></p>\n'''
        with open(os.path.join('pages', 'about.html'), 'w') as about_file:
            for line in lines:
                if '<p>This is the about page.</p>' in line:
                    about_file.write(new_line)
                else:
                    about_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_post_404_invalid_date_month():
    # Linking to a post with incorrect values
    # for dates will cause 404 and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /2014/1/30/example/\n"
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)

        with open(os.path.join('posts', 'example.md'), 'r') as post_file:
            lines = post_file.readlines()

        with open(os.path.join('posts', 'about.html'), 'w') as post_file:
            for line in lines:
                if 'published' in line:
                    post_file.write('published: 2014-01-30')
                elif 'updated' in line:
                    post_file.write('updated: 2014-01-30')
                else:
                    post_file.write(line)

        with open(os.path.join('pages', 'about.html'), 'r') as about_file:
            lines = about_file.readlines()

        new_line = '''<p><a href="{{ url_for('post', year=2014, month='1', day='30', path='example') }}">DNE link</a></p>\n'''
        with open(os.path.join('pages', 'about.html'), 'w') as about_file:
            for line in lines:
                if '<p>This is the about page.</p>' in line:
                    about_file.write(new_line)
                else:
                    about_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_post_404_invalid_date_day():
    # Linking to a post with incorrect values
    # for dates will cause 404 and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /2014/10/3/example/\n"
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)

        with open(os.path.join('posts', 'example.md'), 'r') as post_file:
            lines = post_file.readlines()

        with open(os.path.join('posts', 'about.html'), 'w') as post_file:
            for line in lines:
                if 'published' in line:
                    post_file.write('published: 2014-10-03')
                elif 'updated' in line:
                    post_file.write('updated: 2014-10-03')
                else:
                    post_file.write(line)

        with open(os.path.join('pages', 'about.html'), 'r') as about_file:
            lines = about_file.readlines()

        new_line = '''<p><a href="{{ url_for('post', year=2014, month='10', day='3', path='example') }}">DNE link</a></p>\n'''
        with open(os.path.join('pages', 'about.html'), 'w') as about_file:
            for line in lines:
                if '<p>This is the about page.</p>' in line:
                    about_file.write(new_line)
                else:
                    about_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_post_404_different_date():
    # Linking to a page with the wrong date
    # will cause a 404 status code
    # and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /2014/10/29/example/\n"
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)

        with open(os.path.join('pages', 'about.html'), 'r') as about_file:
            lines = about_file.readlines()

        new_line = '''<p><a href="{{ url_for('post', year=2014, month='10', day='29', path='example') }}">DNE link</a></p>\n'''
        with open(os.path.join('pages', 'about.html'), 'w') as about_file:
            for line in lines:
                if '<p>This is the about page.</p>' in line:
                    about_file.write(new_line)
                else:
                    about_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_multiple_posts():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        shutil.copyfile(
            os.path.join('posts', 'example.md'),
            os.path.join('posts', 'sample.md')
        )
        result = runner.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_year_404_incorrect():
    # Linking to a page with the wrong date
    # will cause a 404 status code
    # and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /14/\n"
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)

        with open(os.path.join('pages', 'about.html'), 'r') as about_file:
            lines = about_file.readlines()

        new_line = '''<p><a href="{{ url_for('year_view', year=14) }}">DNE link</a></p>\n'''
        with open(os.path.join('pages', 'about.html'), 'w') as about_file:
            for line in lines:
                if '<p>This is the about page.</p>' in line:
                    about_file.write(new_line)
                else:
                    about_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 1
    print(result.output)
    assert result.output == expected_output


def test_build_year_404_no_posts():
    # Linking to a page with the wrong date
    # will cause a 404 status code
    # and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /2013/\n"
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)

        with open(os.path.join('pages', 'about.html'), 'r') as about_file:
            lines = about_file.readlines()

        new_line = '''<p><a href="{{ url_for('year_view', year=2013) }}">DNE link</a></p>\n'''
        with open(os.path.join('pages', 'about.html'), 'w') as about_file:
            for line in lines:
                if '<p>This is the about page.</p>' in line:
                    about_file.write(new_line)
                else:
                    about_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_month_404_no_posts():
    # Linking to a page with the wrong date
    # will cause a 404 status code
    # and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /2014/01/\n"
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)

        with open(os.path.join('pages', 'about.html'), 'r') as about_file:
            lines = about_file.readlines()

        new_line = '''<p><a href="{{ url_for('month_view', year=2014, month='01') }}">DNE link</a></p>\n'''
        with open(os.path.join('pages', 'about.html'), 'w') as about_file:
            for line in lines:
                if '<p>This is the about page.</p>' in line:
                    about_file.write(new_line)
                else:
                    about_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_day_404_no_posts():
    # Linking to a page with the wrong date
    # will cause a 404 status code
    # and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /2014/10/29/\n"
    )
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)

        with open(os.path.join('pages', 'about.html'), 'r') as about_file:
            lines = about_file.readlines()

        new_line = '''<p><a href="{{ url_for('day_view', year=2014, month='10', day='29') }}">DNE link</a></p>\n'''
        with open(os.path.join('pages', 'about.html'), 'w') as about_file:
            for line in lines:
                if '<p>This is the about page.</p>' in line:
                    about_file.write(new_line)
                else:
                    about_file.write(line)

        result = runner.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output
