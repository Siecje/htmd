from pathlib import Path
import re
import xml.etree.ElementTree as ET

from click.testing import CliRunner
from htmd.cli.build import build

from utils import (
    get_example_field,
    http_get,
    remove_fields_from_post,
    set_config_field,
    set_example_field,
    SUCCESS_REGEX,
)
from utils_preview import run_preview


def link_to_str(el: ET.Element) -> str:
    href_value = el.get('href')
    rel_value = el.get('rel')
    if rel_value is not None:
        result = f'<link href="{href_value}" rel="{rel_value}"/>'
    else:
        result = f'<link href="{href_value}"/>'
    return result


def assert_tag_text(
    parent: ET.Element,
    tag: str,
    expected: str,
) -> ET.Element:
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    el = parent.find(tag, ns)
    assert el is not None, f'Expected tag <{tag}> was not found.'
    assert el.text == expected, \
        f'Tag <{tag}> text mismatch. Expected: {expected}, Got: {el.text}'
    return el


def validate_example_feed(
    base_url: str,
    feed_contents: str,
    *,
    published: str | None = None,
    updated: str | None = None,
) -> None:
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    root = ET.fromstring(feed_contents)  # noqa: S314

    # --- Feed Metadata ---
    assert_tag_text(root, 'atom:title', 'htmd')
    assert_tag_text(root, 'atom:id', f'{base_url}/feed.atom')
    assert_tag_text(root, 'atom:subtitle', 'Recent Blog Posts')

    assert root.find('atom:generator', ns) is None

    feed_links = root.findall('atom:link', ns)
    feed_url = link_to_str(feed_links[1])
    all_url = link_to_str(feed_links[0])
    assert all_url == f'<link href="{base_url}/all/"/>'
    assert feed_url == f'<link href="{base_url}/feed.atom" rel="self"/>'

    # --- Entry Content ---
    entry = root.find('atom:entry', ns)
    assert entry is not None

    assert_tag_text(entry, 'atom:title', 'Example Post')

    # Check ID and grab the string for the link comparison later
    entry_id_el = assert_tag_text(
        entry,
        'atom:id',
        f'{base_url}/2014/10/30/example/',
    )
    entry_id = entry_id_el.text

    # Updated Date Logic
    updated_el = entry.find('atom:updated', ns)
    assert updated_el is not None
    updated_str = updated_el.text
    assert isinstance(updated_str, str), \
        f'Expected string in <updated>, got {type(updated_str)}'

    if updated:
        assert updated_str == updated
    else:
        assert updated_str.startswith('2014-10-30')

    assert re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', updated_str)

    # Published Date Logic
    published_el = entry.find('atom:published', ns)
    assert published_el is not None
    if published:
        assert published_el.text == published
    else:
        # Defaults to updated_str if not explicitly provided
        assert published_el.text == updated_str

    # Final Details (Link, Author, Content)
    entry_link = entry.find('atom:link', ns)
    assert entry_link is not None
    assert entry_link.get('href') == entry_id

    author = entry.find('atom:author', ns)
    assert author is not None
    assert_tag_text(author, 'atom:name', 'Taylor')

    assert_tag_text(
        entry,
        'atom:content',
        '<p>This is the post <strong>text</strong>.</p>',
    )


def test_without_updated_build(run_start: CliRunner) -> None:
    remove_fields_from_post('example', ('updated',))
    path = Path('posts') / 'example.md'
    contents = path.read_text()
    assert 'updated:' not in contents

    server_name = 'example.com'
    set_config_field('url', server_name)

    result = run_start.invoke(build)
    assert result.exit_code == 0
    assert re.search(SUCCESS_REGEX, result.output)

    feed_path = Path('build') / 'feed.atom'
    feed_contents = feed_path.read_text()

    base_url = f'http://{server_name}'
    validate_example_feed(base_url, feed_contents)


def test_without_updated_preview(run_start: CliRunner) -> None:
    remove_fields_from_post('example', ('updated',))
    path = Path('posts') / 'example.md'
    contents = path.read_text()
    assert 'updated:' not in contents

    server_name = 'example.com'
    set_config_field('url', server_name)
    base_url = f'http://{server_name}'

    with run_preview(run_start) as preview_base_url:
        response = http_get(preview_base_url + '/feed.atom')
        assert response.status_code == 200  # noqa: PLR2004
        validate_example_feed(base_url, response.text)


def test_without_updated_build_and_preview(run_start: CliRunner) -> None:
    remove_fields_from_post('example', ('updated',))
    path = Path('posts') / 'example.md'
    contents = path.read_text()
    assert 'updated:' not in contents

    server_name = 'example.com'
    set_config_field('url', server_name)
    base_url = f'http://{server_name}'

    result = run_start.invoke(build)
    assert result.exit_code == 0, result.output
    assert re.search(SUCCESS_REGEX, result.output)

    published = get_example_field('published')

    feed_path = Path('build') / 'feed.atom'
    feed_contents = feed_path.read_text()

    validate_example_feed(base_url, feed_contents)

    with run_preview(run_start) as preview_base_url:
        updated = get_example_field('updated')
        response = http_get(preview_base_url + '/feed.atom')
        assert response.status_code == 200  # noqa: PLR2004
        validate_example_feed(
            base_url,
            response.text,
            published=published,
            updated=updated,
        )


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
    feed_contents = feed_path.read_text()

    updated = get_example_field('updated')
    assert get_example_field('updated') is not None

    base_url = f'http://{server_name}'
    validate_example_feed(
        base_url,
        feed_contents,
        published=published,
        updated=updated,
    )

    with run_preview(run_start) as preview_base_url:
        response = http_get(preview_base_url + '/feed.atom')
        assert response.status_code == 200  # noqa: PLR2004
        validate_example_feed(
            base_url,
            response.text,
            published=published,
            updated=updated,
        )


def test_without_updated_no_build_preview(run_start: CliRunner) -> None:
    # Set published as datetime so updated will be set
    published = '2014-10-30T10:29:00+00:00'
    set_example_field('published', published)

    assert 'updated:' not in (Path('posts') / 'example.md').read_text()

    server_name = 'example.com'
    set_config_field('url', server_name)

    base_url = f'http://{server_name}'
    with run_preview(run_start) as preview_base_url:
        updated = get_example_field('updated')
        assert updated is not None
        response = http_get(preview_base_url + '/feed.atom')
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
    feed_contents = feed_path.read_text()

    # Parse the XML string
    root = ET.fromstring(feed_contents)  # noqa: S314
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    subtitle = root.find('atom:subtitle', ns)

    assert subtitle is not None
    assert subtitle.text == description
