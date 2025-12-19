from collections.abc import Generator

from click.testing import CliRunner
from flask import Flask
from htmd import site
from htmd.cli.start import start
import pytest


@pytest.fixture(scope='function')  # noqa: PT003
def run_start() -> Generator[CliRunner]:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        assert result.exit_code == 0
        # Tests code is run here
        yield runner


@pytest.fixture(scope='module')
def run_start_module() -> Generator[CliRunner]:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        assert result.exit_code == 0
        # Tests code is run here
        yield runner


@pytest.fixture
def flask_app(run_start_module: CliRunner) -> Flask:  # noqa: ARG001
    app = site.init_app()
    app.config.update({
        'FLATPAGES_AUTO_RELOAD': True,
        'TESTING': True,
    })
    return app
