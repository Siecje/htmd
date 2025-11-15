from importlib.resources import as_file, files
from pathlib import Path
import shutil
import uuid

import click
from csscompressor import compress
from flask import Flask
from flask_flatpages import Page
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


def combine_and_minify_css(static_folder: Path) -> bool:
    # Combine and minify all .css files in the static folder
    try:
        css_files = sorted([
            f for f in static_folder.iterdir()
            if f.name.endswith('.css') and f.name != 'combined.min.css'
        ])
    except FileNotFoundError:
        # static folder does not exist
        return False

    if not css_files:
        # There are no .css files in the static folder
        return False

    # combine all .css files into one string
    file_contents = []
    for f in css_files:
        with f.open('r') as css_file:
            file_contents.append(css_file.read())
    combined_str = '\n'.join(file_contents)

    try:
        with (static_folder / 'combined.min.css').open('r') as combined_file:
            current_combined = combined_file.read()
    except FileNotFoundError:
        current_combined = ''

    new_combined = compress(combined_str)
    if new_combined == current_combined:
        return False

    with (static_folder / 'combined.min.css').open('w') as combined_file:
        combined_file.write(new_combined)
    return True


def combine_and_minify_js(static_folder: Path) -> bool:
    # Combine and minify all .js files in the static folder
    try:
        js_files = sorted([
            f for f in static_folder.iterdir()
            if f.name.endswith('.js')
            and f.name != 'combined.min.js'
        ])
    except FileNotFoundError:
        # static folder does not exist
        return False

    if not js_files:
        # There are no .js files in the static folder
        return False

    # combine all .js files into one string
    file_contents = []
    for f in js_files:
        with f.open('r') as js_file:
            file_contents.append(js_file.read())
    combined_str = '\n'.join(file_contents)

    try:
        with (static_folder / 'combined.min.js').open('r') as combined_file:
            current_combined = combined_file.read()
    except FileNotFoundError:
        current_combined = ''

    new_combined = jsmin(combined_str)
    if new_combined == current_combined:
        return False

    with (static_folder / 'combined.min.js').open('w') as combined_file:
        combined_file.write(new_combined)
    return True


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


def set_post_metadata(
    app: Flask,
    post: Page,
    field: str,
    value: str,
) -> None:
    file_path = (
        Path(app.config['FLATPAGES_ROOT'])
        / (post.path + app.config['FLATPAGES_EXTENSION'])
    )
    with file_path.open('r') as file:
        lines = file.readlines()

    found = False
    with file_path.open('w') as file:
        for line in lines:
            if not found and field in line:
                # Update datetime value
                line = f'{field}: {value}\n'  # noqa: PLW2901
                found = True
            elif not found and '...' in line:
                # Write field and value before '...'
                file.write(f'{field}: {value}\n')
                found = True
            file.write(line)


def valid_uuid(string: str) -> bool:
    try:
        uuid.UUID(string, version=4)
    except ValueError:
        return False
    else:
        return True
