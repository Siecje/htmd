import click

from .build import build
from .preview import preview
from .start import start
from .templates import templates
from .verify import verify


@click.group()
@click.version_option()
def cli() -> None:
    pass  # pragma: no cover


cli.add_command(build)
cli.add_command(preview)
cli.add_command(start)
cli.add_command(templates)
cli.add_command(verify)
