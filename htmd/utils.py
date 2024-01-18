from importlib.resources import as_file, files
import os
import shutil

import click
from csscompressor import compress
from jsmin import jsmin


def create_directory(name):
    try:
        os.mkdir(name)
    except FileExistsError:
        msg = f'{name} already exists and was not created.'
        click.echo(click.style(msg, fg='yellow'))
    else:
        click.echo(click.style(f'{name} was created.', fg='green'))


def combine_and_minify_css(static_folder):
    # Combine and minify all .css files in the static folder
    css_files = sorted(
        [
            f for f in os.listdir(static_folder)
            if f.endswith('.css') and f != 'combined.min.css'
        ]
    )
    if not css_files:
        # There are no .css files in the static folder
        return

    with open(os.path.join(static_folder, 'combined.min.css'), 'w') as master:
        for f in css_files:
            with open(os.path.join(static_folder, f), 'r') as css_file:
                # combine all .css files into one
                master.write(css_file.read())

    with open(os.path.join(static_folder, 'combined.min.css'), 'r') as master:
        combined = master.read()
    with open(os.path.join(static_folder, 'combined.min.css'), 'w') as master:
        master.write(compress(combined))


def combine_and_minify_js(static_folder):
    # Combine and minify all .js files in the static folder
    js_files = sorted(
        [
            f for f in os.listdir(static_folder)
            if f.endswith('.js')
            and f != 'combined.min.js'
        ]
    )
    if not js_files:
        # There are no .js files in the static folder
        return

    with open(os.path.join(static_folder, 'combined.min.js'), 'w') as master:
        for f in js_files:
            with open(os.path.join(static_folder, f), 'r') as js_file:
                # combine all .js files into one
                master.write(js_file.read())

    # minify should be done after combined to avoid duplicate identifiers
    # minifying each file will use 'a' for the first identifier
    with open(os.path.join(static_folder, 'combined.min.js'), 'r') as master:
        combined = master.read()
    with open(os.path.join(static_folder, 'combined.min.js'), 'w') as master:
        master.write(jsmin(combined))


def copy_file(source, destination):
    if os.path.exists(destination) is False:
        shutil.copyfile(source, destination)
        click.echo(click.style(f'{destination} was created.', fg='green'))
    else:
        msg = f'{destination} already exists and was not created.'
        click.echo(click.style(msg, fg='yellow'))


def copy_missing_templates():
    template_dir = files('htmd.example_site') / 'templates'
    for template_file in sorted(template_dir.iterdir()):
        file_name = os.path.basename(template_file)
        copy_file(template_file, os.path.join('templates/', file_name))


def copy_site_file(directory, filename):
    if directory == '':
        anchor = 'htmd.example_site'
    else:
        anchor = f'htmd.example_site.{directory}'
    source_path = files(anchor) / filename
    destination_path = os.path.join(directory, filename)

    with as_file(source_path) as file:
        copy_file(file, destination_path)
