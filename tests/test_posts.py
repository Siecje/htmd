from pathlib import Path
import shutil
import uuid

from click.testing import CliRunner
from htmd.cli.build import build
from htmd.site.posts import Posts, truncate_post_html

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


def test_truncate_post_ellipsis() -> None:
    original = '<p>This is the post <strong>text</strong>.</p>'
    post_html = truncate_post_html(original)
    assert post_html == original

    # count text without HTML elements
    text_length = len('This is the post text.')
    # ellipsis will only be added
    # when there are 4 or more characters remaining
    # Otherwise it will show entire text.
    post_html = truncate_post_html(original, text_length - 1)
    assert post_html == original
    post_html = truncate_post_html(original, text_length - 2)
    assert post_html == original
    post_html = truncate_post_html(original, text_length - 3)
    assert post_html == original
    post_html = truncate_post_html(original, text_length - 4)
    expected = '<p>This is the post <strong>t...</strong></p>'
    assert post_html == expected


def test_truncate_sibling_extraction() -> None:
    original = '<p>This is <strong>text</strong><em>more</em></p>'
    limit = 10
    output = truncate_post_html(original, limit)
    # Expected: The <em> tag should be completely gone.
    assert '<em>' not in output
    assert output == '<p>This is <strong>te...</strong></p>'


def test_truncate_chaos_nesting() -> None:
    html = '<div>Level 1<section><p>Level 2 <b>Level 3 <i>Level 4</i></b>!</p><aside>Remove</aside></section><footer>Remove</footer></div>'  # noqa: E501

    # "Level 1" (7) + "Level 2 " (8) + "Level" (5) = 20
    limit = 20
    output = truncate_post_html(html, limit)

    assert 'Level 4' not in output
    assert '<aside>' not in output
    assert '<footer>' not in output
    assert '!' not in output

    # 20 chars lands exactly after the second 'l' in 'Level 3'
    assert '<b>Level...</b>' in output

    # Verify the structure is still intact
    expected = '<div>Level 1<section><p>Level 2 <b>Level...</b></p></section></div>'
    assert output == expected


def test_post_comments(run_start: CliRunner) -> None:
    result = run_start.invoke(build)
    assert result.exit_code == 0
    post_path = Path('build') / '2014' / '10' / '30' / 'example' / 'index.html'
    post_contents = post_path.read_text()
    assert '<div id="cusdis_thread"' not in post_contents

    app_id = str(uuid.uuid4())
    set_config_field('posts.comments', 'enabled', True)  # noqa: FBT003
    set_config_field('posts.comments', 'cusdis_app_id', app_id)
    set_config_field('posts.comments', 'cusdis_host', 'https://cusdis.com')
    result = run_start.invoke(build)
    assert result.exit_code == 0
    post_path = Path('build') / '2014' / '10' / '30' / 'example' / 'index.html'
    post_contents = post_path.read_text()
    assert '<div id="cusdis_thread"' in post_contents
