import importlib.resources
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
        click.echo(click.style(msg, fg='red'))
    else:
        click.echo(click.style(f'{name} was created.', fg='green'))


def copy_file(src, dest):
    if os.path.exists(dest) is False:
        shutil.copyfile(src, dest)
        click.echo(click.style(f'{dest} was created.', fg='green'))
    else:
        msg = f'{dest} already exists and was not created.'
        click.echo(click.style(msg, fg='red'))


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


def copy_missing_templates():
    htmd_dir = os.path.dirname(__file__)
    template_dir = importlib.resources.contents('htmd.example_site.templates')
    for template_file in sorted(template_dir):
        if template_file in ('__init__.py', '__pycache__'):
            # __init__.py is that this directory for importlib.resources to work
            continue
        copy_file(
            importlib.resources.path('htmd.example_site.templates', template_file),
            os.path.join('templates', template_file)
        )
