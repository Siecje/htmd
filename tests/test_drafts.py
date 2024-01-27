from pathlib import Path

from click.testing import CliRunner
from htmd.cli import build, start
import pytest

from utils import remove_fields_from_example_post


def set_example_as_draft():
    remove_fields_from_example_post(('draft',))
    post_path = Path('posts') / 'example.md'
    with post_path.open('r') as post_file:
        lines = post_file.readlines()
    with post_path.open('w') as post_file:
        for line in lines:
            if line == '...\n':
                post_file.write('draft: true\n')
            post_file.write(line)


@pytest.fixture(scope='module')
def build_draft():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        set_example_as_draft()
        result = runner.invoke(build)
        assert result.exit_code == 0
        # Tests code is run here
        yield
    

def test_draft_is_built(build_draft) -> None:
    with (Path('build') / '2014' / '10' / '30' / 'example' / 'index.html').open('r') as post_page:
        assert 'Example Post' in post_page.read()


def test_no_drafts_home(build_draft) -> None:
    with (Path('build') / 'index.html').open('r') as home_page:
        assert 'Example Post' not in home_page.read()


def test_no_drafts_atom_feed(build_draft) -> None:
    with (Path('build') / 'feed.atom').open('r') as feed_page:
        assert 'Example Post' not in feed_page.read()


def test_no_drafts_all_posts(build_draft) -> None:
    with (Path('build') / 'all' / 'index.html').open('r') as web_page:
        assert 'Example Post' not in web_page.read()


def test_no_drafts_all_tags(build_draft) -> None:
    with (Path('build') / 'tags' / 'index.html').open('r') as web_page:
        assert 'first' not in web_page.read()


def test_no_drafts_in_tag(build_draft) -> None:
    # tag page exists because the draft links to it
    with (Path('build') / 'tags' / 'first' / 'index.html').open('r') as web_page:
        assert 'Example Post' not in web_page.read()


def test_no_drafts_for_author(build_draft) -> None:
    # author page exists because the draft links to it
    with (Path('build') / 'author' / 'Taylor' / 'index.html').open('r') as web_page:
        assert 'Example Post' not in web_page.read()


def test_no_drafts_for_year(build_draft) -> None:
    # folder exists becaues of URL for post
    assert (Path('build') / '2014' / 'index.html').exists() is False


def test_no_drafts_for_month(build_draft) -> None:
    # folder exists becaues of URL for post
    assert (Path('build') / '2014' / '10' / 'index.html').exists() is False


def test_no_drafts_for_day(build_draft) -> None:
    # folder exists becaues of URL for post
    assert (Path('build') / '2014' / '10' / '30' / 'index.html').exists() is False
