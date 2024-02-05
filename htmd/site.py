from collections.abc import Iterator
import os
from pathlib import Path
import sys
import tomllib
import typing
import uuid

from bs4 import BeautifulSoup
from feedwerk.atom import AtomFeed
from flask import abort, Blueprint, Flask, render_template, Response, url_for
from flask.typing import ResponseReturnValue
from flask_flatpages import FlatPages, Page, pygments_style_defs
from flask_frozen import Freezer
from htmlmin import minify
from jinja2 import ChoiceLoader, FileSystemLoader

from .utils import set_post_metadata, valid_uuid


this_dir = Path(__file__).parent


def get_project_dir() -> Path:
    current_directory = Path.cwd()

    while not (current_directory / 'config.toml').is_file():
        parent_directory = current_directory.parent

        if current_directory == parent_directory:
            return Path.cwd()

        current_directory = parent_directory

    return current_directory


project_dir = get_project_dir()


try:
    with (project_dir / 'config.toml').open('rb') as config_file:
        htmd_config = tomllib.load(config_file)
except FileNotFoundError:
    msg = 'Can not find config.toml'
    sys.exit(msg)


# Flask configs are flat, config.toml is not
# Define the configuration keys and their default values
# 'Flask config': [section, key, default]
config_keys : dict[str, tuple[str, str, typing.Any]] = {
    'SITE_NAME': ('site', 'name', ''),
    'SITE_URL': ('site', 'url', ''),
    'SITE_LOGO': ('site', 'logo', ''),
    'SITE_DESCRIPTION': ('site', 'description', ''),
    'SITE_TWITTER': ('site', 'twitter', ''),
    'SITE_FACEBOOK': ('site', 'facebook', ''),
    'FACEBOOK_APP_ID': ('site', 'facebook_app_id', ''),

    'BUILD_FOLDER': ('folders', 'build', 'build'),
    'PAGES_FOLDER': ('folders', 'pages', 'pages'),
    'POSTS_FOLDER': ('folders', 'posts', 'posts'),
    'STATIC_FOLDER': ('folders', 'static', 'static'),
    'TEMPLATE_FOLDER': ('folders', 'templates', 'templates'),

    'POSTS_EXTENSION': ('posts', 'extension', '.md'),

    'PRETTY_HTML': ('html', 'pretty', False),
    'MINIFY_HTML': ('html', 'minify', False),

    'SHOW_AUTHOR': ('author', 'show', True),
    'DEFAULT_AUTHOR': ('author', 'default_name', ''),
    'DEFAULT_AUTHOR_TWITTER': ('author', 'default_twitter', ''),
    'DEFAULT_AUTHOR_FACEBOOK': ('author', 'default_facebook', ''),
}
app = Flask(
    __name__,
    # default templates
    template_folder=this_dir / 'example_site' / 'templates',
)
# Update app.config using the configuration keys
for flask_key, (table, key, default) in config_keys.items():
    app.config[flask_key] = htmd_config.get(table, {}).get(key, default)
app.static_folder = project_dir / app.config['STATIC_FOLDER']
assert app.static_folder is not None

# To avoid full paths in config.toml
app.config['FLATPAGES_ROOT'] = (
    project_dir / app.config['POSTS_FOLDER']
)
app.config['FREEZER_DESTINATION'] = (
    project_dir / app.config['BUILD_FOLDER']
)
app.config['FREEZER_REMOVE_EXTRA_FILES'] = True
# Allow build to be version controlled
app.config['FREEZER_DESTINATION_IGNORE'] = ['.git*', '.hg*']
app.config['FLATPAGES_EXTENSION'] = app.config['POSTS_EXTENSION']

if Path(app.static_folder).is_dir():
    app.config['INCLUDE_CSS'] = 'combined.min.css' in os.listdir(app.static_folder)
    app.config['INCLUDE_JS'] = 'combined.min.js' in os.listdir(app.static_folder)


posts = FlatPages(app)
published_posts = [p for p in posts if not p.meta.get('draft', False)]
freezer = Freezer(app)


SHOW_DRAFTS = False
def preview_drafts() -> None:
    global published_posts, SHOW_DRAFTS  # noqa: PLW0603
    SHOW_DRAFTS = True
    published_posts = [p for p in posts if 'published' in p.meta]


# Allow config settings (even new user created ones) to be used in templates
for key in app.config:
    app.jinja_env.globals[key] = app.config[key]


def truncate_post_html(post_html: str) -> str:
    return BeautifulSoup(post_html[:255], 'html.parser').prettify()


app.jinja_env.globals['truncate_post_html'] = truncate_post_html


