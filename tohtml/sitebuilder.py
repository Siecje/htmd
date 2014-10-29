import os
import sys
from flask import Flask, render_template, Blueprint, abort
from jinja2 import TemplateNotFound, ChoiceLoader, FileSystemLoader
from werkzeug.exceptions import abort
from flask.ext.flatpages import FlatPages
from flask_frozen import Freezer

app = Flask(__name__)
app.config.from_pyfile(os.path.join(os.getcwd(), 'config.py'))
posts = FlatPages(app)
freezer = Freezer(app)

app.jinja_env.globals['SITE_NAME'] = app.config['SITE_NAME']
app.jinja_env.globals['SHOW_AUTHOR'] = app.config['SHOW_AUTHOR']

app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(os.getcwd(), 'templates/')),
    app.jinja_loader
])

MONTHS = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}

pages = Blueprint('pages', __name__, template_folder=os.path.join(os.getcwd(), 'pages/'))

@pages.route('/<path:path>/')
def page(path):
    try:
        return render_template(path + '.html')
    except TemplateNotFound:
        abort(404)

app.register_blueprint(pages)


@app.route('/')
def index():
    latest = sorted(posts, reverse=True, key=lambda p: p.meta.get('date'))
    return render_template('index.html', posts=latest[:4])


@app.route('/all/')
def all_posts():
    latest = sorted(posts, reverse=True, key=lambda p: p.meta.get('date'))
    return render_template('all_posts.html', posts=latest)


@app.route('/<int:year>/<int:month>/<int:day>/<path:path>/')
def post(year, month, day, path):
    post = posts.get_or_404(path)
    date = '%04d-%02d-%02d' % (year, month, day)
    if str(post.meta.get('date')) != date:
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
    return render_template('all_tags.html', tags=tags)


@app.route('/tags/<string:tag>/')
def tag(tag):
    tagged = [p for p in posts if tag in p.meta.get('tags', [])]
    sorted_posts = sorted(tagged, reverse=True,
        key=lambda p: p.meta.get('date'))
    return render_template('tag.html', posts=sorted_posts, tag=tag)


@app.route('/author/<author>/')
def author(author):
    author_posts = [p for p in posts if author == p.meta.get('author', '')]
    sorted_posts = sorted(author_posts, reverse=True,
        key=lambda p: p.meta.get('date'))
    return render_template('author.html', author=author, posts=sorted_posts)


@app.route('/<int:year>/')
def year(year):
    year_posts = [p for p in posts if year == p.meta.get('date', []).year]
    sorted_posts = sorted(year_posts, reverse=False,
        key=lambda p: p.meta.get('date'))
    return render_template('year.html', year=year, posts=sorted_posts)


@app.route('/<int:year>/<int:month>/')
def month(year, month):
    month_posts = [p for p in posts if year == p.meta.get('date').year and month == p.meta.get('date').month == month]
    sorted_posts = sorted(month_posts, reverse=False,
        key=lambda p: p.meta.get('date'))
    month_string = MONTHS[month]
    return render_template('month.html', year=year, month_string=month_string, posts=sorted_posts)


@app.route('/<int:year>/<int:month>/<int:day>/')
def day(year, month, day):
    day_posts = [p for p in posts if year == p.meta.get('date').year and month == p.meta.get('date').month == month]
    month_string = MONTHS[month]
    return render_template('day.html', year=year, month_string=month_string, day=day, posts=day_posts)


# Telling Frozen-Flask about routes that are not linked to in templates
@freezer.register_generator
def year():
    for post in posts:
        yield {'year': post.meta.get('date').year}


@freezer.register_generator
def month():
    for post in posts:
        yield {'year': post.meta.get('date').year,
              'month': post.meta.get('date').month}


@freezer.register_generator
def day():
    for post in posts:
        yield {'year': post.meta.get('date').year,
              'month': post.meta.get('date').month,
              'day': post.meta.get('date').day}
