from collections.abc import Iterable
from pathlib import Path
import time

from htmd.utils import atomic_write
import requests


SUCCESS_REGEX = (
    'All posts are correctly formatted.\n'
    'Running Pagefind indexing...\n'
    r'Static site was created in .*build\n'
)


def remove_fields_from_post(
    path: str,
    field_names: Iterable[str],
) -> None:
    fields_to_remove = set(field_names)
    post_path = Path('posts') / f'{path}.md'

    lines = post_path.read_text().splitlines(keepends=True)
    new_lines = []
    line_iter = iter(lines)

    # Iterate until content is reached or all fields have been removed
    for line in line_iter:  # pragma: no branch
        if line.strip() == '...':
            new_lines.append(line)
            break

        parts = line.split(':', 1)
        key = parts[0]
        if len(parts) > 1 and key in fields_to_remove:
            fields_to_remove.remove(key)
            if not fields_to_remove:
                break
            continue

        new_lines.append(line)

    new_lines.extend(line_iter)
    atomic_write(post_path, ''.join(new_lines))


def set_example_field(field: str, value: str) -> None:
    post_path = Path('posts') / 'example.md'
    lines = post_path.read_text().splitlines(keepends=True)

    new_lines = []
    line_iter = iter(lines)
    field_key = f'{field}:'
    found_and_removed = False

    for line in line_iter:  # pragma: no branch
        if line.strip() == '...':
            new_lines.append(f'{field}: {value}\n')
            new_lines.append(line)
            break

        if not found_and_removed and line.startswith(field_key):
            found_and_removed = True
            continue

        new_lines.append(line)

    new_lines.extend(line_iter)
    atomic_write(post_path, ''.join(new_lines))


def set_example_draft_status(draft_status: str) -> None:
    set_example_field('draft', draft_status)


def set_example_password_value(value: str) -> None:
    set_example_field('password', value)


def set_example_to_draft() -> None:
    set_example_draft_status('true')


def set_example_to_draft_build() -> None:
    set_example_draft_status('build')


def set_example_contents(text: str) -> None:
    post_path = Path('posts') / 'example.md'

    lines = post_path.read_text().splitlines(keepends=True)

    new_lines = []
    for line in lines:  # pragma: no branch
        new_lines.append(line)
        if line == '...\n':
            break
    new_lines.append(text)

    atomic_write(post_path, ''.join(new_lines))


def set_example_subtitle(value: str) -> None:
    set_example_field('subtitle', value)


def _format_value(v: str | bool | list[str]) -> str:  # noqa: FBT001
    """
    Format a Python value for insertion into TOML.

    Supports:
    - bool -> true/false
    - str -> quoted string
    - list/tuple -> TOML array with elements formatted recursively
    """
    # Booleans must be lower-case literals in TOML
    if isinstance(v, bool):
        return str(v).lower()

    # Lists / tuples -> format each element recursively
    if isinstance(v, (list, tuple)):
        inner = ', '.join(_format_value(el) for el in v)
        return f'[{inner}]'

    # Fallback to string representation quoted
    return f'"{v}"'


def _replace_key_in_section(
    lines: list[str],
    section: str,
    field: str,
    new_line: str,
) -> tuple[list[str], bool, bool]:
    out: list[str] = []
    replaced = False
    section_found = False
    current: str | None = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            current = stripped[1:-1].strip()
            if current == section:
                section_found = True
        if current == section and line.lstrip().startswith(f'{field} ='):
            out.append(new_line if new_line.endswith('\n') else new_line + '\n')
            replaced = True
            continue
        out.append(line)
    return out, replaced, section_found


def _insert_after_section(
    lines: list[str],
    section: str,
    new_line: str,
) -> list[str]:
    out: list[str] = []
    inserted = False
    curr: str | None = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            curr = stripped[1:-1].strip()
            out.append(line)
            if curr == section and not inserted:
                out.append(
                    new_line if new_line.endswith('\n') else new_line + '\n',
                )
                inserted = True
            continue
        out.append(line)
    return out


def set_config_field(
    section: str,
    field: str,
    value: str | bool | list[str],  # noqa: FBT001
) -> None:
    """
    Set or add `field` inside `section` in `config.toml`.

    The function will replace the existing key inside the given TOML
    section. If the section exists but the key is missing it will be
    inserted immediately after the section header. If the section does
    not exist it will be appended at the end of the file and the key
    added beneath it.
    """
    config_path = Path('config.toml')
    lines = config_path.read_text().splitlines(keepends=True)

    formatted_value = _format_value(value)
    new_line = f'{field} = {formatted_value}'

    new_lines, replaced, section_found = _replace_key_in_section(
        lines,
        section,
        field,
        new_line,
    )

    if not replaced:
        if section_found:
            new_lines = _insert_after_section(new_lines, section, new_line)
        else:
            new_lines.append(f'[{section}]\n')
            new_lines.append(
                new_line if new_line.endswith('\n') else new_line + '\n',
            )

    atomic_write(config_path, ''.join(new_lines))


def remove_from_config_field(field: str) -> None:
    """
    Remove the line that starts with '<field> =' from config.toml.

    The match is performed against the start of the line (no leading
    whitespace is trimmed), so callers should pass the field name used in
    the file (e.g. 'base_path').
    """
    config_path = Path('config.toml')
    lines = config_path.read_text().splitlines(keepends=True)

    new_lines: list[str] = []
    prefix = f'{field} ='
    for line in lines:
        if line.startswith(prefix):
            # skip this line
            continue
        new_lines.append(line)

    atomic_write(config_path, ''.join(new_lines))


def get_post_field(url_path: str, field: str) -> None | str:
    example_path = Path('posts') / f'{url_path}.md'
    lines = example_path.read_text().splitlines(keepends=True)

    value = None
    for line in lines:
        if line.startswith(f'{field}:'):
            value = line.split(f'{field}:')[1].strip()
            break

    return value


def get_example_field(field: str) -> None | str:
    return get_post_field('example', field)


def wait_for_str_in_file(
    path: Path,
    value: str,
    timeout: float = 5,
) -> None:
    start_time = time.monotonic()
    content = path.read_text()
    while value not in content:  # pragma: no cover
        if time.monotonic() - start_time > timeout:
            msg = f"'{value}' not found in {path} after {timeout}s.\n"
            raise TimeoutError(msg)
        time.sleep(0.1)
        content = path.read_text()


def wait_for_str_not_in_file(
    path: Path,
    value: str,
    timeout: float = 5,
) -> None:
    start_time = time.monotonic()
    while value in path.read_text():  # pragma: no cover
        if time.monotonic() - start_time > timeout:
            msg = f'{value} still in {path} after {timeout}s.'
            raise TimeoutError(msg)
        time.sleep(0.1)


def http_get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    session: requests.Session | None = None,
    timeout: float = 1,
) -> requests.Response:
    if session is None and headers is None:
        headers = {'Connection': 'close'}
    caller = session or requests
    return caller.get(url, headers=headers, timeout=timeout)
