from collections.abc import Iterable
from pathlib import Path


SUCCESS_REGEX = (
    'All posts are correctly formatted.\n'
    r'Static site was created in .*build\n'
)


def remove_fields_from_post(
    path: str,
    field_names: Iterable[str],
) -> None:
    example_post_path = Path('posts') / f'{path}.md'
    with example_post_path.open('r') as post:
        lines = post.readlines()
    with example_post_path.open('w') as post:
        for line in lines:
            skip = any(line.startswith(f'{field}:') for field in field_names)
            if skip:
                continue
            post.write(line)


def set_example_field(field: str, value: str) -> None:
    remove_fields_from_post('example', (field,))
    post_path = Path('posts') / 'example.md'

    with post_path.open('r') as post_file:
        lines = post_file.readlines()

    with post_path.open('w') as post_file:
        for line in lines:
            if line == '...\n':
                field_line = f'{field}: {value}\n'
                post_file.write(field_line)
            post_file.write(line)


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

    with post_path.open('r') as post_file:
        lines = post_file.readlines()

    new_lines = []
    for line in lines:  # pragma: no branch
        if line == '...\n':
            break
        new_lines.append(line)
    new_lines.append(text)

    with post_path.open('w') as post_file:
        for line in lines:
            post_file.write(line)


def set_example_subtitle(value: str) -> None:
    set_example_field('subtitle', value)


def set_config_field(field: str, value: str | bool) -> None: # noqa: FBT001
    config_path = Path('config.toml')
    with config_path.open('r') as config_file:
        lines = config_file.readlines()

    with config_path.open('w') as config_file:
        for line in lines:
            if line.startswith(f'{field} ='):
                if isinstance(value, bool):
                    config_file.write(f'{field} = {str(value).lower()}\n')
                else:
                    config_file.write(f'{field} = "{value}"\n')
            else:
                config_file.write(line)


def get_example_field(field: str) -> None | str:
    example_path = Path('posts') / 'example.md'
    with example_path.open('r') as post_file:
        lines = post_file.readlines()
    value = None
    for line in lines:
        if line.startswith(f'{field}:'):
            value = line.split(f'{field}:')[1].strip()
            break

    return value
