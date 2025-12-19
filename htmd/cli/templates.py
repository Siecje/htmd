import sys

import click

from ..utils import copy_missing_templates, send_stderr


@click.command('templates', short_help='Create any missing templates.')
def templates() -> None:
    try:
        copy_missing_templates()
    except FileNotFoundError:
        send_stderr('templates/ directory not found.')
        sys.exit(1)
