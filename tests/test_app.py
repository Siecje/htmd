import threading
import time

from flask import Flask
from flask.testing import FlaskClient
from htmd import site
import pytest

from utils import set_example_to_draft


@pytest.fixture
def client(flask_app: Flask) -> FlaskClient:
    return flask_app.test_client()


def test_author_does_not_exist(client: FlaskClient) -> None:
    # If the author doesn't exist it will be a 404
    response = client.get('/author/dne/')
    assert response.status_code == 404  # noqa: PLR2004


def test_page_does_not_exist(client: FlaskClient) -> None:
    # Ensure htmd preview matches build
    # Only pages will be served
    # before this change pages.page was serving templates
    response = client.get('/author/')
    assert response.status_code == 404  # noqa: PLR2004


def test_draft_does_not_exist(client: FlaskClient) -> None:
    # Ensure htmd preview matches build
    # Only pages will be served
    # before this change pages.page was serving templates
    response = client.get('/draft/dne/')
    assert response.status_code == 404  # noqa: PLR2004


def test_tag_does_not_exist(client: FlaskClient) -> None:
    found = 200
    not_found = 404
    # If the author doesn't exist it will be a 404
    response = client.get('/tags/dne/')
    assert response.status_code == not_found

    set_example_to_draft()
    response = client.get('/tags/first/')
    assert response.status_code == not_found
    response = client.get('/author/Taylor/')
    assert response.status_code == not_found
    response = client.get('/2014/10/30/example/')
    assert response.status_code == not_found

    site.reload_posts(show_drafts=True)
    response = client.get('/tags/first/')
    assert response.status_code == found
    response = client.get('/author/Taylor/')
    assert response.status_code == found


def test_changes_view(client: FlaskClient) -> None:
    response = client.get('/changes')
    assert response.status_code == 200  # noqa: PLR2004
    assert response.mimetype == 'text/event-stream'


def test_changes_view_event_stream(flask_app: Flask) -> None:
    def in_thread(
        start_event: threading.Event,
        end_event: threading.Event,
        url: str,
        changes: list[bytes],
        client: FlaskClient,
    ) -> None:
        start_event.set()
        with client:
            response = client.get(url)
            for data in response.response:  # pragma: no branch
                assert isinstance(data, bytes)
                changes.append(data)
                if len(changes) >= 2:  # noqa: PLR2004
                    break
        end_event.set()

    changes: list[bytes] = []
    client = flask_app.test_client()
    # Set the refresh event
    refresh_event = threading.Event()
    flask_app.config['refresh_event'] = refresh_event

    started = threading.Event()
    ended = threading.Event()
    thread = threading.Thread(
        target=in_thread,
        args=(started, ended, '/changes', changes, client),
    )
    thread.start()
    started.wait(5)

    # trigger two events
    refresh_event.set()
    while refresh_event.is_set():
        time.sleep(0.1)
    refresh_event.set()

    ended.wait(timeout=5)
    expected = [
        b'data: refresh\n\n',
        b'data: refresh\n\n',
    ]
    assert changes == expected
