import calendar
import datetime

from bs4 import BeautifulSoup
from feedwerk.atom import AtomFeed
from flask import (
    abort,
    Blueprint,
    current_app,
    render_template,
    Response,
    url_for,
)
from flask.blueprints import BlueprintSetupState
from flask.typing import ResponseReturnValue
from flask_flatpages import FlatPages, Page

from ..password_protect import encrypt_post
from ..utils import set_post_metadata


posts_bp = Blueprint('posts', __name__)


class Posts(FlatPages):
    def __init__(self) -> None:
        super().__init__()
        self.show_drafts: bool = False
        self.published_posts: list[Page] = []


posts = Posts()


def reload_posts(show_drafts: bool | None = None) -> None: # noqa: FBT001
    posts.reload()
    if show_drafts is not None:
        posts.show_drafts = show_drafts
    if posts.show_drafts:
        posts.published_posts = [
            p for p in posts
            if 'published' in p.meta and hasattr(p.meta['published'], 'year')
        ]
    else:
        posts.published_posts = [
            p for p in posts
            if (
                not p.meta.get('draft', False)
                and 'published' in p.meta
                and hasattr(p.meta['published'], 'year')
            )
        ]


def truncate_post_html(post_html: str) -> str:
    return BeautifulSoup(post_html[:255], 'html.parser').prettify()


@posts_bp.record_once
def on_load(state: BlueprintSetupState) -> None:
    # state.app is the actual Flask app instance
    state.app.jinja_env.globals['truncate_post_html'] = truncate_post_html


@posts_bp.route('/feed.atom')
def feed() -> Response:
    name = current_app.config.get('SITE_NAME')
    subtitle = current_app.config.get('SITE_DESCRIPTION') or 'Recent Blog Posts'
    feed_url = url_for('posts.feed', _external=True)
    url = url_for('posts.all_posts', _external=True)
    atom = AtomFeed(
        feed_url=feed_url,
        generator=(None, None, None),
        subtitle=subtitle,
        title=name,
        url=url,
    )
    for post in posts.published_posts:
        url = url_for(
            'posts.post',
            year=post.meta['published'].strftime('%Y'),
            month=post.meta['published'].strftime('%m'),
            day=post.meta['published'].strftime('%d'),
            path=post.path,
            _external=True,
        )

        # published and updated need to be datetime
        published = post.meta['published']
        post_datetime = post.meta.get('updated', published)
        atom.add(
            post.meta.get('title'),
            post.html,
            author=post.meta.get('author', current_app.config.get('DEFAULT_AUTHOR')),
            content_type='html',
            published=published,
            updated=post_datetime,
            url=url,
        )
    ret = atom.get_response()
    return ret


@posts_bp.route('/all/')
def all_posts() -> ResponseReturnValue:
    latest = sorted(
        posts.published_posts,
        reverse=True,
        key=lambda p: p.meta['published'],
    )
    return render_template('all_posts.html', active='posts', posts=latest)


def draft_and_not_shown(post: Page) -> bool:
    is_draft = 'draft' in post.meta
    return is_draft and not posts.show_drafts and 'build' not in str(post.meta['draft'])


def render_password_protected_post(post: Page) -> ResponseReturnValue:
    (
        password,
        encrypted_content,
        encrypted_title,
        encrypted_subtitle,
    ) = encrypt_post(
        post.html,
        post.meta['title'],
        post.meta.get('subtitle'),
        post.meta['password'],
    )
    if password != post.meta['password']:
        set_post_metadata(
            current_app,
            post,
            {'password': password},
        )
    return render_template(
        'post.html',
        active=post.path,
        post=post,
        encrypted_content=encrypted_content,
        encrypted_title=encrypted_title,
        encrypted_subtitle=encrypted_subtitle,
    )


# If month and day are ints then Flask removes leading zeros
@posts_bp.route('/<year>/<month>/<day>/<path:path>/')
def post(year: str, month: str, day: str, path: str) -> ResponseReturnValue:
    if len(year) != 4 or len(month) != 2 or len(day) != 2:  # noqa: PLR2004
        abort(404)
    post = posts.get_or_404(path)
    if draft_and_not_shown(post):
        abort(404)
    date_str = f'{year}-{month}-{day}'
    published = post.meta.get('published')
    if (not isinstance(published, (datetime.date))
        or published.strftime('%Y-%m-%d') != date_str
    ):
        abort(404)
    if 'password' in post.meta and post.meta['password'] is not False:
        return render_password_protected_post(post)
    return render_template('post.html', active=path, post=post)


