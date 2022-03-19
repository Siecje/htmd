import importlib
# Need to import importlib.resources explicitly
import importlib.resources
import os
import sys

import click

from .utils import (
    combine_and_minify_css,
    combine_and_minify_js,
    copy_file,
    copy_missing_templates,
    create_directory,
)


@click.group()
def cli():
    pass  # pragma: no cover


@cli.command('start', short_help='Create example files to get started.')
@click.option(
    '--all-templates',
    is_flag=True,
    default=False,
    help='Include all templates.'
)
def start(all_templates):
    htmd_dir = os.path.dirname(__file__)

    create_directory('templates/')
    if all_templates:
        copy_missing_templates()
    else:
        copy_file(
            importlib.resources.path('htmd.example_site.templates', '_layout.html'),
            os.path.join('templates/', '_layout.html')
        )

    create_directory('static/')
    copy_file(
        importlib.resources.path('htmd.example_site.static', '_reset.css'),
        os.path.join('static/', '_reset.css')
    )
    copy_file(
        importlib.resources.path('htmd.example_site.static', 'style.css'),
        os.path.join('static/', 'style.css'),
    )

    create_directory('pages/')
    copy_file(
        importlib.resources.path('htmd.example_site.pages', 'about.html'),
        os.path.join('pages/', 'about.html'),
    )

    create_directory('posts/')
    copy_file(
        importlib.resources.path('htmd.example_site.posts', 'example.md'),
        os.path.join('posts/', 'example.md'),
    )

    copy_file(
        importlib.resources.path('htmd.example_site', 'config.py'),
        os.path.join('config.py'),
    )
    click.echo('Add the site name and edit settings in config.py')


@cli.command('verify', short_help='Verify posts formatting is correct.')
def verify():
    # import is here to avoid looking for the config
    # which doesn't exist until you run start
    from . import site
    # reload is needed for testing when the directory changes
    # FlatPages has already been loaded so the pages do not reload
    importlib.reload(site)

    correct = True
    for post in site.posts:
        for item in ['author', 'title', 'published']:
            if item not in post.meta:
                correct = False
                msg = f'Post "{post.path}" does not have field {item}.'
                click.echo(click.style(msg, fg='red'))
        if 'published' in post.meta:
            try:
                post.meta.get('published').year
            except AttributeError:
                correct = False
                published = post.meta.get('published')
                msg = (
                    f'Published date {published} for {post.path}'
                    ' is not in the format YYYY-MM-DD.'
                )
                click.echo(click.style(msg, fg='red'))
    if correct:
        msg = 'All posts are correctly formatted.'
        click.echo(click.style(msg, fg='green'))

    # Check if SITE_NAME exists
    app = site.app
    site_name = app.config.get('SITE_NAME')
    if not site_name:
        click.echo(click.style('SITE_NAME is not set in config.py.', fg='red'))

    # SITE_NAME is not required
    if not correct:
        sys.exit(1)


@cli.command('build', short_help='Create static version of the site.')
@click.pass_context
@click.option(
    '--css-minify/--no-css-minify',
    default=True,
    help='If CSS should be minified'
)
@click.option(
    '--js-minify/--no-js-minify',
    default=True,
    help='If JavaScript should be minified'
)
def build(ctx, css_minify, js_minify):
    ctx.invoke(verify)
    # If verify fails sys.exit(1) will run

    from . import site
    app = site.app

    if css_minify:
        combine_and_minify_css(app.static_folder)

    if js_minify:
        combine_and_minify_js(app.static_folder)

    if css_minify or js_minify:
        # reload to set app.config['INCLUDE_CSS'] and app.config['INCLUDE_JS']
        # setting them here doesn't work
        importlib.reload(site)

    freezer = site.freezer
    try:
        freezer.freeze()
    except ValueError as exc:
        click.echo(click.style(str(exc), fg='red'))
        sys.exit(1)

    build_dir = app.config.get('FREEZER_DESTINATION')
    msg = f'Static site was created in {build_dir}'
    click.echo(click.style(msg, fg='green'))


@cli.command('preview', short_help='Serve files to preview site.')
@click.pass_context
@click.option(
    '--host', '-h',
    default='127.0.0.1',
    help='Location to access the files.'
)
@click.option(
    '--port', '-p',
    default=9090,
    help='Port on which to serve the files.'
)
@click.option(
    '--css-minify/--no-css-minify',
    default=True,
    help='If CSS should be minified'
)
@click.option(
    '--js-minify/--no-js-minify',
    default=True,
    help='If JavaScript should be minified'
)
def preview(ctx, host, port, css_minify, js_minify):
    from . import site
    # reload for tests to refresh app.static_folder
    # otherwise app.static_folder will be from another test
    importlib.reload(site)
    app = site.app

    if css_minify:
        combine_and_minify_css(app.static_folder)

    if js_minify:
        combine_and_minify_js(app.static_folder)

    app.run(debug=True, host=host, port=port)


@cli.command('templates', short_help='Create any missing templates')
def templates():
    try:
        copy_missing_templates()
    except FileNotFoundError:
        click.echo(click.style('templates/ directory not found.', fg='red'))
        sys.exit(1)
