from collections.abc import Iterable, Iterator
from pathlib import Path

from flask import Blueprint, current_app, render_template, url_for
from flask.typing import ResponseReturnValue
from flask_frozen import Freezer

from .pages import pages
from .posts import get_posts


freezer = Freezer(
    with_static_files=False,
    with_no_argument_rules=False,
)


freeze_bp = Blueprint('freezer', __name__)


# Create successful /404.html view
# for build to have 404.html
@freeze_bp.route('/404.html')
def not_found() -> ResponseReturnValue:
    return render_template('404.html')


@freezer.register_generator
def add_404() -> Iterator[str]:
    yield '/404.html'


# Telling Frozen-Flask about routes that are not linked to in templates
@freezer.register_generator
def year_view() -> Iterator[tuple[str, dict[str, int]]]:
    posts = get_posts()
    for post in posts.published_posts:
        yield 'posts.year_view', {
            'year': post.meta['published'].year,
        }


@freezer.register_generator
def month_view() -> Iterator[tuple[str, dict[str, int | str]]]:
    posts = get_posts()
    for post in posts.published_posts:
        yield 'posts.month_view', {
            'month': post.meta['published'].strftime('%m'),
            'year': post.meta['published'].year,
        }


@freezer.register_generator
def day_view() -> Iterator[tuple[str, dict[str, int | str]]]:
    posts = get_posts()
    for post in posts.published_posts:
        yield 'posts.day_view', {
            'day': post.meta['published'].strftime('%d'),
            'month': post.meta['published'].strftime('%m'),
            'year': post.meta['published'].year,
        }


@freezer.register_generator
def draft() -> Iterator[tuple[str, dict[str, str]]]:
    posts = get_posts()
    draft_posts = [
        p
        for p in posts
        if 'draft' in p.meta
        and 'build|' in str(p.meta['draft'])
    ]
    for post in draft_posts:
        yield 'posts.draft', {
            'post_uuid': post.meta['draft'].replace('build|', ''),
        }


@freezer.register_generator
def page() -> Iterator[tuple[str, dict[str, str]]]:
    pages_folder = pages.template_folder
    if not isinstance(pages_folder, Path) or not pages_folder.is_dir():
        return

    # rglob("*") recursively finds all files and directories
    for item in pages_folder.rglob('*.html'):
        if not item.is_file():
            continue
        # Calculate the relative path from the base templates folder
        # Example: 'blog/about.html' -> 'blog/about'
        relative_path = item.relative_to(pages_folder).with_suffix('')

        # Convert to POSIX string (forward slashes) for the URL
        path_str = relative_path.as_posix()

        yield 'pages.page', {'path': path_str}


@freezer.register_generator
def posts_json() -> Iterable[str]:
    if current_app.config.get('RANDOM_POST_ENABLED'):
        yield url_for('posts.posts_json')
