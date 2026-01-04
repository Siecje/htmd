from collections.abc import Iterable
import datetime
from pathlib import Path
import sys
import warnings

import click
from flask import Flask
from flask_flatpages import Page

from .. import site
from ..utils import (
    combine_and_minify_css,
    combine_and_minify_js,
    send_stderr,
    set_post_metadata,
)
from .verify import verify


warnings.filterwarnings('ignore', '.*Nothing frozen for endpoints.*')


def get_published(
    published: None | datetime.date,
    updated: None | datetime.date,
    now: datetime.datetime,
) -> datetime.datetime:
    current_time = now.time()
    if isinstance(published, datetime.datetime):
        return published

    if isinstance(published, datetime.date):
        if isinstance(updated, datetime.datetime):
            new_published = datetime.datetime.combine(
                published, updated.time(),
            ).replace(tzinfo=datetime.UTC)
            return new_published

        new_published = datetime.datetime.combine(
            published, current_time,
        ).replace(tzinfo=datetime.UTC)
        return new_published

    if isinstance(updated, datetime.datetime):
        return updated
    if isinstance(updated, datetime.date):
        new_published = datetime.datetime.combine(
            updated, current_time,
        ).replace(tzinfo=datetime.UTC)
        return new_published

    return now


def set_posts_datetime(app: Flask, posts: Iterable[Page]) -> None:
    """
    Set published and updated for each post.

    Ensure each post has published.
    if missing, published will be set to current datetime
    Atom feed needs a datetime
    so if published is date, convert to datetime
    by keeping date and adding current time
    if published is already datetime
    set updated field to current datetime
    """
    now = datetime.datetime.now(tz=datetime.UTC)
    for post in posts:
        if post.meta.get('draft', False):
            continue

        current_published = post.meta.get('published')
        current_updated = post.meta.get('updated')
        published = get_published(
            current_published,
            current_updated,
            now,
        )
        if current_published != published:
            post.meta['published'] = published
            set_post_metadata(app, post, 'published', published.isoformat())
        if current_updated or isinstance(current_published, datetime.datetime):
            post.meta['updated'] = now
            set_post_metadata(app, post, 'updated', now.isoformat())


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
    *,
    css_minify: bool,
    js_minify: bool,
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
