import os
from pathlib import Path
import re
import shutil

from click.testing import CliRunner
from htmd.cli.build import build
import yaml

from utils import (
    remove_fields_from_post,
    set_example_password_value,
    set_example_to_draft,
    set_example_to_draft_build,
    SUCCESS_REGEX,
)


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
    with (Path('build') / 'index.html').open('r') as built_index:
        contents = built_index.read()
    assert 'combined.min.js' in contents


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
    # combined.min.css is used instead of style.css
    static_build_files = [
        file.name for file in (Path('build') / 'static').iterdir()]
    assert 'combined.min.css' in static_build_files
    assert 'style.css' not in static_build_files


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
    assert path.exists() is False
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


def test_build_drafts_removed_from_build(run_start: CliRunner) -> None:
    path_list = [
        Path('build') / '2014' / 'index.html',
        Path('build') / '2014' / '10' / 'index.html',
        Path('build') / '2014' / '10' / '30' / 'index.html',
        Path('build') / '2014' / '10' / '30' / 'example' / 'index.html',
    ]
    # create example post in build
    run_start.invoke(build)
    for path in path_list:
        assert path.is_file()

    set_example_to_draft()
    run_start.invoke(build)
    for path in path_list:
        assert path.is_file() is False


def test_build_vcs_repo(run_start: CliRunner) -> None:
    path_list = [
        Path('build') / '.git',
        Path('build') / '.hg',
    ]
    run_start.invoke(build)
    for path in path_list:
        path.mkdir()
        with (path / 'keep').open('w') as keep_file:
            keep_file.write('keep')

    run_start.invoke(build)
    for path in path_list:
        assert path.is_dir()


def test_build_with_default_author(run_start: CliRunner) -> None:
    config_path = Path('config.toml')
    with config_path.open('r') as config_file:
        lines = config_file.readlines()

    with config_path.open('w') as config_file:
        for line in lines:
            if 'default_name' in line:
                config_file.write('default_name = "Taylor"\n')
            else:
                config_file.write(line)

    remove_fields_from_post('example', ('draft',))

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    post_path = Path('build') / '2014' / '10' / '30' / 'example' / 'index.html'
    with post_path.open('r') as post_file:
        contents = post_file.read()
    assert 'Posted by <a href="/author/Taylor/">Taylor</a> on 2014-10-30' in contents


def test_build_contains_favicon(run_start: CliRunner) -> None:
    with (Path('static') / 'favicon.svg').open('r') as favicon_file:
        original_contents = favicon_file.read()
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    build_favicon = Path('build') / 'static' / 'favicon.svg'
    assert build_favicon.is_file()
    with build_favicon.open('r') as favicon_file:
        contents = favicon_file.read()
    assert contents == original_contents


def test_build_password_protect(run_start: CliRunner) -> None:
    set_example_password_value('')
    with (Path('posts') / 'example.md').open('r') as md_file:
        md_str = md_file.read()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    password = data['password']
    assert password is None
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    post_path = Path('build') / '2014' / '10' / '30' / 'example' / 'index.html'
    with post_path.open('r') as post_file:
        contents = post_file.read()
    with (Path('posts') / 'example.md').open('r') as md_file:
        md_str = md_file.read()

    # extract password
    data = yaml.safe_load(md_str[:md_str.find('...')])
    password = data['password']

    assert 'Posted by <a href="/author/Taylor/">Taylor</a> on 2014-10-30' in contents
    title = 'Example Post'
    assert title in md_str
    assert title not in contents
    body = 'This is the post'
    assert body in md_str
    assert body not in contents

    # build again and verify that the password has not changed
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    with (Path('posts') / 'example.md').open('r') as md_file:
        md_str = md_file.read()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    after_password = data['password']
    assert after_password == password


def test_build_password_false(run_start: CliRunner) -> None:
    set_example_password_value('false')
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    post_path = Path('build') / '2014' / '10' / '30' / 'example' / 'index.html'
    with post_path.open('r') as post_file:
        contents = post_file.read()

    assert 'Posted by <a href="/author/Taylor/">Taylor</a> on 2014-10-30' in contents
    title = 'Example Post'
    assert title in contents
    body = 'This is the post'
    assert body in contents

    with (Path('posts') / 'example.md').open('r') as md_file:
        md_str = md_file.read()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    assert data['password'] is False


def test_build_draft_password_protect(run_start: CliRunner) -> None:
    set_example_to_draft_build()
    set_example_password_value('')
    with (Path('posts') / 'example.md').open('r') as md_file:
        md_str = md_file.read()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    password = data['password']
    assert password is None
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    with (Path('posts') / 'example.md').open('r') as md_file:
        md_str = md_file.read()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    build_uuid = data['draft'].replace('build|', '')

    post_path = Path('build') / 'draft' / build_uuid / 'index.html'
    with post_path.open('r') as post_file:
        contents = post_file.read()

    # extract password
    data = yaml.safe_load(md_str[:md_str.find('...')])
    password = data['password']

    assert 'Posted by <a href="/author/Taylor/">Taylor</a> on 2014-10-30' in contents
    title = 'Example Post'
    assert title in md_str
    assert title not in contents
    body = 'This is the post'
    assert body in md_str
    assert body not in contents

    # build again and verify that the password has not changed
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    with (Path('posts') / 'example.md').open('r') as md_file:
        md_str = md_file.read()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    after_password = data['password']
    assert after_password == password


def test_build_draft_password_false(run_start: CliRunner) -> None:
    set_example_to_draft_build()
    set_example_password_value('false')
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    with (Path('posts') / 'example.md').open('r') as md_file:
        md_str = md_file.read()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    build_uuid = data['draft'].replace('build|', '')

    post_path = Path('build') / 'draft' / build_uuid / 'index.html'
    with post_path.open('r') as post_file:
        contents = post_file.read()

    assert 'Posted by <a href="/author/Taylor/">Taylor</a> on 2014-10-30' in contents
    title = 'Example Post'
    assert title in contents
    body = 'This is the post'
    assert body in contents
    assert 'password-protect.js' not in contents

    with (Path('posts') / 'example.md').open('r') as md_file:
        md_str = md_file.read()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    assert data['password'] is False


def test_build_doesnt_have_sse(run_start: CliRunner) -> None:
    sse_js_line = 'sse.onmessage'
    layout_path = Path('templates') / '_layout.html'
    with layout_path.open('r') as layout_file:
        contents = layout_file.read()
    assert sse_js_line in contents

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    post_path = Path('build') / 'index.html'
    with post_path.open('r') as post_file:
        contents = post_file.read()

    assert sse_js_line not in contents
