import datetime
import hashlib
from importlib.resources import as_file, files
import os
from pathlib import Path
import shutil
import tempfile
import uuid

import click
from csscompressor import compress
from flask import Flask
from flask_flatpages import Page
from jsmin import jsmin

from .password_protect import generate_private_key


def atomic_write(path: Path, content: str) -> None:
    """
    Write content to a file using an atomic move.

    This prevents other processes (like Flask or a Watchdog)
    from seeing a truncated or empty file.
    """
    # Create the temp file in the same directory as the target
    # to ensure os.replace works across the same file system partition.
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        text=True,
        suffix='.tmp',
    )
    try:
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(content)
            tmp.flush()
            # Force write to disk
            os.fsync(tmp.fileno())

        # Atomically swap the new file into the old one's place
        os.replace(temp_path, path)  # noqa: PTH105
    except Exception:  # pragma: no cover
        Path(temp_path).unlink(missing_ok=True)
        raise


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


def format_yaml_value(value: str) -> str:
    """Return a single-line value or a YAML literal block if newlines are present."""
    if '\n' in value:
        # YAML Literal Block Scalar: indent each line by 4 spaces
        indented = value.replace('\n', '\n    ')
        return f'|\n    {indented}'
    return value


def set_post_metadata(
    app: Flask,
    post: Page,
    updates: dict[str, str],
) -> None:
    post_folder = Path(app.config['FLATPAGES_ROOT']) / post.folder
    file_extension = app.config['FLATPAGES_EXTENSION']
    file_path = post_folder / (post.path + file_extension)
    with file_path.open('r') as file:
        lines = file.readlines()

    applied_keys = set()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        key_match = None
        for key in updates:
            if line.startswith(f'{key}:'):
                key_match = key
                break

        if key_match:
            val = updates[key]
            formatted_val = format_yaml_value(val)
            new_lines.append(f'{key}: {formatted_val}\n')
            applied_keys.add(key)

            # Skip existing multi-line values in the source
            if line.strip().endswith('|'):
                i += 1
                while i < len(lines) and lines[i].startswith('    '):
                    i += 1
                continue
        elif line.strip() == '...' and (set(updates.keys()) - applied_keys):
            # If we hit the end of metadata and have new keys to add
            for key, val in updates.items():
                if key not in applied_keys:
                    formatted_val = format_yaml_value(val)
                    new_lines.append(f'{key}: {formatted_val}\n')
            new_lines.append(line)
            applied_keys.update(updates.keys())
        else:
            new_lines.append(line)

        i += 1

    atomic_write(file_path, ''.join(new_lines))


def valid_uuid(string: str) -> bool:
    try:
        uuid.UUID(string, version=4)
    except ValueError:
        return False
    else:
        return True


def send_stderr(message: str) -> None:
    click.echo(click.style(message, fg='red'), err=True)


def validate_post(post: Page, required_fields: list[str]) -> bool: # noqa: C901
    correct = True
    for field in required_fields:
        if field not in post.meta:
            correct = False
            msg = f'Post "{post.path}" does not have field {field}.'
            send_stderr(msg)
    if 'published' in post.meta:
        published = post.meta.get('published')
        if not hasattr(published, 'year'):
            correct = False
            msg = (
                f'Published date {published} for {post.path}'
                ' is not in the format YYYY-MM-DD.'
            )
            send_stderr(msg)
    if 'updated' in post.meta:
        updated = post.meta.get('updated')
        if not hasattr(updated, 'year'):
            correct = False
            msg = (
                f'Updated date {updated} for {post.path}'
                ' is not in the format YYYY-MM-DD.'
            )
            send_stderr(msg)
    if 'draft' in post.meta:
        draft = post.meta['draft']
        if draft in [True, False, 'build']:
            pass
        elif 'build|' in draft:
            draft_id = draft.split('|')[1]
            if not valid_uuid(draft_id):
                correct = False
                msg = (
                    f'Draft field {draft} for {post.path}'
                    ' has an invalid UUID4.'
                )
                send_stderr(msg)
        else:
            correct = False
            msg = (
                f'Draft field {draft} for {post.path}'
                ' is not valid. It must be True, False,'
                ' "build", or "build|<UUID4>".'
            )
            send_stderr(msg)

    return correct


