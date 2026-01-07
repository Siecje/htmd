from pathlib import Path
import re
from typing import Any

from bs4 import BeautifulSoup
from click.testing import CliRunner
from htmd.cli.build import build
import requests

from utils import (
    get_example_field,
    remove_fields_from_post,
    set_config_field,
    set_example_field,
    SUCCESS_REGEX,
)
from utils_preview import run_preview


def validate_example_feed(
    base_url: str,
    feed_contents: str,
    *,
    published: str | None = None,
    updated: str | None = None,
) -> None:
    # type Any to prevent mypy from complaing that .find() can return None
    feed: Any = BeautifulSoup(feed_contents, 'xml').find('feed')
    assert feed.find('title').string == 'htmd'
    assert feed.find('id').string == base_url + '/feed.atom'
    feed_links = [
        str(link) for link in feed.find_all('link', recursive=False)
    ]
    feed_link = f'<link href="{base_url}/feed.atom" rel="self"/>'
    assert feed_links == [f'<link href="{base_url}/all/"/>', feed_link]
    assert str(feed.find('link', rel='self')) == feed_link
    assert feed.find('subtitle').string == 'Recent Blog Posts'
    assert feed.find('generator') is None

    entry = feed.find('entry')
    assert entry.find('title').string == 'Example Post'
    assert entry.find('id').string == f'{base_url}/2014/10/30/example/'
    updated_str = entry.find('updated').string
    if updated:
        assert updated_str == updated
    else:
        assert updated_str.startswith('2014-10-30')
    # Check for ISO 8601 format (YYYY-MM-DDTHH:MM:SS...)
    iso_regex = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
    assert re.match(iso_regex, updated_str)

    published_str = entry.find('published').string
    if published:
        assert published_str == published
    else:
        assert published_str == updated_str
    assert entry.find('link')['href'] == entry.find('id').string
    author = entry.find('author')
    assert author is not None
    assert author.find('name').string == 'Taylor'
    expected = '<p>This is the post <strong>text</strong>.</p>'
    assert entry.find('content').text == expected


def test_without_updated(run_start: CliRunner) -> None:
    remove_fields_from_post('example', ('updated',))
    path = Path('posts') / 'example.md'
    with path.open('r') as post_file:
        contents = post_file.read()
    assert 'updated:' not in contents

    server_name = 'example.com'
    set_config_field('url', server_name)

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    feed_path = Path('build') / 'feed.atom'
    with feed_path.open('r') as feed_file:
        feed_contents = feed_file.read()

    base_url = f'http://{server_name}'
    validate_example_feed(base_url, feed_contents)

    with run_preview(run_start) as preview_base_url:
        response = requests.get(preview_base_url + '/feed.atom', timeout=1)
        assert response.status_code == 200  # noqa: PLR2004
        validate_example_feed(base_url, response.text)


def test_with_updated(run_start: CliRunner) -> None:
    # Set published as datetime so updated will be set
    # during build
    published = '2014-10-30T10:29:00+00:00'
    set_example_field('published', published)

    assert get_example_field('updated') is None

    server_name = 'example.com'
    set_config_field('url', server_name)

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    feed_path = Path('build') / 'feed.atom'
    with feed_path.open('r') as feed_file:
        feed_contents = feed_file.read()

    updated = get_example_field('updated')

    base_url = f'http://{server_name}'
    validate_example_feed(
        base_url,
        feed_contents,
        published=published,
        updated=updated,
    )

    with run_preview(run_start) as preview_base_url:
        response = requests.get(preview_base_url + '/feed.atom', timeout=1)
        assert response.status_code == 200  # noqa: PLR2004
        validate_example_feed(
            base_url,
            response.text,
            published=published,
            updated=updated,
        )


def test_with_site_description(run_start: CliRunner) -> None:
    description = 'This is my blog description.'
    set_config_field('description', description)

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    feed_path = Path('build') / 'feed.atom'
    with feed_path.open('r') as feed_file:
        feed_contents = feed_file.read()

    feed = BeautifulSoup(feed_contents, 'xml').find('feed')
    assert feed.find('subtitle').string == description  # type: ignore[union-attr]
