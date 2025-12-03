from pathlib import Path
import uuid

from flask import Flask
from flask_flatpages import Page
from htmd import site
from htmd.utils import set_post_metadata, validate_post
import pytest


def test_set_post_metadata_with_field_in_title(flask_app: Flask) -> None:
    # Add draft to the title
    example_path = Path('posts') / 'example.md'
    with example_path.open('r') as example_file:
        lines = example_file.readlines()

    title_line = 'title: Player drafted\n'
    with example_path.open('w') as example_file:
        for line in lines:
            if 'title:' in line:
                example_file.write(title_line)
            else:
                example_file.write(line)

    post = site.posts.get('example')
    post.meta['draft'] = 'build|' + str(uuid.uuid4())
    set_post_metadata(flask_app, post, 'draft', post.meta['draft'])

    with example_path.open('r') as example_file:
        contents = example_file.read()

    expected = 'draft: ' + post.meta['draft']
    assert expected in contents
    assert title_line in contents


def test_validate_post_invalid_updated(
    flask_app: Flask, # noqa: ARG001
    capsys: pytest.CaptureFixture[str],
) -> None:
    invalid_date = '2025-12-3'
    post = Page(
        path='example',
        meta=f'updated: {invalid_date}',
        body='',
        html_renderer=None,
        folder='.',
    )
    is_valid = validate_post(post, [])
    assert not is_valid
    exp = f'Updated date {invalid_date} for example is not in the format YYYY-MM-DD.\n'
    assert exp == capsys.readouterr().err



def test_validate_post_invalid_draft_uuid(
    flask_app: Flask, # noqa: ARG001
    capsys: pytest.CaptureFixture[str],
) -> None:
    invalid_draft = 'build|2025-12-03'
    post = Page(
        path='example',
        meta=f'draft: {invalid_draft}',
        body='',
        html_renderer=None,
        folder='.',
    )
    is_valid = validate_post(post, [])
    assert not is_valid
    expected = f'Draft field {invalid_draft} for example has an invalid UUID4.\n'
    assert expected == capsys.readouterr().err


def test_validate_post_invalid_draft_value(
    flask_app: Flask, # noqa: ARG001
    capsys: pytest.CaptureFixture[str],
) -> None:
    invalid_draft = 'foo'
    post = Page(
        path='example',
        meta=f'draft: {invalid_draft}',
        body='',
        html_renderer=None,
        folder='.',
    )
    is_valid = validate_post(post, [])
    assert not is_valid
    expected = 'Draft field foo for example is not valid. It must be True, False, "build", or "build|<UUID4>".\n' # noqa: E501
    assert expected == capsys.readouterr().err
