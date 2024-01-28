from click.testing import CliRunner
from htmd.cli import start
import pytest


@pytest.fixture(scope='module')
def run_start():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        assert result.exit_code == 0
        # Tests code is run here
        yield


@pytest.fixture()
def flask_app(run_start):
    from htmd.site import app
    app.config.update({
        'TESTING': True,
    })
    yield app


@pytest.fixture()
def client(flask_app):
    return flask_app.test_client()


def test_author_does_not_exist(client) -> None:
    # If the author doesn't exist it will be a 404
    response = client.get("/author/dne/")
    assert 404 == response.status_code


def test_page_does_not_exist(client) -> None:
    # Ensure htmd preview matches build
    # Only pages will be served
    # before this change pages.page was serving templates
    response = client.get("/author/")
    assert 404 == response.status_code
