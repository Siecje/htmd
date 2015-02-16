import os
import shutil
import click
from csscompressor import compress
from jsmin import jsmin
from flask import Flask


@click.group()
def cli():
    pass


def create_directory(name):
    if os.path.isdir(name) is False:
        os.mkdir(name)
        click.echo(click.style('%s was created.' % name, fg='green'))
    else:
        click.echo(click.style('%s already exists and was not created.' % name, fg='red'))


def copy_file(src, dest):
    if os.path.exists(dest) is False:
        shutil.copyfile(src, dest)
        click.echo(click.style('%s was created.' % dest, fg='green'))
    else:
        click.echo(click.style('%s already exists and was not created.' % dest, fg='red'))


def combine_and_minify_js():
    from site import app
    # Combine and minify all .js files in the static folder
    js_files = sorted([f for f in os.listdir(app.static_folder) if f.endswith('.js') and f != 'combined.min.js'])
    if not js_files:
        # There are no .js files in the static folder
        return
    with open(os.path.join(app.static_folder, 'combined.min.js'), 'w') as master:
        for f in js_files:
            with open(os.path.join(app.static_folder, f), 'r') as js_file:
                # combine all .js files into one
                master.write(js_file.read())
    # minify should be done after combined to avoid duplicate identifiers
    # minifying each file will use 'a' for the first identifier
    with open(os.path.join(app.static_folder, 'combined.min.js'), 'r') as master:
        combined = master.read()
    with open(os.path.join(app.static_folder, 'combined.min.js'), 'w') as master:
        master.write(jsmin(combined))

def combine_and_minify_css():
    from site import app
    # Combine and minify all .css files in the static folder
    css_files = sorted([f for f in os.listdir(app.static_folder) if f.endswith('.css') and f != 'combined.min.css'])
    if not css_files:
        # There are no .css files in the static folder
        return
    with open(os.path.join(app.static_folder, 'combined.min.css'), 'w') as master:
        for f in css_files:
            with open(os.path.join(app.static_folder, f), 'r') as css_file:
                # combine all .css files into one
                master.write(css_file.read())

    with open(os.path.join(app.static_folder, 'combined.min.css'), 'r') as master:
        combined = master.read()
    with open(os.path.join(app.static_folder, 'combined.min.css'), 'w') as master:
        master.write(compress(combined))


@cli.command('start', short_help='Create example files to get started.')
def start():
    create_directory('templates/')
    copy_file(os.path.join(os.path.dirname(__file__), 'templates', '_layout.html'),
          os.path.join('templates/', '_layout.html'))
    create_directory('static/')
    copy_file(os.path.join(os.path.dirname(__file__), 'static', '_reset.css'),
              os.path.join('static/', '_reset.css'))
    copy_file(os.path.join(os.path.dirname(__file__), 'static', 'style.css'),
              os.path.join('static/', 'style.css'))
    create_directory('pages/')
    copy_file(os.path.join(os.path.dirname(__file__), 'about.html'),
              os.path.join('pages/', 'about.html'))
    create_directory('posts/')
    copy_file(os.path.join(os.path.dirname(__file__), 'example.md'),
              os.path.join('posts/', 'example.md'))
    copy_file(os.path.join(os.path.dirname(__file__), 'config.py'),
              os.path.join('config.py'))
    click.echo('Add the site name and edit settings in config.py')


@cli.command('verify', short_help='Verify posts formatting is correct.')
def verify():
    # import is here to avoid looking for the config
    # which doesn't exist until you run start
    from site import posts
    correct = True
    for post in posts:
        for item in ['author', 'title', 'published']:
            if item not in post.meta:
                correct = False
                click.echo(click.style('%s does not have %s' % (post.path, item), fg='red'))
        if 'published' in post.meta:
            try:
                post.meta.get('published').year
            except AttributeError:
                correct = False
                click.echo(click.style('Published date %s for %s is not in the format YYYY-MM-DD' % (post.meta.get('published'), post.path), fg='red'))
    if correct is True:
        click.echo(click.style('All posts are correctly formatted.', fg='green'))

    # Check if SITE_NAME exists
    from site import app
    if not app.config['SITE_NAME']:
        click.echo(click.style('Specify SITE_NAME in config.py.', fg='red'))
    if app.config['SITE_NAME'] and correct:
        return True
    return False


@cli.command('build', short_help='Create static version of the site.')
@click.pass_context
@click.option('--no-min', is_flag=True, help="Prevent JS and CSS from being minified")
def build(ctx, no_min):
    valid = ctx.invoke(verify)
    if valid:
        from site import freezer, app
        if no_min is False:
          combine_and_minify_js()
          combine_and_minify_css()
        freezer.freeze()
        #if no_min is False:
            # minify HTML files in build/
            # TODO:
        click.echo(click.style('Static site was created in %s' % app.config.get('FREEZER_DESTINATION'), fg='green'))
    return valid


@cli.command('preview', short_help='Serve files to preview site.')
@click.pass_context
@click.option('--host', '-h', default='127.0.0.1', help='Location to access the files.')
@click.option('--port', '-p', default=9090, help='Port on which to serve the files.')
@click.option('--no-min', is_flag=True, help="Prevent JS and CSS from being minified")
def preview(ctx, host, port, no_min):
    if no_min is False:
        combine_and_minify_js()
        combine_and_minify_css()
    from site import app as build_app
    build_app.run(debug=True, host=host, port=port)
