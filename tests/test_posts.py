from pathlib import Path
import shutil

from click.testing import CliRunner
from htmd.cli.build import build
from htmd.site.posts import Posts

from utils import (
    remove_fields_from_post,
    remove_from_config_field,
    set_config_field,
    set_example_field,
)


def test_Posts_without_app() -> None:  # noqa: N802
    posts = Posts()
    assert posts._app is None  # noqa: SLF001
    assert posts.published_posts == []
    assert posts.show_drafts is False
    # Doesn't error and can still change show_drafts
    posts.reload(show_drafts=True)
    assert posts.published_posts == []
    assert posts.show_drafts is True


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


def test_posts_base_path(run_start: CliRunner) -> None:
    """Ensure [posts] base_path from config.toml is used when building."""
    # test default behavior (base_path should be /blog/)
    remove_from_config_field('base_path')
    result = run_start.invoke(build)
    assert result.exit_code == 0

    blog_index = Path('build') / 'blog' / 'index.html'
    assert blog_index.is_file()
    contents = blog_index.read_text()
    # The all posts page should include the heading and the example post
    assert '<h1>All Posts</h1>' in contents
    assert 'Example Post' in contents

    # Set posts.base_path to /all/ in config.toml
    set_config_field('posts', 'base_path', '/all/')
    assert 'base_path = "/all/"' in Path('config.toml').read_text()

    result = run_start.invoke(build)
    assert result.exit_code == 0
    all_index = Path('build') / 'all' / 'index.html'
    assert all_index.is_file()
    assert blog_index.exists() is False
    contents = all_index.read_text()
    assert '<h1>All Posts</h1>' in contents
    assert 'Example Post' in contents


def test_hr_only_between_posts(run_start: CliRunner) -> None:
    # build with one post shouldn't have <hr>
    result = run_start.invoke(build)
    assert result.exit_code == 0
    blog_index = Path('build') / 'blog' / 'index.html'
    assert blog_index.is_file()
    contents = blog_index.read_text()
    assert '<hr>' not in contents

    # Create a second post
    src_path = Path('posts') / 'example.md'
    dst_path = Path('posts') / 'copy.md'
    shutil.copy(src_path, dst_path)

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert blog_index.is_file()
    contents = blog_index.read_text()
    assert '<hr>' in contents
