from collections.abc import Iterable
from pathlib import Path
import time

from htmd.utils import atomic_write
import requests


SUCCESS_REGEX = (
    'All posts are correctly formatted.\n'
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


def set_config_field(field: str, value: str | bool) -> None: # noqa: FBT001
    config_path = Path('config.toml')
    lines = config_path.read_text().splitlines(keepends=True)

    content = ''
    for line in lines:
        if line.startswith(f'{field} ='):
            if isinstance(value, bool):
                content += f'{field} = {str(value).lower()}\n'
            else:
                content += f'{field} = "{value}"\n'
        else:
            content += line + '\n'

    atomic_write(config_path, content)


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
