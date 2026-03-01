from pathlib import Path

from click.testing import CliRunner
from htmd.cli.build import build

from utils import set_config_field, set_example_contents


def test_code_blocks(run_start: CliRunner) -> None:
    """
    Ensure fenced code blocks are only rendered when markdown extensions are enabled.

    Steps:
    1) create a post with a fenced code block
    2) run build without any markdown extensions and verify no rendered code block
    3) add a [markdown] section with extensions to config.toml
    4) run build and verify the built post contains a code block
    """
    # 1) write a fenced code block into the example post body
    code_block = '```python\nprint("hello world")\n```\n'
    set_example_contents(code_block)

    # Remove [markdown] section from config
    cfg_path = Path('config.toml')
    cfg_lines = cfg_path.read_text().splitlines(keepends=True)
    # Remove a possible multi-line extensions = [ .. ] block
    out_lines: list[str] = []
    for line in cfg_lines:  # pragma: no branch
        if line == '[markdown]\n':
            break
        out_lines.append(line)
    cfg_path.write_text(''.join(out_lines))

    # 2) build without markdown extensions
    result = run_start.invoke(build)
    assert result.exit_code == 0

    build_post = Path('build') / '2014' / '10' / '30' / 'example' / 'index.html'
    assert build_post.is_file()
    contents = build_post.read_text()

    # When markdown extensions aren't enabled the fenced block should not be
    # rendered as a block-level code element (no <pre> or codehilite wrapper).
    assert '<pre' not in contents
    assert 'class="codehilite"' not in contents

    # 3) enable markdown extensions by appending a [markdown] section
    extensions = ['codehilite', 'fenced_code']
    set_config_field('markdown', 'extensions', extensions)

    # 4) rebuild and verify code block is rendered
    result = run_start.invoke(build)
    assert result.exit_code == 0

    build_post = Path('build') / '2014' / '10' / '30' / 'example' / 'index.html'
    assert build_post.is_file()
    contents = build_post.read_text()

    # With the extensions enabled we expect a rendered code block (either
    # a <pre> or a codehilite wrapper).
    assert '<pre' in contents
    assert 'class="codehilite"' in contents
