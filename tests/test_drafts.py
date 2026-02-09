from collections.abc import Generator
from pathlib import Path
import re

from click.testing import CliRunner
from htmd.cli.build import build
from htmd.cli.start import start
from htmd.utils import atomic_write
import pytest

from utils import (
    get_example_field,
    http_get,
    remove_fields_from_post,
    set_example_draft_status,
    set_example_to_draft,
    set_example_to_draft_build,
    SUCCESS_REGEX,
    wait_for_str_in_file,
)
from utils_preview import run_preview


def copy_example_as_draft_build() -> Path:
    post_path = Path('posts') / 'example.md'
    copy_path = Path('posts') / 'copy.md'
    lines = post_path.read_text().splitlines(keepends=True)
    new_lines = [
        'draft: build\n' if 'draft' in line
        else line
        for line in lines
    ]
    atomic_write(copy_path, ''.join(new_lines))
    return copy_path


def get_draft_uuid(path: str) -> str:
    draft_path = Path('posts') / f'{path}.md'
    lines = draft_path.read_text().splitlines(keepends=True)
    for line in lines:
        if 'draft: build|' in line:
            return line.replace('draft: build|', '').strip()
    return ''


@pytest.fixture(scope='module')
def build_draft() -> Generator[CliRunner]:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        set_example_to_draft()
        copy_example_as_draft_build()
        result = runner.invoke(build)
        assert result.exit_code == 0, result.output
        assert re.search(SUCCESS_REGEX, result.output)
        # Tests code is run here
        yield runner


def test_draft_only_draft_build_is_in_build(build_draft: CliRunner) -> None:
    post_path = Path('build') / '2014' / '10' / '30' / 'example' / 'index.html'
    assert post_path.exists() is False

    example_uuid = get_draft_uuid('example')
    assert example_uuid == ''
    draft_uuid = get_draft_uuid('copy')
    draft_path = Path('build') / 'draft' / draft_uuid / 'index.html'
    assert draft_path.is_file() is True

    # build again now that draft has uuid
    result = build_draft.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    assert draft_path.is_file() is True


def test_no_drafts_home(build_draft: CliRunner) -> None:  # noqa: ARG001
    assert 'Example Post' not in (Path('build') / 'index.html').read_text()


def test_no_drafts_atom_feed(build_draft: CliRunner) -> None:  # noqa: ARG001
    assert 'Example Post' not in (Path('build') / 'feed.atom').read_text()


def test_no_drafts_all_posts(build_draft: CliRunner) -> None:  # noqa: ARG001
    build_all = (Path('build') / 'all' / 'index.html').read_text()
    assert 'Example Post' not in build_all


def test_no_drafts_all_tags(build_draft: CliRunner) -> None:  # noqa: ARG001
    assert 'first' not in (Path('build') / 'tags' / 'index.html').read_text()


def test_no_drafts_in_tag(build_draft: CliRunner) -> None:  # noqa: ARG001
    # tag page exists because the draft links to it
    first = (Path('build') / 'tags' / 'first' / 'index.html').read_text()
    assert 'Example Post' not in first


def test_no_drafts_for_author(build_draft: CliRunner) -> None:  # noqa: ARG001
    # author page exists because the draft links to it
    author = (Path('build') / 'author' / 'Taylor' / 'index.html').read_text()
    assert 'Example Post' not in author


def test_no_drafts_for_year(build_draft: CliRunner) -> None:  # noqa: ARG001
    # folder exists becaues of URL for post
    assert (Path('build') / '2014' / 'index.html').exists() is False


def test_no_drafts_for_month(build_draft: CliRunner) -> None:  # noqa: ARG001
    # folder exists becaues of URL for post
    assert (Path('build') / '2014' / '10' / 'index.html').exists() is False


def test_no_drafts_for_day(build_draft: CliRunner) -> None:  # noqa: ARG001
    # folder exists becaues of URL for post
    day = Path('build') / '2014' / '10' / '30' / 'index.html'
    assert day.exists() is False