# Use templates in user set template folder
# but fallback to app.template_folder (example_site/templates/)
assert app.jinja_loader is not None
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(project_dir / app.config['TEMPLATE_FOLDER']),
    app.jinja_loader,
])


MONTHS = {
    '01': 'January',
    '02': 'February',
    '03': 'March',
    '04': 'April',
    '05': 'May',
    '06': 'June',
    '07': 'July',
    '08': 'August',
    '09': 'September',
    '10': 'October',
    '11': 'November',
    '12': 'December',
}


pages = Blueprint(
    'pages',
    __name__,
    template_folder=project_dir / app.config['PAGES_FOLDER'],
)


@app.after_request
def format_html(response: Response) -> ResponseReturnValue:
    if response.mimetype == 'text/html':
        if app.config.get('PRETTY_HTML', False):
            response.data = BeautifulSoup(
                response.data,
                'html.parser',
            ).prettify()
        elif app.config.get('MINIFY_HTML', False):
            response.data = minify(response.data.decode('utf-8'))
    return response


@pages.route('/<path:path>/')
def page(path: str) -> ResponseReturnValue:
    # ensure page is from pages directory
    # otherwise this will load any templates in the template folder
    pages_folder = project_dir / app.config['PAGES_FOLDER']
    if not pages_folder.is_dir():
        abort(404)
    for page_path in pages_folder.iterdir():
        if path == page_path.stem:
            break
    else:
        abort(404)
    return render_template(path + '.html', active=path)


app.register_blueprint(pages)


# Will end up in the static directory
@app.route('/static/pygments.css')
def pygments_css() -> ResponseReturnValue:
    return pygments_style_defs('tango'), 200, {'Content-Type': 'text/css'}


@app.route('/')
def index() -> ResponseReturnValue:
    latest = sorted(published_posts, reverse=True, key=lambda p: p.meta['published'])
    return render_template('index.html', active='home', posts=latest[:4])


@app.route('/feed.atom')
def feed() -> ResponseReturnValue:
    name = app.config.get('SITE_NAME')
    subtitle = app.config.get('SITE_DESCRIPTION') or 'Recent Blog Posts'
    url = app.config.get('URL')
    atom = AtomFeed(
        feed_url=url_for('all_posts'),
        subtitle=subtitle,
        title=name,
        url=url,
    )
    for post in published_posts:
        url = url_for(
            'post',
            year=post.meta.get('published').strftime('%Y'),
            month=post.meta.get('published').strftime('%m'),
            day=post.meta.get('published').strftime('%d'),
            path=post.path,
        )

        post_datetime = post.meta.get('updated') or post.meta.get('published')
        atom.add(
            post.meta.get('title'),
            post.html,
            content_type='html',
            author=post.meta.get('author', app.config.get('DEFAULT_AUTHOR')),
            url=url,
            updated=post_datetime,
        )
    ret = atom.get_response()
    return ret


@app.route('/all/')
def all_posts() -> ResponseReturnValue:
    latest = sorted(published_posts, reverse=True, key=lambda p: p.meta['published'])
    return render_template('all_posts.html', active='posts', posts=latest)


def draft_and_not_shown(post: Page) -> bool:
    is_draft = 'draft' in post.meta
    return is_draft and not SHOW_DRAFTS and 'build' not in str(post.meta['draft'])


# If month and day are ints then Flask removes leading zeros
@app.route('/<year>/<month>/<day>/<path:path>/')
def post(year: str, month: str, day: str, path: str) -> ResponseReturnValue:
    if len(year) != 4 or len(month) != 2 or len(day) != 2:  # noqa: PLR2004
        abort(404)
    post = posts.get_or_404(path)
    if draft_and_not_shown(post):
        abort(404)
    date_str = f'{year}-{month}-{day}'
    if post.meta.get('published').strftime('%Y-%m-%d') != date_str:
        abort(404)
    return render_template('post.html', post=post)


@app.route('/draft/<post_uuid>/')
def draft(post_uuid: str) -> ResponseReturnValue:
    for post in posts:
        if str(post.meta.get('draft', '')).replace('build|', '') == post_uuid:
            return render_template('post.html', post=post)
    abort(404)  # noqa: RET503


@app.route('/tags/')
def all_tags() -> ResponseReturnValue:
    tag_counts: dict[str, int] = {}
    for post in published_posts:
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

