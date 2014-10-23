import sys
from flask import Flask, render_template
from werkzeug.exceptions import abort
from flask.ext.flatpages import FlatPages
from flask_frozen import Freezer


DEBUG = True
FLATPAGES_AUTO_RELOAD = DEBUG
FLATPAGES_EXTENSION = '.md'


app = Flask(__name__)
app.config.from_object(__name__)
pages = FlatPages(app)
freezer = Freezer(app)

app.jinja_env.globals['SITE_NAME'] = 'Cody Scott'
app.jinja_env.globals['SHOW_AUTHOR'] = True

MONTHS = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}


@app.route('/')
def index():
    return render_template('index.html', pages=pages)


@app.route('/about')
def about():
    return render_template('about.html', pages=pages)

@app.route('/tags/<string:tag>')
def tag(tag):
    tagged = [p for p in pages if tag in p.meta.get('tags', [])]
    return render_template('tag.html', pages=tagged, tag=tag)


@app.route('/all')
def all_pages():
    return render_template('all_pages.html', pages=pages)


@app.route('/tags/')
def all_tags():
    tags = []
    for page in pages:
        for tag in page.meta.get('tags', []):
            if tag not in tags:
                tags.append(tag)
    return render_template('all_tags.html', tags=tags)

@app.route('/<int:year>/')
def year(year):
    posts = [p for p in pages if year == p.meta.get('date', []).year]
    return render_template('year.html', year=year, posts=posts)

@app.route('/<int:year>/<int:month>/')
def month(year, month):
    posts = [p for p in pages if year == p.meta.get('date').year and month == p.meta.get('date').month == month]
    month_string = MONTHS[month]
    return render_template('month.html', year=year, month_string=month_string, posts=posts)

@app.route('/<int:year>/<int:month>/<int:day>/')
def day(year, month, day):
    posts = [p for p in pages if year == p.meta.get('date').year and month == p.meta.get('date').month == month]
    month_string = MONTHS[month]
    return render_template('day.html', year=year, month_string=month_string, day=day, posts=posts)

@app.route('/<int:year>/<int:month>/<int:day>/<path:path>')
def post(year, month, day, path):
    post = pages.get_or_404(path)
    date = '%04d-%02d-%02d' % (year, month, day)
    if str(post.meta.get('date')) != date:
        abort(404)
    return render_template('page.html', page=post)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        freezer.freeze()
    else:
        app.run(port=5000)
