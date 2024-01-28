from click.testing import CliRunner
from htmd.cli import preview


def test_preview(run_start: CliRunner) -> None:
    result = run_start.invoke(preview)
    # Why is this 5?
    expected_exit_code = 5
    assert result.exit_code == expected_exit_code
