from pathlib import Path
import sys
import warnings

import click

from .. import site
from ..utils import (
    combine_and_minify_css,
    combine_and_minify_js,
    send_stderr,
    sync_posts,
)
from .verify import verify


warnings.filterwarnings('ignore', '.*Nothing frozen for endpoints.*')


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
