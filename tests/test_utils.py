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


def test_set_post_metadata_with_multi_line_value(flask_app: Flask) -> None:
    password = '''MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDJYAdiWsLrPh7F
V7CJwvvJAxMeOijlTTacFbjNnk3pPlE5OdOFDRlFw3VCbyBZIReGgOTe1LKtCcsm
QELCOMSrGY6SnW3tnQ1Qyj7NJhVm88WHYQwhSNTpq22fJe69p05eeBvA8yUjf5qS
SToJz4mDwaaZTUc0oQjvSs4OuYskisCoHjCHtfdLEUtwJQ09MlqcpZATxHJd3Jci
3OkauGkgTtNwqN1HAodufNKCX/3PbrO2fwRb7CcbuCEPSYoPPWQt8/McCK5Mdpnp
Ak31mUrvd3v5ehBy5dOQdlobMxNyojTgdrk4DjqL2OyMAVD6GIfrokV/m+4s6n1C
JJiTfPDhAgMBAAECggEAH+kSMnvscFz/K57E2we6th9BG89JOhDdav18M+/L1n6p
XgFJAJ1TQxKr6wjzXicCydh0rCTrYsVEW72KIVSKlwxtOH7ZnnIpMS4N+/H20+zO
1oWX56cEFOU1RqdlqMhcKwHVxWJ3oPjwXxGwhevNFZkNvomYPixDNLGCFqOV+4ZN
p3CE0fuM8ni18jOHWr6z1u9XY//tlhBcluHdlQCeiuIoqlJgUIW8QWD2OCG+6aRs
OlLOQw3cqGS7Hhf+UVwtddn8GKMspxXPq69N+3sDa8zAim1f+FYJDqpOcxOyg30s
eihVkpPeDw6Em+mTrN1swpMA/f8vcJi5jU/qnMqDGwKBgQD5M9wXhfWmH7EW3yMS
HvtZ9K6+ZST5+13pQg2nyACqP2/gNZUj1h6r4OQstoK5rhbf5FMhHSp8eX3jkCLH
aPSXz5Arl/7Zou52PpOQ42dbgL58SUAv6ipDIVbFXWqAncdjBxk1Xd87ALIr8HUr
I36dpAFzFsmUKSMvlshKlkEYBwKBgQDO3jKm3de6hW22Nb1ebrOa2JIPZxywVFBY
QKoSGZwcewWv7214M6LnoheKx/l5NbEqCMefo++LUCCj7qa7UdLRKI3ojouRTWWs
+CkTfBgJx8OtKHYQXQCiL4yCSgd1fzCDmZ+moM6LpZQ3nSprJycSywFHIThFVpzU
uYTbTTFl1wKBgQDPS6hlmPWCvxIcqHkP9d24MqW5k4FywPqZsmyRiPmkpSh3JZtu
OAtDhsvHtfqAYqR8kf3kqdJRwO5LgfasUk5EilCvMry4ZaRfkCZIfCHaJ/pMgNJ4
CR4mwXDgtJiHbLgTVDBQCEpNVoLfsiKFQ/1rPKZICkiciqvORmtOQDbduQKBgFry
y5gbXnYNpW9/bvMufl4sqwKEldNcLjquq1br1XucBqMUA6/eG9f0pp8ITkEg/vP5
CjLAc1dvcfpAuSMP1TzJtKIy0V+fhH0oWX7MhxD9t6TQbh/Bk766Yu8BNwhMU/r3
tn4eotA4itJskbKscvxLLhOkokWxz5+itKtp47bfAoGBAKBTLFXAikBjRpkpg5NX
+Bo9eUZiDMoKiK2/zSishCmn12WUQE4FSSl/xttRtpS8TQplv9hdFkYUQSTxdbZk
I6UzQGcHpLQFzw2AV6rcA1RlVLrNpPQXgq1vFZAiOJotkn9oj6/3BZSPDPjkw2f5
gRdZDizOd3mXWl0Pa6u4Uh+F'''  # noqa: S105
    old_post = site.posts.get('example')
    set_post_metadata(flask_app, old_post, 'password', password)
    site.posts.reload()
    post = site.posts.get('example')
    assert post.meta['password'].rstrip() == password
    assert post.meta['author'] == old_post.meta['author']
    assert post.html == old_post.html
    assert post.meta['published'] == old_post.meta['published']
    assert post.meta['tags'] == old_post.meta['tags']
    assert post.meta['title'] == old_post.meta['title']
    assert post.meta['updated'] == old_post.meta['updated']

    # Old multi line value needs to be replaced
    new_password = password + 'A'
    set_post_metadata(flask_app, post, 'password', new_password)
    site.posts.reload()
    post = site.posts.get('example')
    assert post.meta['password'].rstrip() == new_password
    assert post.meta['author'] == old_post.meta['author']
    assert post.html == old_post.html
    assert post.meta['published'] == old_post.meta['published']
    assert post.meta['tags'] == old_post.meta['tags']
    assert post.meta['title'] == old_post.meta['title']
    assert post.meta['updated'] == old_post.meta['updated']

    # Add another field so password is not last
    new_password = password + 'AB'
    set_post_metadata(flask_app, post, 'draft', 'true')
    set_post_metadata(flask_app, post, 'password', new_password)
    site.posts.reload()
    post = site.posts.get('example')
    assert post.meta['password'].rstrip() == new_password
    assert post.meta['author'] == old_post.meta['author']
    assert post.meta['draft'] is True
    assert post.html == old_post.html
    assert post.meta['published'] == old_post.meta['published']
    assert post.meta['tags'] == old_post.meta['tags']
    assert post.meta['title'] == old_post.meta['title']
    assert post.meta['updated'] == old_post.meta['updated']


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
