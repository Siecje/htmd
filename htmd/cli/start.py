from pathlib import Path

import click

from ..constants import CONFIG_FILE
from ..utils import copy_missing_templates, copy_site_file, create_directory


@click.command('start', short_help='Create example files to get started.')
@click.option(
    '--all-templates',
    is_flag=True,
    default=False,
    help='Include all templates.',
)
def start(*, all_templates: bool) -> None:
    dir_templates = create_directory('templates/')
    if all_templates:
        copy_missing_templates()
    else:
        copy_site_file(dir_templates, '_layout.html')

    dir_static = create_directory('static/')
    copy_site_file(dir_static, '_reset.css')
    copy_site_file(dir_static, 'style.css')
    copy_site_file(dir_static, 'favicon.svg')

    dir_pages = create_directory('pages/')
    copy_site_file(dir_pages, 'about.html')
    copy_site_file(dir_pages, 'search.html')

    dir_posts = create_directory('posts/')
    copy_site_file(dir_posts, 'example.md')
    create_directory('posts/password-protect/')
    Path('posts/password-protect/.keep').touch()

    copy_site_file(Path(), CONFIG_FILE)
    click.echo(f'Add the site name and edit settings in {CONFIG_FILE}')