def _get_published(
    published: None | datetime.date,
    updated: None | datetime.date,
    now: datetime.datetime,
) -> datetime.datetime:
    if isinstance(published, datetime.datetime):
        return published

    if isinstance(published, datetime.date):
        new_published = datetime.datetime.combine(
            published,
            datetime.time.min,
            tzinfo=datetime.UTC,
        )
        return new_published

    if isinstance(updated, datetime.datetime):
        return updated
    if isinstance(updated, datetime.date):
        new_published = datetime.datetime.combine(
            updated,
            datetime.time.min,
            tzinfo=datetime.UTC,
        )
        return new_published

    return now


def _get_post_hash(title: str, contents: str) -> str:
    hash_obj = hashlib.sha256()

    separator = b'\x00'

    hash_obj.update(title.encode('utf-8'))
    hash_obj.update(separator)
    hash_obj.update(contents.encode('utf-8'))

    hex_result = hash_obj.hexdigest()
    return hex_result


def sync_posts(
    app: Flask,
) -> None:
    """
    Sync draft, published, updated, and _hash for each post.

    Ensure each draft build post has a uuid.
    Don't change published, updated, or _hash for drafts.

    Ensure each non draft post has published:
    If published is missing set to current datetime
    Atom feed needs a datetime
    so if published is date, convert to datetime
    if published is already datetime
    set updated field to current datetime

    If updated is a date, convert to datetime.

    Set hash using title and post contents.
    """
    now = datetime.datetime.now(tz=datetime.UTC)
    _posts = app.extensions['flatpages'][None]
    with app.app_context():
        for post in _posts.pages.values():
            file_updates: dict[str, str] = {}
            if 'password' in post.meta and post.meta['password'] is None:
                _, post.meta['password'] = generate_private_key()
                assert isinstance(post.meta['password'], str)
                file_updates['password'] = post.meta['password']

            if post.meta.get('draft', False):
                if (
                    'build' in str(post.meta['draft'])
                    and not valid_uuid(post.meta['draft'].replace('build|', ''))
                ):
                    post.meta['draft'] = 'build|' + str(uuid.uuid4())
                    file_updates['draft'] = post.meta['draft']
                    set_post_metadata(
                        app,
                        post,
                        file_updates,
                    )
                continue

            current_published = post.meta.get('published')
            current_updated = post.meta.get('updated')
            current_hash = post.meta.get('_hash', '')
            published = _get_published(
                current_published,
                current_updated,
                now,
            )

            post_hash = _get_post_hash(
                post.meta.get('title') or '',
                post.html,
            )

            hash_changed = current_hash != post_hash

            if hash_changed:
                post.meta['_hash'] = post_hash
                file_updates['_hash'] = post.meta['_hash']
            if published != current_published:
                post.meta['published'] = published
                file_updates['published'] = published.isoformat()
            post_already_published = (
                isinstance(current_published, datetime.datetime)
                or isinstance(current_updated, datetime.datetime)
            )
            if hash_changed and post_already_published:
                post.meta['updated'] = now
                file_updates['updated'] = now.isoformat()
            elif (
                not isinstance(current_updated, datetime.datetime)
                and isinstance(current_updated, datetime.date)
            ):
                updated = datetime.datetime.combine(
                    current_updated,
                    datetime.time.min,
                    tzinfo=datetime.UTC,
                )
                post.meta['updated'] = updated
                file_updates['updated'] = updated.isoformat()

            if file_updates:
                set_post_metadata(
                    app,
                    post,
                    file_updates,
                )