def test_draft_without_published(run_start: CliRunner) -> None:
    set_example_to_draft()
    remove_fields_from_post('example', ('published', 'updated'))
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    draft_path = Path('build') / 'draft' / 'example' / 'index.html'
    assert not draft_path.is_file()


def test_draft_build_and_without_published(run_start: CliRunner) -> None:
    set_example_to_draft_build()
    remove_fields_from_post('example', ('published', 'updated'))
    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)
    draft_uuid = get_draft_uuid('example')
    draft_path = Path('build') / 'draft' / draft_uuid / 'index.html'
    assert draft_path.is_file() is True

    anchor_text = f'<a href="/draft/{draft_uuid}/" class="post-preview-link"'
    with run_preview(run_start, ['--drafts']) as base_url:
        response = http_get(base_url + '/author/Taylor/')
        contents = response.text
        assert response.status_code == 200  # noqa: PLR2004
        assert 'Example Post' in contents
        assert anchor_text in contents

    with run_preview(run_start) as base_url:
        response = http_get(base_url + '/author/Taylor/')
        contents = response.text
        # draft post is in build and links to author so author page exists
        assert response.status_code == 200  # noqa: PLR2004
        assert 'Example Post' not in contents
        assert anchor_text not in contents


def test_draft_build_preview(run_start: CliRunner) -> None:
    set_example_to_draft_build()
    draft_value = get_example_field('draft')
    assert draft_value == 'build'
    draft_uuid = get_draft_uuid('example')
    assert draft_uuid == ''

    with run_preview(run_start) as base_url:
        draft_uuid = get_draft_uuid('example')
        assert draft_uuid != ''
        response = http_get(base_url + f'/draft/{draft_uuid}/')
        assert response.status_code == 200  # noqa: PLR2004
        contents = response.text
        assert 'Example Post' in contents


def test_draft_build_preview_without_published(run_start: CliRunner) -> None:
    remove_fields_from_post('example', ('published', 'updated'))
    set_example_to_draft_build()
    draft_value = get_example_field('draft')
    assert draft_value == 'build'
    draft_uuid = get_draft_uuid('example')
    assert draft_uuid == ''

    with run_preview(run_start) as base_url:
        draft_uuid = get_draft_uuid('example')
        assert draft_uuid != ''
        response = http_get(base_url + f'/draft/{draft_uuid}/')
        assert response.status_code == 200  # noqa: PLR2004
        contents = response.text
        assert 'Example Post' in contents


def test_draft_during_preview(run_start: CliRunner) -> None:
    post_path = Path('posts') / 'example.md'
    with run_preview(run_start) as base_url:
        # Wait for initial watchdog to finish
        wait_for_str_in_file(post_path, '_hash')
        set_example_to_draft_build()
        wait_for_str_in_file(post_path, 'build|')
        post_uuid = get_draft_uuid('example')
        assert post_uuid != ''
        response = http_get(base_url + f'/draft/{post_uuid}/')
        assert response.status_code == 200  # noqa: PLR2004
        contents = response.text
        assert 'Example Post' in contents


def test_new_draft_during_preview(run_start: CliRunner) -> None:
    # put draft line in example so that when we copy it we can set it to build
    example_path = Path('posts') / 'example.md'
    set_example_draft_status('false')
    with run_preview(run_start) as base_url:
        # Wait for initial watchdog to finish
        wait_for_str_in_file(example_path, '_hash')
        # Create new draft build post
        post_path = copy_example_as_draft_build()
        wait_for_str_in_file(post_path, 'build|')
        post_uuid = get_draft_uuid(post_path.stem)
        assert post_uuid != ''
        response = http_get(base_url + f'/draft/{post_uuid}/')
        assert response.status_code == 200  # noqa: PLR2004
        contents = response.text
        assert 'Example Post' in contents
