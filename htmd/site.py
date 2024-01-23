from collections.abc import Iterator
import os
from pathlib import Path
import sys
import tomllib
from typing import TypedDict

from bs4 import BeautifulSoup
from feedwerk.atom import AtomFeed
from flask import abort, Blueprint, Flask, render_template, Response, url_for
from flask_flatpages import FlatPages, pygments_style_defs
from flask_frozen import Freezer
from htmlmin import minify
from jinja2 import ChoiceLoader, FileSystemLoader, TemplateNotFound


this_dir = Path(__file__).parent


def get_project_dir() -> Path:
    current_directory = Path.cwd()

    while True:
        file_path = current_directory / 'config.toml'

        if file_path.is_file():
            return current_directory

        # Move to the parent directory
        parent_directory = current_directory.parent

        # If the current and parent directories are the same, break the loop
        if current_directory == parent_directory:
            break

        current_directory = parent_directory

    return Path.cwd()


project_dir = get_project_dir()

app = Flask(
    __name__,
    static_folder=project_dir / 'static',
    template_folder=this_dir / 'example_site' / 'templates',
)


try:
    with (project_dir / 'config.toml').open('rb') as config_file:
        htmd_config = tomllib.load(config_file)
except FileNotFoundError:
    msg = 'Can not find config.toml'
    sys.exit(msg)

# Flask configs are flat, config.toml is not
# Define the configuration keys and their default values
# 'Flask config': [section, key, default]
config_keys = {
    'SITE_NAME': ['site', 'name', ''],
    'SITE_URL': ['site', 'url', ''],
    'SITE_LOGO': ['site', 'logo', ''],
    'SITE_DESCRIPTION': ['site', 'description', ''],
    'SITE_TWITTER': ['site', 'twitter', ''],
    'SITE_FACEBOOK': ['site', 'facebook', ''],
    'FACEBOOK_APP_ID': ['site', 'facebook_app_id', ''],
    'STATIC_FOLDER': ['folders', 'static', 'static'],
    'POSTS_FOLDER': ['folders', 'posts', 'posts'],
    'PAGES_FOLDER': ['folders', 'pages', 'pages'],
    'BUILD_FOLDER': ['folders', 'build', 'build'],
    'POSTS_EXTENSION': ['posts', 'extension', '.md'],
    'PRETTY_HTML': ['html', 'pretty', False],
    'MINIFY_HTML': ['html', 'minify', False],
    'SHOW_AUTHOR': ['author', 'show', True],
    'DEFAULT_AUTHOR': ['author', 'default_name', ''],
    'DEFAULT_AUTHOR_TWITTER': ['author', 'default_twitter', ''],
    'DEFAULT_AUTHOR_FACEBOOK': ['author', 'default_facebook', ''],
}

# Update app.config using the configuration keys
for flask_key, (table, key, default) in config_keys.items():
    app.config[flask_key] = htmd_config.get(table, {}).get(key, default)


# To avoid full paths in config.toml
app.config['FLATPAGES_ROOT'] = (
    project_dir / app.config.get('POSTS_FOLDER')
)
app.config['FREEZER_DESTINATION'] = (
    project_dir / app.config.get('BUILD_FOLDER')
)
app.config['FREEZER_REMOVE_EXTRA_FILES'] = False
app.config['FLATPAGES_EXTENSION'] = app.config.get('POSTS_EXTENSION')

app.config['INCLUDE_CSS'] = 'combined.min.css' in os.listdir(app.static_folder)
app.config['INCLUDE_JS'] = 'combined.min.js' in os.listdir(app.static_folder)


posts = FlatPages(app)
freezer = Freezer(app)

# Allow config settings (even new user created ones) to be used in templates
for key in app.config:
    app.jinja_env.globals[key] = app.config[key]


def truncate_post_html(post_html: str) -> str:
    return BeautifulSoup(post_html[:255], 'html.parser').prettify()


app.jinja_env.globals['truncate_post_html'] = truncate_post_html


# Include current htmd site templates
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(project_dir / 'templates/'),
    app.jinja_loader,
])

MONTHS = {
    '01': 'January',
    '02': 'February',
    '3': 'March',
    '4': 'April',
    '5': 'May',
    '6': 'June',
    '7': 'July',
    '8': 'August',
    '9': 'September',
    '10': 'October',
    '11': 'November',
    '12': 'December',
}

pages = Blueprint(
    'pages',
    __name__,
    template_folder=project_dir / app.config.get('PAGES_FOLDER'),
)


@app.after_request
def format_html(response: Response) -> Response:
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
def page(path: str) -> Response:
    try:
        return render_template(path + '.html', active=path)
    except TemplateNotFound:
        abort(404)