@app.route('/tags/<string:tag>/')
def tag(tag: str) -> ResponseReturnValue:
    tagged = [p for p in posts if tag in p.meta.get('tags', [])]
    if not tagged:
        abort(404)
    if not SHOW_DRAFTS and no_posts_shown(tagged):
        abort(404)
    if SHOW_DRAFTS:
        tagged_published = tagged
    else:
        tagged_published = [p for p in tagged if 'draft' not in p.meta]
    sorted_posts = sorted(
        tagged_published,
        reverse=True,
        key=lambda p: p.meta.get('published'),
    )
    return render_template('tag.html', posts=sorted_posts, tag=tag)


@app.route('/author/<author>/')
def author(author: str) -> ResponseReturnValue:
    # if the author has a draft build
    # page is served without displaying posts
    # so no 404 when for the link from the draft
    posts_author = [p for p in posts if author == p.meta.get('author', '')]

    if not posts_author:
        abort(404)

    if not SHOW_DRAFTS and no_posts_shown(posts_author):
        abort(404)
    if SHOW_DRAFTS:
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


@app.route('/404.html')
def not_found() -> ResponseReturnValue:
    return render_template('404.html')


@app.route('/<int:year>/')
def year_view(year: int) -> ResponseReturnValue:
    year_str = str(year)
    if len(year_str) != len('YYYY'):
        abort(404)
    year_posts = [
        p for p in published_posts if year_str == p.meta['published'].strftime('%Y')
    ]
    if not year_posts:
        abort(404)
    sorted_posts = sorted(
        year_posts,
        reverse=False,
        key=lambda p: p.meta.get('published'),
    )
    return render_template('year.html', year=year_str, posts=sorted_posts)


@app.route('/<year>/<month>/')
def month_view(year: str, month: str) -> ResponseReturnValue:
    month_posts = [
        p for p in published_posts if year == p.meta.get('published').strftime('%Y')
        and month == p.meta.get('published').strftime('%m')
    ]
    if not month_posts:
        abort(404)
    sorted_posts = sorted(
        month_posts,
        reverse=False,
        key=lambda p: p.meta.get('published'),
    )
    month_string = MONTHS[month]
    return render_template(
        'month.html',
        year=year,
        month_string=month_string,
        posts=sorted_posts,
    )


@app.route('/<year>/<month>/<day>/')
def day_view(year: str, month: str, day: str) -> ResponseReturnValue:
    day_posts = [
        p for p in published_posts if year == p.meta.get('published').strftime('%Y')
        and month == p.meta.get('published').strftime('%m')
        and day == p.meta.get('published').strftime('%d')
    ]
    if not day_posts:
        abort(404)
    month_string = MONTHS[month]
    return render_template(
        'day.html',
        year=year,
        month_string=month_string,
        day=day,
        posts=day_posts,
    )


@app.errorhandler(404)
def page_not_found(_e: Exception | int) -> ResponseReturnValue:
    return render_template('404.html'), 404


# Telling Frozen-Flask about routes that are not linked to in templates
@freezer.register_generator  # type: ignore[no-redef]
def year_view() -> Iterator[dict]:  # noqa: F811
    for post in published_posts:
        yield {
            'year': post.meta.get('published').year,
        }


@freezer.register_generator  # type: ignore[no-redef]
def month_view() -> Iterator[dict]:  # noqa: F811
    for post in published_posts:
        yield {
            'month': post.meta.get('published').strftime('%m'),
            'year': post.meta.get('published').year,
        }


@freezer.register_generator  # type: ignore[no-redef]
def day_view() -> Iterator[dict]:  # noqa: F811
    for post in published_posts:
        yield {
            'day': post.meta.get('published').strftime('%d'),
            'month': post.meta.get('published').strftime('%m'),
            'year': post.meta.get('published').year,
        }


@freezer.register_generator  # type: ignore[no-redef]
def draft() -> Iterator[dict]:  # noqa: F811
    draft_posts = [
        p for p in posts
        if 'draft' in p.meta and 'build' in str(p.meta['draft'])
    ]
    for post in draft_posts:
        if not valid_uuid(post.meta['draft'].replace('build|', '')):
            post.meta['draft'] = 'build|' + str(uuid.uuid4())
            set_post_metadata(app, post, 'draft', post.meta['draft'])
        yield {
            'post_uuid': post.meta['draft'].replace('build|', ''),
        }


@freezer.register_generator  # type: ignore[no-redef]
def page() -> Iterator[str]:  # noqa: F811
    pages_folder = project_dir / app.config['PAGES_FOLDER']
    if not pages_folder.is_dir():
        return
    for page in pages_folder.iterdir():
        # Need to create for pages.page
        # Since this route is in a different Blueprint
        # Using the URL works
        yield f'/{page.stem}/'
