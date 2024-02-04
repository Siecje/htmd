from collections.abc import Generator

from click.testing import CliRunner
from flask import Flask
from flask.testing import FlaskClient
from htmd.cli import start
import pytest


@pytest.fixture(scope='module')
def run_start() -> Generator[CliRunner, None, None]:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        assert result.exit_code == 0
        # Tests code is run here
        yield runner


@pytest.fixture()
def flask_app(run_start: CliRunner) -> Flask:
    from htmd.site import app
    app.config.update({
        'TESTING': True,
    })
    return app


@pytest.fixture()
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
