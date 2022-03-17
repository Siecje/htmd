from click.testing import CliRunner
from htmd.cli import preview, start


def test_preview():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(preview)
    assert result.exit_code == 5
