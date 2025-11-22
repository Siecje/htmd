from collections.abc import Generator

from click.testing import CliRunner
from htmd.cli import start
import pytest


@pytest.fixture(scope='function')  # noqa: PT003
def run_start() -> Generator[CliRunner]:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        assert result.exit_code == 0
        # Tests code is run here
        yield runner
