import os
import shutil
import sys

import click
from csscompressor import compress
from flask import Flask
from jsmin import jsmin


@click.group()
def cli():
    pass


def create_directory(name):
    try:
        os.mkdir(name)
    except FileExistsError:
        click.echo(click.style(f'{name} already exists and was not created.', fg='red'))
    else:
        click.echo(click.style(f'{name} was created.', fg='green'))


def copy_file(src, dest):
    if os.path.exists(dest) is False:
        shutil.copyfile(src, dest)
        click.echo(click.style(f'{dest} was created.', fg='green'))
    else:
        click.echo(click.style(f'{dest} already exists and was not created.', fg='red'))


def combine_and_minify_js():
    from .site import app
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
    from .site import app
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


def copy_missing_templates():
    htmd_dir = os.path.dirname(__file__)
    template_dir = os.path.join(htmd_dir, 'templates')
    for template_file in os.listdir(template_dir):
        copy_file(os.path.join(template_dir, template_file),
            os.path.join('templates', template_file))


@cli.command('start', short_help='Create example files to get started.')
@click.option('--all-templates', is_flag=True, default=False, help="Include all templates.")
def start(all_templates):
    htmd_dir = os.path.dirname(__file__)

    create_directory('templates/')
    if all_templates:
        copy_missing_templates()
    else:
        copy_file(os.path.join(htmd_dir, 'templates', '_layout.html'),
          os.path.join('templates/', '_layout.html'))

    create_directory('static/')
    copy_file(os.path.join(htmd_dir, 'static', '_reset.css'),
              os.path.join('static/', '_reset.css'))
    copy_file(os.path.join(htmd_dir, 'static', 'style.css'),
              os.path.join('static/', 'style.css'))
    
    create_directory('pages/')
    copy_file(os.path.join(htmd_dir, 'about.html'),
              os.path.join('pages/', 'about.html'))
    
    create_directory('posts/')
    copy_file(os.path.join(htmd_dir, 'example.md'),
              os.path.join('posts/', 'example.md'))
    
    copy_file(os.path.join(htmd_dir, 'config.py'),
              os.path.join('config.py'))
    click.echo('Add the site name and edit settings in config.py')


@cli.command('verify', short_help='Verify posts formatting is correct.')
def verify():
    # import is here to avoid looking for the config
    # which doesn't exist until you run start
    from .site import posts
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
    from .site import app
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
    if not valid:
        return valid

    from .site import freezer, app
    if no_min is False:
        combine_and_minify_js()
        combine_and_minify_css()

    freezer.freeze()

    build_dir = app.config.get('FREEZER_DESTINATION')
    click.echo(click.style(f'Static site was created in {build_dir}', fg='green'))


@cli.command('preview', short_help='Serve files to preview site.')
@click.pass_context
@click.option('--host', '-h', default='127.0.0.1', help='Location to access the files.')
@click.option('--port', '-p', default=9090, help='Port on which to serve the files.')
@click.option('--no-min', is_flag=True, help="Prevent JS and CSS from being minified")
def preview(ctx, host, port, no_min):
    if no_min is False:
        combine_and_minify_js()
        combine_and_minify_css()
    from .site import app as build_app
    build_app.run(debug=True, host=host, port=port)


@cli.command('templates', short_help='Create any missing templates')
def templates():
    try:
        copy_missing_templates()
    except FileNotFoundError:
        click.echo(click.style('templates/ directory not found.', fg='red'))
        sys.exit(1)