@posts_bp.route('/draft/<post_uuid>/')
def draft(post_uuid: str) -> ResponseReturnValue:
    for post in posts:
        if str(post.meta.get('draft', '')).replace('build|', '') == post_uuid:
            break
    else:
        abort(404)
    if 'password' in post.meta and post.meta['password'] is not False:
        return render_password_protected_post(post)
    return render_template(
        'post.html',
        active=post.path,
        post=post,
    )


@posts_bp.route('/tags/')
def all_tags() -> ResponseReturnValue:
    tag_counts: dict[str, int] = {}
    for post in posts.published_posts:
        for tag in post.meta.get('tags', []):
            if tag not in tag_counts:
                tag_counts[tag] = 0
            tag_counts[tag] += 1
    return render_template('all_tags.html', active='tags', tags=tag_counts)


def no_posts_shown(post_list: list[Page]) -> bool:
    return all(
        'draft' in p.meta and 'build' not in str(p.meta['draft'])
        for p in post_list
    )


@posts_bp.route('/tags/<string:tag>/')
def tag(tag: str) -> ResponseReturnValue:
    tagged = [p for p in posts if tag in p.meta.get('tags', [])]
    if not tagged:
        abort(404)
    if not posts.show_drafts and no_posts_shown(tagged):
        abort(404)
    if posts.show_drafts:
        tagged_published = tagged
    else:
        tagged_published = [p for p in tagged if 'draft' not in p.meta]
    sorted_posts = sorted(
        tagged_published,
        reverse=True,
        key=lambda p: p.meta.get('published'),
    )
    return render_template('tag.html', active=tag, posts=sorted_posts, tag=tag)


@posts_bp.route('/author/<author>/')
def author(author: str) -> ResponseReturnValue:
    # if the author has a draft build
    # page is served without displaying posts
    # so no 404 when for the link from the draft
    posts_author = [p for p in posts if author == p.meta.get('author', '')]

    if not posts_author:
        abort(404)

    if not posts.show_drafts and no_posts_shown(posts_author):
        abort(404)
    if posts.show_drafts:
        posts_author_published = posts_author
    else:
        posts_author_published = [p for p in posts_author if 'draft' not in p.meta]

    posts_sorted = sorted(
        posts_author_published,
        reverse=True,
        key=lambda p: p.meta.get('published'),
    )
    return render_template(
        'author.html',
        active='author',
        author=author,
        posts=posts_sorted,
    )


@posts_bp.route('/<int:year>/')
def year_view(year: int) -> ResponseReturnValue:
    year_str = str(year)
    if len(year_str) != len('YYYY'):
        abort(404)
    year_posts = [
        p for p in posts.published_posts
        if year_str == p.meta['published'].strftime('%Y')
    ]
    if not year_posts:
        abort(404)
    sorted_posts = sorted(
        year_posts,
        reverse=False,
        key=lambda p: p.meta['published'],
    )
    return render_template(
        'year.html',
        active=year_str,
        year=year_str,
        posts=sorted_posts,
    )


@posts_bp.route('/<year>/<month>/')
def month_view(year: str, month: str) -> ResponseReturnValue:
    month_posts = [
        p for p in posts.published_posts if year == p.meta['published'].strftime('%Y')
        and month == p.meta['published'].strftime('%m')
    ]
    if not month_posts:
        abort(404)
    sorted_posts = sorted(
        month_posts,
        reverse=False,
        key=lambda p: p.meta['published'],
    )
    month_string = calendar.month_name[int(month)]
    return render_template(
        'month.html',
        active=year,
        year=year,
        month_string=month_string,
        posts=sorted_posts,
    )


@posts_bp.route('/<year>/<month>/<day>/')
def day_view(year: str, month: str, day: str) -> ResponseReturnValue:
    day_posts = [
        p for p in posts.published_posts if year == p.meta['published'].strftime('%Y')
        and month == p.meta['published'].strftime('%m')
        and day == p.meta['published'].strftime('%d')
    ]
    if not day_posts:
        abort(404)
    month_string = calendar.month_name[int(month)]
    return render_template(
        'day.html',
        active=f'{year}-{month}-{day}',
        year=year,
        month_string=month_string,
        day=day,
        posts=day_posts,
    )