app.register_blueprint(pages)


# Will end up in the static directory
@app.route('/static/pygments.css')
def pygments_css() -> Response:
    return pygments_style_defs('tango'), 200, {'Content-Type': 'text/css'}


@app.route('/')
def index() -> Response:
    latest = sorted(posts, reverse=True, key=lambda p: p.meta.get('published'))
    return render_template('index.html', active='home', posts=latest[:4])


@app.route('/feed.atom')
def feed() -> Response:
    name = app.config.get('SITE_NAME')
    subtitle = app.config.get('SITE_DESCRIPTION') or 'Recent Blog Posts'
    url = app.config.get('URL')
    atom = AtomFeed(
        feed_url=url_for('all_posts'),
        subtitle=subtitle,
        title=name,
        url=url,
    )
    for post in posts:
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
def all_posts() -> Response:
    latest = sorted(posts, reverse=True, key=lambda p: p.meta.get('published'))
    return render_template('all_posts.html', active='posts', posts=latest)


# If month and day are ints then Flask removes leading zeros
@app.route('/<year>/<month>/<day>/<path:path>/')
def post(year: str, month: str, day:str, path: str) -> Response:
    if len(year) != 4 or len(month) != 2 or len(day) != 2:  # noqa: PLR2004
        abort(404)
    post = posts.get_or_404(path)
    date_str = f'{year}-{month}-{day}'
    if str(post.meta.get('published')) != date_str:
        abort(404)
    return render_template('post.html', post=post)


class TagDict(TypedDict):
    tag: str
    count: int


def tag_in_list(list_of_tags: [TagDict], tag: str) -> bool:
    return any(i['tag'] == tag for i in list_of_tags)


def increment_tag_count(list_of_tags: [TagDict], tag: str) -> [TagDict]:
    for i in list_of_tags:
        if i['tag'] == tag:
            i['count'] += 1
    return list_of_tags


@app.route('/tags/')
def all_tags() -> Response:
    tags = []
    for post in posts:
        for tag in post.meta.get('tags', []):
            if tag_in_list(tags, tag) is False:
                tags.append({'tag': tag, 'count': 1})
            else:
                increment_tag_count(tags, tag)
    return render_template('all_tags.html', active='tags', tags=tags)


@app.route('/tags/<string:tag>/')
def tag(tag: str) -> Response:
    tagged = [p for p in posts if tag in p.meta.get('tags', [])]
    sorted_posts = sorted(
        tagged,
        reverse=True,
        key=lambda p: p.meta.get('published'),
    )
    return render_template('tag.html', posts=sorted_posts, tag=tag)


@app.route('/author/<author>/')
def author(author: str) -> Response:
    author_posts = [p for p in posts if author == p.meta.get('author', '')]
    sorted_posts = sorted(
        author_posts,
        reverse=True,
        key=lambda p: p.meta.get('published'),
    )
    return render_template(
        'author.html',
        active='author',
        author=author,
        posts=sorted_posts,
    )


@app.route('/404.html')
def not_found() -> Response:
    return render_template('404.html')


@app.route('/<int:year>/')
def year_view(year: int) -> Response:
    year = str(year)
    if len(year) != len('YYYY'):
        abort(404)
    year_posts = [
        p for p in posts if year == p.meta.get('published', []).strftime('%Y')
    ]
    if not year_posts:
        abort(404)
    sorted_posts = sorted(
        year_posts,
        reverse=False,
        key=lambda p: p.meta.get('published'),
    )
    return render_template('year.html', year=year, posts=sorted_posts)


@app.route('/<year>/<month>/')
def month_view(year: str, month: str) -> Response:
    month_posts = [
        p for p in posts if year == p.meta.get('published').strftime('%Y')
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
def day_view(year: str, month: str, day: str) -> Response:
    day_posts = [
        p for p in posts if year == p.meta.get('published').strftime('%Y')
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
def page_not_found(_e: Exception | int) -> Response:
    return render_template('404.html'), 404


# Telling Frozen-Flask about routes that are not linked to in templates
@freezer.register_generator
def year_view() -> Iterator[dict]:  # noqa: F811
    for post in posts:
        yield {
            'year': post.meta.get('published').year,
        }


@freezer.register_generator
def month_view() -> Iterator[dict]:  # noqa: F811
    for post in posts:
        yield {
            'month': post.meta.get('published').strftime('%m'),
            'year': post.meta.get('published').year,
        }


@freezer.register_generator
def day_view() -> Iterator[dict]:  # noqa: F811
    for post in posts:
        yield {
            'day': post.meta.get('published').strftime('%d'),
            'month': post.meta.get('published').strftime('%m'),
            'year': post.meta.get('published').year,
        }
