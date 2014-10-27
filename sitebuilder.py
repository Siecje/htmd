import sys
from flask import Flask, render_template, Blueprint, abort
from jinja2 import TemplateNotFound
from werkzeug.exceptions import abort
from flask.ext.flatpages import FlatPages
from flask_frozen import Freezer

app = Flask(__name__)
app.config.from_object('config')
posts = FlatPages(app)
freezer = Freezer(app)

app.jinja_env.globals['SITE_NAME'] = app.config['SITE_NAME']
app.jinja_env.globals['SHOW_AUTHOR'] = app.config['SHOW_AUTHOR']

MONTHS = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}

pages = Blueprint('pages', __name__, template_folder='pages')

@pages.route('/<path:path>')
def page(path):
    try:
        return render_template(path + '.html')
    except TemplateNotFound:
        abort(404)

app.register_blueprint(pages)


@app.route('/')
def index():
    return render_template('index.html', posts=posts)


@app.route('/all/')
def all_posts():
    return render_template('all_posts.html', posts=posts)


@app.route('/<int:year>/<int:month>/<int:day>/<path:path>/')
def post(year, month, day, path):
    post = posts.get_or_404(path)
    date = '%04d-%02d-%02d' % (year, month, day)
    if str(post.meta.get('date')) != date:
        abort(404)
    return render_template('post.html', post=post)


@app.route('/tags/')
def all_tags():
    tags = []
    for post in posts:
        for tag in post.meta.get('tags', []):
            if tag not in tags:
                tags.append(tag)
    return render_template('all_tags.html', tags=tags)


@app.route('/tags/<string:tag>/')
def tag(tag):
    tagged = [p for p in posts if tag in p.meta.get('tags', [])]
    return render_template('tag.html', posts=tagged, tag=tag)


@app.route('/author/<author>/')
def author(author):
    author_posts = [p for p in posts if author == p.meta.get('author', '')]
    return render_template('author.html', author=author, posts=author_posts)


@app.route('/<int:year>/')
def year(year):
    year_posts = [p for p in posts if year == p.meta.get('date', []).year]
    return render_template('year.html', year=year, posts=year_posts)


@app.route('/<int:year>/<int:month>/')
def month(year, month):
    month_posts = [p for p in posts if year == p.meta.get('date').year and month == p.meta.get('date').month == month]
    month_string = MONTHS[month]
    return render_template('month.html', year=year, month_string=month_string, posts=month_posts)


@app.route('/<int:year>/<int:month>/<int:day>/')
def day(year, month, day):
    day_posts = [p for p in posts if year == p.meta.get('date').year and month == p.meta.get('date').month == month]
    month_string = MONTHS[month]
    return render_template('day.html', year=year, month_string=month_string, day=day, posts=day_posts)


# Telling Frozen-Flask about routes that are not linked to
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

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        freezer.freeze()
    else:
        app.run(port=5000)

if __name__ == '__main__':
    main()
