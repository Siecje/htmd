import datetime
from pathlib import Path
import sys
import warnings

import click
from flask import Flask
from flask_flatpages import FlatPages

from .. import site
from ..utils import (
    combine_and_minify_css,
    combine_and_minify_js,
    send_stderr,
    set_post_metadata,
)
from .verify import verify


warnings.filterwarnings('ignore', '.*Nothing frozen for endpoints.*')


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


@click.command('build', short_help='Create static version of the site.')
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
    app = ctx.invoke(verify)
    # If verify fails sys.exit(1) will run

    assert app.static_folder is not None
    static_path = Path(app.static_folder)
    if css_minify and combine_and_minify_css(static_path):
        app.config['INCLUDE_CSS'] = app.jinja_env.globals['INCLUDE_CSS'] = True

    if js_minify and combine_and_minify_js(static_path):
        app.config['INCLUDE_JS'] = app.jinja_env.globals['INCLUDE_JS'] = True

    set_posts_datetime(app, site.posts)

    freezer = site.freezer
    try:
        freezer.freeze()
    except ValueError as exc:
        send_stderr(str(exc))
        sys.exit(1)

    build_dir = app.config.get('FREEZER_DESTINATION')
    msg = f'Static site was created in {build_dir}'
    click.echo(click.style(msg, fg='green'))
