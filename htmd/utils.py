from importlib.resources import as_file, files
from pathlib import Path
import shutil

import click
from csscompressor import compress
from jsmin import jsmin


def create_directory(name: str) -> Path:
    directory = Path(name)
    try:
        directory.mkdir()
    except FileExistsError:
        msg = f'{name} already exists and was not created.'
        click.echo(click.style(msg, fg='yellow'))
    else:
        click.echo(click.style(f'{name} was created.', fg='green'))
    return directory


def combine_and_minify_css(static_folder: Path) -> None:
    # Combine and minify all .css files in the static folder
    css_files = sorted([
        f for f in static_folder.iterdir()
        if f.name.endswith('.css') and f.name != 'combined.min.css'
    ])
    if not css_files:
        # There are no .css files in the static folder
        return

    with (static_folder / 'combined.min.css').open('w') as master:
        for f in css_files:
            with (static_folder / f).open('r') as css_file:
                # combine all .css files into one
                master.write(css_file.read())

    with (static_folder / 'combined.min.css').open('r') as master:
        combined = master.read()
    with (static_folder / 'combined.min.css').open('w') as master:
        master.write(compress(combined))


def combine_and_minify_js(static_folder: Path) -> None:
    # Combine and minify all .js files in the static folder
    js_files = sorted([
        f for f in static_folder.iterdir()
        if f.name.endswith('.js')
        and f.name != 'combined.min.js'
    ])
    if not js_files:
        # There are no .js files in the static folder
        return

    with (static_folder / 'combined.min.js').open('w') as master:
        for f in js_files:
            with (static_folder / f).open('r') as js_file:
                # combine all .js files into one
                master.write(js_file.read())

    # minify should be done after combined to avoid duplicate identifiers
    # minifying each file will use 'a' for the first identifier
    with (static_folder / 'combined.min.js').open('r') as master:
        combined = master.read()
    with (static_folder / 'combined.min.js').open('w') as master:
        master.write(jsmin(combined))


def copy_file(source: Path, destination: Path) -> None:
    if destination.exists() is False:
        shutil.copyfile(source, destination)
        click.echo(click.style(f'{destination} was created.', fg='green'))
    else:
        msg = f'{destination} already exists and was not created.'
        click.echo(click.style(msg, fg='yellow'))


def copy_missing_templates() -> None:
    template_dir = files('htmd.example_site') / 'templates'
    with as_file(template_dir) as template_path:
        for template_file in sorted(template_path.iterdir()):
            file_name = template_file.name
            copy_file(template_file, Path('templates') / file_name)


def copy_site_file(directory: Path, filename: str) -> None:
    if directory.name == '':
        anchor = 'htmd.example_site'
    else:
        anchor = f'htmd.example_site.{directory}'
    source_path = files(anchor) / filename
    destination_path = directory / filename

    with as_file(source_path) as file:
        copy_file(file, destination_path)
