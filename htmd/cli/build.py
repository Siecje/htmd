import sys
import warnings

import click

from .. import site
from ..utils import (
    send_stderr,
    sync_posts,
)
from .verify import verify


warnings.filterwarnings('ignore', '.*Nothing frozen for endpoints.*')


@click.command('build', short_help='Create static version of the site.')
@click.pass_context
@click.option(
    '--minify-css', '--css-minify',
    '/--no-minify-css', '--no-css-minify',
    default=True,
    help='If CSS should be minified',
    is_flag=True,
    show_default=True,
)
@click.option(
    '--minify-js', '--js-minify',
    '/--no-minify-js', '--no-js-minify',
    default=True,
    help='If JavaScript should be minified',
    is_flag=True,
    show_default=True,
)
def build(
    ctx: click.Context,
    *,
    minify_css: bool,
    minify_js: bool,
) -> None:
    app = site.create_app(minify_css=minify_css, minify_js=minify_js)
    ctx.ensure_object(dict)
    ctx.obj['flask_app'] = app
    ctx.invoke(verify)
    # If verify fails sys.exit(1) will run

    sync_posts(app)

    freezer = site.freezer
    try:
        freezer.freeze()
    except ValueError as exc:
        send_stderr(str(exc))
        sys.exit(1)

    build_dir = app.config.get('FREEZER_DESTINATION')
    msg = f'Static site was created in {build_dir}'
    click.echo(click.style(msg, fg='green'))
