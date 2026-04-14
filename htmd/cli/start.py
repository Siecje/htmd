from pathlib import Path

import click

from ..constants import CONFIG_FILE
from ..utils import copy_missing_templates, copy_site_file, create_directory


FILES = {
    'static/': ['_reset.css', 'style.css', 'favicon.svg'],
    'pages/': ['about.html', 'search.html'],
    'posts/': ['example.md'],
    'posts/password-protect/': ['.keep'],
    '.': [CONFIG_FILE],
}


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

    for folder, filenames in FILES.items():
        target_dir = Path() if folder == '.' else create_directory(folder)

        # Process files for target_dir
        for filename in filenames:
            if filename == '.keep':
                (target_dir / filename).touch()
            else:
                copy_site_file(target_dir, filename)

    click.echo(f'Add the site name and edit settings in {CONFIG_FILE}')
