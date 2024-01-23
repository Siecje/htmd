from click.testing import CliRunner
from htmd.cli import preview, start


def test_preview() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(start)
        result = runner.invoke(preview)
    # Why is this 5?
    expected_exit_code = 5
    assert result.exit_code == expected_exit_code
