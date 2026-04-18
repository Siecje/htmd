import calendar
from collections.abc import Iterator
import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from bs4.element import NavigableString, PageElement
from feedwerk.atom import AtomFeed
from flask import (
    abort,
    Blueprint,
    current_app,
    Flask,
    jsonify,
    render_template,
    Response,
    url_for,
)
from flask.blueprints import BlueprintSetupState
from flask.typing import ResponseReturnValue
from flask_flatpages import FlatPages, Page
from werkzeug.routing import BaseConverter, Map

from ..password_protect import encrypt_post


class RegexConverter(BaseConverter):
    def __init__(self, url_map: Map, *items: str) -> None:
        super().__init__(url_map)
        self.regex = items[0]


class Posts(FlatPages):
    def __init__(self, app: Flask | None = None) -> None:
        super().__init__(app)
        self.show_drafts: bool = False
        self.published_posts: list[Page] = []
        self._app = app

    def __iter__(self) -> Iterator[Page]:
        """Iterate on a snapshot of all :class:`Page` objects."""
        return iter(list(self._pages.values()))

    def reload(self, *, show_drafts: bool | None = None) -> None:
        super().reload()
        if show_drafts is not None:
            self.show_drafts = show_drafts

        if not self._app:
            return
        with self._app.app_context():
            new_published_posts = [
                p for p in self
                if 'published' in p.meta
                and hasattr(p.meta['published'], 'year')
                and (self.show_drafts or not p.meta.get('draft', False))
            ]
        self.published_posts = new_published_posts


def get_posts(app: Flask | None = None) -> Posts:
    app_ = app or current_app
    ret = app_.extensions['flatpages'][None]
    assert isinstance(ret, Posts)
    return ret


def truncate_post_html(post_html: str, limit: int = 255) -> str:
    soup = BeautifulSoup(post_html, 'html.parser')
    all_text_nodes = list(soup.find_all(string=True))
    full_text_len = len(soup.get_text())

    current_count = 0
    suffix = '...'
    for node in all_text_nodes:
        node_len = len(node)

        if current_count + node_len > limit:
            if full_text_len - limit <= len(suffix):
                return soup.decode()

            # truncate current node
            chars_to_keep = limit - current_count
            new_content = node[:chars_to_keep].rstrip() + suffix
            new_node = NavigableString(new_content)
            node.replace_with(new_node)

            # prune the tree
            curr: PageElement | None = new_node
            while curr and curr != soup:
                for sibling in list(curr.next_siblings):
                    sibling.extract()
                curr = curr.parent
            break

        current_count += node_len

    ret = soup.decode()
    return ret


def on_load(state: BlueprintSetupState) -> None:
    # state.app is the actual Flask app instance
    state.app.jinja_env.globals['truncate_post_html'] = truncate_post_html
    # add regex type to routes
    state.app.url_map.converters['regex'] = RegexConverter


def feed() -> Response:
    name = current_app.config.get('SITE_NAME')
    subtitle = (
        current_app.config.get('SITE_DESCRIPTION')
        or 'Recent Blog Posts'
    )
    feed_url = url_for('posts.feed', _external=True)
    url = url_for('posts.all_posts', _external=True)
    atom = AtomFeed(
        feed_url=feed_url,
        generator=(None, None, None),
        subtitle=subtitle,
        title=name,
        url=url,
    )

    include_full_text: bool = current_app.config['POSTS_FEED_FULL_TEXT']
    truncate_limit: int = current_app.config['POSTS_FEED_TRUNCATE_LIMIT']

    posts = get_posts()
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
        author = post.meta.get(
            'author',
            current_app.config.get('DEFAULT_AUTHOR'),
        )
        if include_full_text:
            content = post.html
        else:
            content = truncate_post_html(post.html, limit=truncate_limit)
        atom.add(
            post.meta.get('title'),
            content,
            author=author,
            content_type='html',
            published=published,
            updated=post_datetime,
            url=url,
        )
    ret = atom.get_response()
    return ret


def posts_json() -> ResponseReturnValue:
    posts = get_posts()
    with current_app.app_context():
        urls = [
            '/{year}/{month}/{day}/{path}/'.format(
                year=post.meta['published'].strftime('%Y'),
                month=post.meta['published'].strftime('%m'),
                day=post.meta['published'].strftime('%d'),
                path=post.path,
            )
            for post in posts.published_posts
        ]
    return jsonify(urls)


def all_posts() -> ResponseReturnValue:
    posts = get_posts()
    latest = sorted(
        posts.published_posts,
        reverse=True,
        key=lambda p: p.meta['published'],
    )
    return render_template('all_posts.html', active='posts', posts=latest)


def draft_and_not_shown(post: Page) -> bool:
    posts = get_posts()
    show_drafts = posts.show_drafts
    is_draft = 'draft' in post.meta
    return (
        is_draft
        and not show_drafts
        and 'build' not in str(post.meta['draft'])
    )


