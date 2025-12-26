import click

from . import build, preview, start, templates, verify


@click.group()
@click.version_option()
def cli() -> None:
    pass  # pragma: no cover


cli.add_command(build.build)
cli.add_command(preview.preview)
cli.add_command(start.start)
cli.add_command(templates.templates)
cli.add_command(verify.verify)
