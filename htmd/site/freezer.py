from collections.abc import Iterator
from pathlib import Path
import uuid

from flask import Blueprint, current_app, render_template
from flask.typing import ResponseReturnValue
from flask_frozen import Freezer

from ..utils import set_post_metadata, valid_uuid
from .pages import pages
from .posts import posts


freezer = Freezer(with_static_files=False, with_no_argument_rules=False)


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
    for post in posts.published_posts:
        yield 'posts.year_view', {
            'year': post.meta['published'].year,
        }


@freezer.register_generator
def month_view() -> Iterator[tuple[str, dict[str, int | str]]]:
    for post in posts.published_posts:
        yield 'posts.month_view', {
            'month': post.meta['published'].strftime('%m'),
            'year': post.meta['published'].year,
        }


@freezer.register_generator
def day_view() -> Iterator[tuple[str, dict[str, int | str]]]:
    for post in posts.published_posts:
        yield 'posts.day_view', {
            'day': post.meta['published'].strftime('%d'),
            'month': post.meta['published'].strftime('%m'),
            'year': post.meta['published'].year,
        }


@freezer.register_generator
def draft() -> Iterator[tuple[str, dict[str, str]]]:
    draft_posts = [
        p for p in posts
        if 'draft' in p.meta and 'build' in str(p.meta['draft'])
    ]
    for post in draft_posts:
        if not valid_uuid(post.meta['draft'].replace('build|', '')):
            post.meta['draft'] = 'build|' + str(uuid.uuid4())
            set_post_metadata(
                current_app,
                post,
                {'draft': post.meta['draft']},
            )
        yield 'posts.draft', {
            'post_uuid': post.meta['draft'].replace('build|', ''),
        }


@freezer.register_generator
def page() -> Iterator[tuple[str, dict[str, str]]]:
    pages_folder = pages.template_folder
    if not isinstance(pages_folder, Path) or not pages_folder.is_dir():
        return
    for page in pages_folder.iterdir():
        if page.is_file() and not page.name.startswith('.') and page.suffix == '.html':
            yield 'pages.page', {'path': page.stem}
