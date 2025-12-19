import sys

import click
from flask import Flask

from .. import site
from ..utils import validate_post


@click.command('verify', short_help='Verify posts formatting is correct.')
def verify() -> Flask:
    app = site.init_app()

    correct = True
    required_fields = ['title']
    # Only check author if there is no default
    if not app.config.get('DEFAULT_AUTHOR'):
        required_fields.append('author')
    for post in site.posts:
        if not validate_post(post, required_fields):
            correct = False

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
    return app
