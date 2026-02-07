import os
from pathlib import Path
import re
import shutil

from click.testing import CliRunner
from htmd.cli.build import build
import yaml

from utils import (
    remove_fields_from_post,
    set_config_field,
    set_example_password_value,
    set_example_subtitle,
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
    path = Path('static') / 'app.js'
    path.write_text('console.log("htmd");')

    result = run_start.invoke(build, ['--js-minify'])
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    contents = (Path('build') / 'index.html').read_text()
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
    contents = (Path('build') / 'index.html').read_text()
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
    set_config_field('pretty', 'true')

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)


def test_build_html_minify_true(run_start: CliRunner) -> None:
    set_config_field('minify', 'true')

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
    lines = about_path.read_text().splitlines(keepends=True)

    new_line = '''<p><a href="{{ url_for('pages.page', path='dne') }}">DNE link</a></p>\n'''  # noqa: E501
    replace_line = '<p>This is the about page.</p>\n'
    new_lines = [new_line if replace_line in line else line for line in lines]

    about_path.write_text(''.join(new_lines))

    result = run_start.invoke(build)
    assert result.output == expected_output
    assert result.exit_code == 1


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
    (Path('pages') / 'new.html').write_text(''.join(page_lines))
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert 'Totally new' in (Path('build') / 'new' / 'index.html').read_text()


def test_build_pages_with_non_html_file(run_start: CliRunner) -> None:
    page_path = Path('pages') / '.DS_STORE'
    page_path.touch()
    assert page_path.is_file()
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert (Path('build') / '.DS_STORE').exists() is False
    build_path = Path('build') / '.DS_STORE' / 'index.html'
    assert build_path.exists() is False


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
    lines = layout_path.read_text().splitlines(keepends=True)
    new_lines = [line for line in lines if 'about' not in line]
    layout_path.write_text(''.join(new_lines))

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
    result = run_start.invoke(build)
    assert result.exit_code == 0, result.output
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
        (path / 'keep').write_text('keep')

    run_start.invoke(build)
    for path in path_list:
        assert path.is_dir()


def test_build_with_default_author(run_start: CliRunner) -> None:
    set_config_field('default_name', 'Taylor')

    remove_fields_from_post('example', ('draft',))

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    post_path = Path('build') / '2014' / '10' / '30' / 'example' / 'index.html'
    contents = post_path.read_text()
    expected = 'Posted by <a href="/author/Taylor/">Taylor</a> on 2014-10-30'
    assert expected in contents


def test_build_contains_favicon(run_start: CliRunner) -> None:
    original_contents = (Path('static') / 'favicon.svg').read_text()
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    build_favicon = Path('build') / 'static' / 'favicon.svg'
    assert build_favicon.is_file()
    contents = build_favicon.read_text()
    assert contents == original_contents


def test_build_password_protect(run_start: CliRunner) -> None:
    subtitle = 'This is a subtitle'
    set_example_subtitle(subtitle)
    set_example_password_value('')
    md_str = (Path('posts') / 'example.md').read_text()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    password = data['password']
    assert password is None
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    md_str = (Path('posts') / 'example.md').read_text()

    # extract password
    data = yaml.safe_load(md_str[:md_str.find('...')])
    password = data['password']

    # Verify post page
    post_path = Path('build') / '2014' / '10' / '30' / 'example' / 'index.html'
    contents = post_path.read_text()

    assert (
        'Posted by <a href="/author/Taylor/">Taylor</a> on 2014-10-30'
        in contents
    )
    title = 'Example Post'
    assert title in md_str
    assert title not in contents

    assert subtitle in md_str
    assert subtitle not in contents

    body = 'This is the post'
    assert body in md_str
    assert body not in contents

    # Verify list pages
    home_path = Path('build') / 'index.html'
    all_path = Path('build') / 'all' / 'index.html'
    tag_path = Path('build') / 'tags' / 'first' / 'index.html'
    author_path = Path('build') / 'author' / 'Taylor' / 'index.html'
    year_path = Path('build') / '2014' / 'index.html'
    month_path = Path('build') / '2014' / '10' / 'index.html'
    day_path = Path('build') / '2014' / '10' / '30' / 'index.html'
    list_paths = [
        home_path,
        all_path,
        tag_path,
        author_path,
        year_path,
        month_path,
        day_path,
    ]
    for path in list_paths:
        contents = path.read_text()
        assert title not in contents
        assert 'Protected Post' in contents
        assert subtitle not in contents
        assert body[:5] not in contents

    # build again and verify that the password has not changed
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    md_str = (Path('posts') / 'example.md').read_text()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    after_password = data['password']
    assert after_password == password


def test_build_password_false(run_start: CliRunner) -> None:
    set_example_password_value('false')
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    post_path = Path('build') / '2014' / '10' / '30' / 'example' / 'index.html'
    contents = post_path.read_text()

    assert (
        'Posted by <a href="/author/Taylor/">Taylor</a> on 2014-10-30'
        in contents
    )
    title = 'Example Post'
    assert title in contents
    body = 'This is the post'
    assert body in contents

    md_str = (Path('posts') / 'example.md').read_text()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    assert data['password'] is False


def test_build_draft_password_protect(run_start: CliRunner) -> None:
    set_example_to_draft_build()
    set_example_password_value('')
    md_str = (Path('posts') / 'example.md').read_text()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    password = data['password']
    assert password is None
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    md_str = (Path('posts') / 'example.md').read_text()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    build_uuid = data['draft'].replace('build|', '')

    post_path = Path('build') / 'draft' / build_uuid / 'index.html'
    contents = post_path.read_text()

    # extract password
    data = yaml.safe_load(md_str[:md_str.find('...')])
    password = data['password']

    assert (
        'Posted by <a href="/author/Taylor/">Taylor</a> on 2014-10-30'
        in contents
    )

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
    md_str = (Path('posts') / 'example.md').read_text()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    after_password = data['password']
    assert after_password == password


def test_build_draft_password_false(run_start: CliRunner) -> None:
    set_example_to_draft_build()
    set_example_password_value('false')
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    md_str = (Path('posts') / 'example.md').read_text()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    build_uuid = data['draft'].replace('build|', '')

    post_path = Path('build') / 'draft' / build_uuid / 'index.html'
    contents = post_path.read_text()

    assert (
        'Posted by <a href="/author/Taylor/">Taylor</a> on 2014-10-30'
        in contents
    )
    title = 'Example Post'
    assert title in contents
    body = 'This is the post'
    assert body in contents
    assert 'password-protect.js' not in contents

    md_str = (Path('posts') / 'example.md').read_text()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    assert data['password'] is False


def test_build_doesnt_have_sse(run_start: CliRunner) -> None:
    sse_js_line = 'sse.onmessage'
    layout_path = Path('templates') / '_layout.html'
    contents = layout_path.read_text()
    assert sse_js_line in contents

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    post_path = Path('build') / 'index.html'
    contents = post_path.read_text()

    assert sse_js_line not in contents


def test_post_without_published_and_without_author(
    run_start: CliRunner,
) -> None:
    set_config_field('show', value=False)
    set_example_to_draft_build()
    remove_fields_from_post('example', ('published', 'updated'))

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    md_str = (Path('posts') / 'example.md').read_text()
    data = yaml.safe_load(md_str[:md_str.find('...')])
    build_uuid = data['draft'].replace('build|', '')

    post_path = Path('build') / 'draft' / build_uuid / 'index.html'
    contents = post_path.read_text()

    assert (
        'Posted by <a href="/author/Taylor/">Taylor</a> on 2014-10-30'
        not in contents
    )
    assert '<span class="meta">' not in contents
