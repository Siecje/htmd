import sys

import click
from flask import Flask

from .. import site
from ..constants import CONFIG_FILE
from ..utils import validate_post


@click.command('verify', short_help='Verify posts formatting is correct.')
@click.pass_context
def verify(ctx: click.Context) -> Flask:
    ctx.ensure_object(dict)
    app: Flask | None = ctx.obj.get('flask_app')
    if app is None:
        app = site.create_app()

    correct = True
    required_fields = ['title']
    # Only check author if there is no default
    if not app.config.get('DEFAULT_AUTHOR'):
        required_fields.append('author')
    posts = site.posts.get_posts(app)
    for post in posts:
        if not validate_post(post, required_fields):
            correct = False
            break
    else:
        msg = 'All posts are correctly formatted.'
        click.echo(click.style(msg, fg='green'))

    # Check if SITE_NAME exists
    site_name = app.config.get('SITE_NAME')
    if not site_name:
        # SITE_NAME is not required
        message = f'[site] name is not set in {CONFIG_FILE}.'
        click.echo(click.style(message, fg='yellow'))

    if not correct:
        sys.exit(1)
    return app
