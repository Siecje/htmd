import datetime
import importlib
from pathlib import Path
import sys
import warnings

import click
from flask import Flask
from flask_flatpages import FlatPages

from .utils import (
    combine_and_minify_css,
    combine_and_minify_js,
    copy_missing_templates,
    copy_site_file,
    create_directory,
    set_post_metadata,
)


warnings.filterwarnings('ignore', '.*Nothing frozen for endpoints.*')


@click.group()
@click.version_option()
def cli() -> None:
    pass  # pragma: no cover


@cli.command('start', short_help='Create example files to get started.')
@click.option(
    '--all-templates',
    is_flag=True,
    default=False,
    help='Include all templates.',
)
def start(all_templates: bool) -> None:  # noqa: FBT001
    dir_templates = create_directory('templates/')
    if all_templates:
        copy_missing_templates()
    else:
        copy_site_file(dir_templates, '_layout.html')

    dir_static = create_directory('static/')
    copy_site_file(dir_static, '_reset.css')
    copy_site_file(dir_static, 'style.css')

    dir_pages = create_directory('pages/')
    copy_site_file(dir_pages, 'about.html')

    dir_posts = create_directory('posts/')
    copy_site_file(dir_posts, 'example.md')

    copy_site_file(Path(), 'config.toml')
    click.echo('Add the site name and edit settings in config.toml')


@cli.command('verify', short_help='Verify posts formatting is correct.')
def verify() -> None:
    # import is here to avoid looking for the config
    # which doesn't exist until you run start
    from . import site
    # reload is needed for testing when the directory changes
    # FlatPages has already been loaded so the pages do not reload
    importlib.reload(site)
    app = site.app

    correct = True
    required_fields = ['title']
    # Only check author if there is no default
    if not app.config.get('DEFAULT_AUTHOR'):
        required_fields.append('author')
    for post in site.posts:
        for field in required_fields:
            if field not in post.meta:
                correct = False
                msg = f'Post "{post.path}" does not have field {field}.'
                click.echo(click.style(msg, fg='red'))
        if 'published' in post.meta:
            published = post.meta.get('published')
            if not hasattr(published, 'year'):
                correct = False
                msg = (
                    f'Published date {published} for {post.path}'
                    ' is not in the format YYYY-MM-DD.'
                )
                click.echo(click.style(msg, fg='red'))

    if correct:
        msg = 'All posts are correctly formatted.'
        click.echo(click.style(msg, fg='green'))

    # Check if SITE_NAME exists
    site_name = app.config.get('SITE_NAME')
    if not site_name:
        # SITE_NAME is not required
        message = '[site] name is not set in config.toml.'
        click.echo(click.style(message, fg='yellow'))

    if not correct:
        sys.exit(1)


def set_posts_datetime(app: Flask, posts: FlatPages) -> None:
    # Ensure each post has a published date
    # set time for correct date field
    for post in posts:
        if post.meta.get('draft', False):
            continue
        if 'updated' not in post.meta:
            published = post.meta.get('published')
            if isinstance(published, datetime.datetime):
                field = 'updated'
            else:
                field = 'published'
        else:
            field = 'updated'

        post_datetime = post.meta.get(field)
        now = datetime.datetime.now(tz=datetime.UTC)
        current_time = now.time()
        if isinstance(post_datetime, datetime.date):
            post_datetime = datetime.datetime.combine(
                post_datetime, current_time,
            ).replace(tzinfo=datetime.UTC)
        else:
            post_datetime = now
        post.meta[field] = post_datetime
        set_post_metadata(app, post, field, post_datetime.isoformat())


@cli.command('build', short_help='Create static version of the site.')
@click.pass_context
@click.option(
    '--css-minify/--no-css-minify',
    default=True,
    help='If CSS should be minified',
)
@click.option(
    '--js-minify/--no-js-minify',
    default=True,
    help='If JavaScript should be minified',
)
def build(
    ctx: click.Context,
    css_minify: bool,  # noqa: FBT001
    js_minify: bool,  # noqa: FBT001
) -> None:
    ctx.invoke(verify)
    # If verify fails sys.exit(1) will run

    from . import site
    app = site.app

    assert app.static_folder is not None
    static_path = Path(app.static_folder)
    if static_path.is_dir():
        if css_minify:
            assert app.static_folder is not None
            combine_and_minify_css(static_path)

        if js_minify:
            assert app.static_folder is not None
            combine_and_minify_js(static_path)

        if css_minify or js_minify:
            # reload to set app.config['INCLUDE_CSS'] and app.config['INCLUDE_JS']
            # setting them here doesn't work
            importlib.reload(site)

    set_posts_datetime(site.app, site.posts)

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
    help='Location to access the files.',
)
@click.option(
    '--port', '-p',
    default=9090,
    help='Port on which to serve the files.',
)
@click.option(
    '--css-minify/--no-css-minify',
    default=True,
    help='If CSS should be minified',
)
@click.option(
    '--js-minify/--no-js-minify',
    default=True,
    help='If JavaScript should be minified',
)
@click.option(
    '--drafts',
    default=False,
    help='Show draft posts in the preview.',
    is_flag=True,
)
def preview(
    _ctx: click.Context,
    host: str,
    port: int,
    css_minify: bool,  # noqa: FBT001
    js_minify: bool,  # noqa: FBT001
    drafts: bool,  # noqa: FBT001
) -> None:
    from . import site
    # reload for tests to refresh app.static_folder
    # otherwise app.static_folder will be from another test
    importlib.reload(site)
    app = site.app

    if css_minify:
        assert app.static_folder is not None
        combine_and_minify_css(Path(app.static_folder))

    if js_minify:
        assert app.static_folder is not None
        combine_and_minify_js(Path(app.static_folder))

    if drafts:
        site.preview_drafts()

    # reload when static files change
    # werkzeug will re-run the terminal command
    # Which causes the above combine_and_minify_*() to run
    # and recreate combined.min.css/combined.min.js files
    static_path = site.project_dir / 'static'
    extra_files = static_path.iterdir()
    app.run(debug=True, host=host, port=port, extra_files=extra_files)


@cli.command('templates', short_help='Create any missing templates')
def templates() -> None:
    try:
        copy_missing_templates()
    except FileNotFoundError:
        click.echo(click.style('templates/ directory not found.', fg='red'))
        sys.exit(1)