def render_password_protected_post(post: Page) -> ResponseReturnValue:
    (
        encrypted_content,
        encrypted_title,
        encrypted_subtitle,
    ) = encrypt_post(
        post.html,
        post.meta['title'],
        post.meta.get('subtitle'),
        post.meta['password'],
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
def post(year: str, month: str, day: str, path: str) -> ResponseReturnValue:
    date_str = f'{year}-{month}-{day}'
    posts = get_posts()
    post = posts.get(path)
    if not post:
        path = str(Path('password-protect') / path)
        post = posts.get_or_404(path)
    if draft_and_not_shown(post):
        abort(404)
    published = post.meta.get(
        'published',
        datetime.datetime.now(tz=datetime.UTC),
    )
    if published.strftime('%Y-%m-%d') != date_str:
        abort(404)
    if post.meta.get('password'):
        return render_password_protected_post(post)
    return render_template('post.html', active=path, post=post)


def draft(post_uuid: str) -> ResponseReturnValue:
    posts = get_posts()
    for post in posts:
        if str(post.meta.get('draft', '')).replace('build|', '') == post_uuid:
            break
    else:
        abort(404)
    if post.meta.get('password'):
        return render_password_protected_post(post)
    return render_template(
        'post.html',
        active=post.path,
        post=post,
    )


def all_tags() -> ResponseReturnValue:
    tag_counts: dict[str, int] = {}
    posts = get_posts()
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


def tag(tag: str) -> ResponseReturnValue:
    posts = get_posts()
    # Not using published_posts because build draft can link to a tag
    # and build will fail if link is 404
    tagged = [
        p
        for p in posts
        if tag in p.meta.get('tags', [])
    ]
    if not tagged:
        abort(404)
    if not posts.show_drafts and no_posts_shown(tagged):
        abort(404)
    if posts.show_drafts:
        tagged_published = tagged
    else:
        tagged_published = [
            p
            for p in tagged
            if (
                'draft' not in p.meta
                or p.meta['draft'] is False
            )
        ]
    today = datetime.datetime.now(tz=datetime.UTC)
    sorted_posts = sorted(
        tagged_published,
        reverse=True,
        key=lambda p: p.meta.get('published', today),
    )
    return render_template(
        'tag.html',
        active=tag,
        posts=sorted_posts,
        tag=tag,
        today=today,
    )


def author(author: str) -> ResponseReturnValue:
    # if the author has a draft build
    # page is served without displaying posts
    # so no 404 when for the link from the draft
    posts = get_posts()
    posts_author = [
        p
        for p in posts
        if author == p.meta.get('author', '')
    ]

    if not posts_author:
        abort(404)

    if not posts.show_drafts and no_posts_shown(posts_author):
        abort(404)
    if posts.show_drafts:
        posts_author_published = posts_author
    else:
        posts_author_published = [
            p
            for p in posts_author
            if (
                'draft' not in p.meta
                or p.meta['draft'] is False
            )
        ]

    today = datetime.datetime.now(tz=datetime.UTC)
    posts_sorted = sorted(
        posts_author_published,
        reverse=True,
        key=lambda p: p.meta.get('published', today),
    )
    return render_template(
        'author.html',
        active='author',
        author=author,
        posts=posts_sorted,
        today=today,
    )


def year_view(year: str) -> ResponseReturnValue:
    posts = get_posts()
    year_posts = [
        p
        for p in posts.published_posts
        if year == p.meta['published'].strftime('%Y')
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
        active=year,
        year=year,
        posts=sorted_posts,
    )


def month_view(year: str, month: str) -> ResponseReturnValue:
    posts = get_posts()
    month_posts = [
        p
        for p in posts.published_posts
        if year == p.meta['published'].strftime('%Y')
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


def day_view(year: str, month: str, day: str) -> ResponseReturnValue:
    posts = get_posts()
    day_posts = [
        p
        for p in posts.published_posts
        if year == p.meta['published'].strftime('%Y')
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


def create_posts_blueprint(
    url_prefix: str,
    all_posts_path: str,
    *,
    random_post_enabled: bool = False,
) -> tuple[Blueprint, Posts]:
    """
    Create a fresh Blueprint and Posts instance for an app.

    `url_prefix` is the base string prepended to all routes

    `all_posts_path` is the URL path for the "all posts" view

    `random_post_enabled` determines if the JSON posts endpoint is registered.

    Returns (blueprint, posts_instance).
    """
    bp = Blueprint('posts', __name__)
    posts = Posts()

    # Define reusable route components
    re_year = r'<regex("\d{4}"):year>'
    re_month = r'<regex("\d{2}"):month>'
    re_day = r'<regex("\d{2}"):day>'

    bp.record_once(on_load)

    prefix = '/' + url_prefix.strip('/')
    if prefix == '/':
        prefix = ''

    bp.add_url_rule(f'{prefix}/feed.atom', endpoint='feed', view_func=feed)

    if random_post_enabled:
        bp.add_url_rule(
            f'{prefix}/posts.json',
            endpoint='posts_json',
            view_func=posts_json,
        )

    # Individual Post View
    bp.add_url_rule(
        f'{prefix}/{re_year}/{re_month}/{re_day}/<path:path>/',
        endpoint='post',
        view_func=post,
    )

    bp.add_url_rule(f'{prefix}/draft/<post_uuid>/', endpoint='draft', view_func=draft)
    bp.add_url_rule(f'{prefix}/tags/', endpoint='all_tags', view_func=all_tags)
    bp.add_url_rule(f'{prefix}/tags/<string:tag>/', endpoint='tag', view_func=tag)
    bp.add_url_rule(f'{prefix}/author/<author>/', endpoint='author', view_func=author)

    # Archive Views
    bp.add_url_rule(
        f'{prefix}/{re_year}/',
        endpoint='year_view',
        view_func=year_view,
    )
    bp.add_url_rule(
        f'{prefix}/{re_year}/{re_month}/',
        endpoint='month_view',
        view_func=month_view,
    )
    bp.add_url_rule(
        f'{prefix}/{re_year}/{re_month}/{re_day}/',
        endpoint='day_view',
        view_func=day_view,
    )

    # Register the all_posts view at the configurable base path.
    if all_posts_path == '':
        all_posts_path = prefix + '/'

    bp.add_url_rule(
        all_posts_path,
        endpoint='all_posts',
        view_func=all_posts,
    )

    return bp, posts
