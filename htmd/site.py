import datetime
import os
import sys

from bs4 import BeautifulSoup
from feedwerk.atom import AtomFeed
from flask import (
    abort, Blueprint, Flask, render_template, make_response, url_for
)
from flask_flatpages import FlatPages, pygments_style_defs
from flask_frozen import Freezer
from htmlmin import minify
from jinja2 import TemplateNotFound, ChoiceLoader, FileSystemLoader


this_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=os.path.join(os.getcwd(), 'static'),
    template_folder=os.path.join(this_dir, 'example_site', 'templates'),
)


try:
    app.config.from_pyfile(os.path.join(os.getcwd(), 'config.py'))
except IOError:
    print('Can not find config.py')
    sys.exit(1)

# To avoid full paths in config.py
app.config['FLATPAGES_ROOT'] = os.path.join(
    os.getcwd(), app.config.get('POSTS_FOLDER')
)
app.config['FREEZER_DESTINATION'] = os.path.join(
    os.getcwd(), app.config.get('BUILD_FOLDER')
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


def truncate_post_html(post_html):
    return BeautifulSoup(post_html[:255], 'html.parser').prettify()


app.jinja_env.globals['truncate_post_html'] = truncate_post_html


# Include current htmd site templates
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(os.getcwd(), 'templates/')),
    app.jinja_loader
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
    template_folder=os.path.join(os.getcwd(), app.config.get('PAGES_FOLDER'))
)


@app.after_request
def format_html(response):
    if response.mimetype == 'text/html':
        if app.config.get('PRETTY_HTML', False):
            response.data = BeautifulSoup(
                response.data,
                'html.parser'
            ).prettify()
        elif app.config.get('MINIFY_HTML', False):
            response.data = minify(response.data.decode('utf-8'))
    return response


@pages.route('/<path:path>/')
def page(path):
    try:
        return render_template(path + '.html', active=path)
    except TemplateNotFound:
        abort(404)


app.register_blueprint(pages)


# Will end up in the static directory
@app.route('/static/pygments.css')
def pygments_css():
    return pygments_style_defs('tango'), 200, {'Content-Type': 'text/css'}


@app.route('/')
def index():
    latest = sorted(posts, reverse=True, key=lambda p: p.meta.get('published'))
    return render_template('index.html', active='home', posts=latest[:4])


@app.route('/feed.atom/')
def feed():
    name = app.config.get('SITE_NAME')
    subtitle = app.config.get('SITE_DESCRIPTION') or 'Recent Blog Posts'
    url = app.config.get('URL')
    feed = AtomFeed(
        title=name,
        subtitle=subtitle,
        feed_url=url_for('all_posts'),
        url=url
    )
    for post in posts:
        url = url_for(
            'post',
            year=post.meta.get('published').strftime('%Y'),
            month=post.meta.get('published').strftime('%m'),
            day=post.meta.get('published').strftime('%d'),
            path=post.path
        )
        updated = datetime.datetime.combine(
            post.meta.get('updated') or post.meta.get('published'),
            datetime.time()
        )
        feed.add(
            post.meta.get('title'), post.html, content_type='html',
            author=post.meta.get('author', app.config.get('DEFAULT_AUTHOR')),
            url=url,
            updated=updated,
        )
    return make_response(feed.to_string().encode('utf-8') + b'\n')


@app.route('/all/')
def all_posts():
    latest = sorted(posts, reverse=True, key=lambda p: p.meta.get('published'))
    return render_template('all_posts.html', active='posts', posts=latest)


# If month and day are ints then Flask removes leading zeros
@app.route('/<year>/<month>/<day>/<path:path>/')
def post(year, month, day, path):
    if len(year) != 4 or len(month) != 2 or len(day) != 2:
        abort(404)
    post = posts.get_or_404(path)
    date_str = f'{year}-{month}-{day}'
    if str(post.meta.get('published')) != date_str:
        abort(404)
    return render_template('post.html', post=post)


def tag_in_list(list_of_tags, tag):
    for i in list_of_tags:
        if i['tag'] == tag:
            return True
    return False


def increment_tag_count(list_of_tags, tag):
    for i in list_of_tags:
        if i['tag'] == tag:
            i['count'] += 1
    return list_of_tags


@app.route('/tags/')
def all_tags():
    tags = []
    for post in posts:
        for tag in post.meta.get('tags', []):
            if tag_in_list(tags, tag) is False:
                tags.append({'tag': tag, 'count': 1})
            else:
                increment_tag_count(tags, tag)
    return render_template('all_tags.html', active='tags', tags=tags)


@app.route('/tags/<string:tag>/')
def tag(tag):
    tagged = [p for p in posts if tag in p.meta.get('tags', [])]
    sorted_posts = sorted(tagged, reverse=True,
                          key=lambda p: p.meta.get('published'))
    return render_template('tag.html', posts=sorted_posts, tag=tag)


@app.route('/author/<author>/')
def author(author):
    author_posts = [p for p in posts if author == p.meta.get('author', '')]
    sorted_posts = sorted(author_posts, reverse=True,
                          key=lambda p: p.meta.get('published'))
    return render_template(
        'author.html',
        active='author',
        author=author,
        posts=sorted_posts
    )


@app.route('/404.html')
def not_found():
    return render_template('404.html')


@app.route('/<int:year>/')
def year(year):
    year = str(year)
    if len(year) != 4:
        abort(404)
    year_posts = [
        p for p in posts if year == p.meta.get('published', []).strftime('%Y')
    ]
    if not year_posts:
        abort(404)
    sorted_posts = sorted(year_posts, reverse=False,
                          key=lambda p: p.meta.get('published'))
    return render_template('year.html', year=year, posts=sorted_posts)


@app.route('/<year>/<month>/')
def month(year, month):
    month_posts = [
        p for p in posts if year == p.meta.get('published').strftime('%Y')
        and month == p.meta.get('published').strftime('%m')
    ]
    if not month_posts:
        abort(404)
    sorted_posts = sorted(month_posts, reverse=False,
                          key=lambda p: p.meta.get('published'))
    month_string = MONTHS[month]
    return render_template(
        'month.html',
        year=year,
        month_string=month_string,
        posts=sorted_posts
    )


@app.route('/<year>/<month>/<day>/')
def day(year, month, day):
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
def page_not_found(e):
    return render_template('404.html'), 404


# Telling Frozen-Flask about routes that are not linked to in templates
@freezer.register_generator
def year():
    for post in posts:
        yield {'year': post.meta.get('published').year}


@freezer.register_generator
def month():
    for post in posts:
        yield {'year': post.meta.get('published').year,
               'month': post.meta.get('published').strftime('%m')}


@freezer.register_generator
def day():
    for post in posts:
        yield {'year': post.meta.get('published').year,
               'month': post.meta.get('published').strftime('%m'),
               'day': post.meta.get('published').strftime('%d')}
