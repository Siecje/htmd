from collections.abc import Generator
from pathlib import Path
import re

from click.testing import CliRunner
from htmd.cli.build import build
from htmd.cli.start import start
import pytest

from utils import (
  remove_fields_from_post,
  set_example_to_draft,
  set_example_to_draft_build,
  SUCCESS_REGEX,
)


def copy_example_as_draft_build() -> None:
    post_path = Path('posts') / 'example.md'
    copy_path = Path('posts') / 'copy.md'
    with post_path.open('r') as post_file:
        lines = post_file.readlines()
    with copy_path.open('w') as copy_file:
        for line in lines:
            if 'draft' in line:
                copy_file.write('draft: build\n')
            else:
                copy_file.write(line)


def get_draft_uuid(path: str) -> str:
    draft_path = Path('posts') / f'{path}.md'
    with draft_path.open('r') as draft_file:
        for line in draft_file.readlines():
            if 'draft: build' in line:
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
        assert result.exit_code == 0
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
    with (Path('build') / 'index.html').open('r') as home_page:
        assert 'Example Post' not in home_page.read()


def test_no_drafts_atom_feed(build_draft: CliRunner) -> None:  # noqa: ARG001
    with (Path('build') / 'feed.atom').open('r') as feed_page:
        assert 'Example Post' not in feed_page.read()


def test_no_drafts_all_posts(build_draft: CliRunner) -> None:  # noqa: ARG001
    with (Path('build') / 'all' / 'index.html').open('r') as web_page:
        assert 'Example Post' not in web_page.read()


def test_no_drafts_all_tags(build_draft: CliRunner) -> None:  # noqa: ARG001
    with (Path('build') / 'tags' / 'index.html').open('r') as web_page:
        assert 'first' not in web_page.read()


def test_no_drafts_in_tag(build_draft: CliRunner) -> None:  # noqa: ARG001
    # tag page exists because the draft links to it
    with (Path('build') / 'tags' / 'first' / 'index.html').open('r') as web_page:
        assert 'Example Post' not in web_page.read()


def test_no_drafts_for_author(build_draft: CliRunner) -> None:  # noqa: ARG001
    # author page exists because the draft links to it
    with (Path('build') / 'author' / 'Taylor' / 'index.html').open('r') as web_page:
        assert 'Example Post' not in web_page.read()


def test_no_drafts_for_year(build_draft: CliRunner) -> None:  # noqa: ARG001
    # folder exists becaues of URL for post
    assert (Path('build') / '2014' / 'index.html').exists() is False


def test_no_drafts_for_month(build_draft: CliRunner) -> None:  # noqa: ARG001
    # folder exists becaues of URL for post
    assert (Path('build') / '2014' / '10' / 'index.html').exists() is False


def test_no_drafts_for_day(build_draft: CliRunner) -> None:  # noqa: ARG001
    # folder exists becaues of URL for post
    assert (Path('build') / '2014' / '10' / '30' / 'index.html').exists() is False


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
