from pathlib import Path
import uuid

from flask import Flask
from htmd import site
from htmd.utils import set_post_metadata


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
