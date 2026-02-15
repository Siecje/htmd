from pathlib import Path

from click.testing import CliRunner
from htmd.cli.build import build
from htmd.site.posts import Posts

from utils import remove_fields_from_post, set_example_field


def test_Posts_without_app() -> None:  # noqa: N802
    posts = Posts()
    assert posts._app is None  # noqa: SLF001
    assert posts.published_posts == []
    assert posts.show_drafts is False
    # Doesn't error and can still change show_drafts
    posts.reload(show_drafts=True)
    assert posts.show_drafts is True
    assert posts.published_posts == []


def test_post_without_tags(run_start: CliRunner) -> None:
    remove_fields_from_post('example', ('tags',))
    result = run_start.invoke(build)
    assert result.exit_code == 0
    build_post = Path('build') / '2014' / '10' / '30' / 'example' / 'index.html'
    assert build_post.is_file()
    contents = build_post.read_text()
    assert 'Example Post' in contents
    assert '<p><strong>Tags</strong></p>' not in contents

    set_example_field('tags', '[]')
    result = run_start.invoke(build)
    assert result.exit_code == 0
    build_post = Path('build') / '2014' / '10' / '30' / 'example' / 'index.html'
    assert build_post.is_file()
    contents = build_post.read_text()
    assert 'Example Post' in contents
    assert '<p><strong>Tags</strong></p>' not in contents

    build_tags = Path('build') / 'tags' / 'index.html'
    assert build_tags.is_file()
    contents = build_tags.read_text()
    assert '<h1>All Tags</h1>' in contents
