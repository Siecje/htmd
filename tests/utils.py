from pathlib import Path


SUCCESS_REGEX = (
    'All posts are correctly formatted.\n'
    r'Static site was created in .*build\n'
)


def remove_fields_from_post(path: str, field_names: tuple[str, ...]) -> None:
    example_post_path = Path('posts') / f'{path}.md'
    with example_post_path.open('r') as post:
        lines = post.readlines()
    with example_post_path.open('w') as post:
        for line in lines:
            for field_name in field_names:
                if field_name in line:
                    break
            else:
                post.write(line)


def set_example_draft_status(draft_status: str) -> None:
    remove_fields_from_post('example', ('draft',))
    post_path = Path('posts') / 'example.md'

    with post_path.open('r') as post_file:
        lines = post_file.readlines()

    with post_path.open('w') as post_file:
        for line in lines:
            if line == '...\n':
                draft_line = f'draft: {draft_status}\n'
                post_file.write(draft_line)
            post_file.write(line)


def set_example_password_value(value: str) -> None:
    remove_fields_from_post('example', ('password',))
    post_path = Path('posts') / 'example.md'

    with post_path.open('r') as post_file:
        lines = post_file.readlines()

    with post_path.open('w') as post_file:
        for line in lines:
            if line == '...\n':
                password_line = f'password: {value}\n'
                post_file.write(password_line)
            post_file.write(line)


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

