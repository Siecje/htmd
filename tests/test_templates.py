from click.testing import CliRunner
from htmd.cli.templates import templates


def test_templates(run_start: CliRunner) -> None:
    expected_output = (
        'templates/404.html was created.\n'
        'templates/_layout.html already exists and was not created.\n'
        'templates/_list.html was created.\n'
        'templates/all_posts.html was created.\n'
        'templates/all_tags.html was created.\n'
        'templates/author.html was created.\n'
        'templates/day.html was created.\n'
        'templates/index.html was created.\n'
        'templates/month.html was created.\n'
        'templates/post.html was created.\n'
        'templates/tag.html was created.\n'
        'templates/year.html was created.\n'
    )
    result = run_start.invoke(templates)
    assert result.exit_code == 0
    assert result.output == expected_output


def test_templates_without_folder() -> None:
    expected_output = 'templates/ directory not found.\n'
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(templates)
    assert result.exit_code == 1
    assert result.stderr == expected_output
