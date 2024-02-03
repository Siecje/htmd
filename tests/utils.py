from pathlib import Path


SUCCESS_REGEX = (
    'All posts are correctly formatted.\n'
    r'Static site was created in [\w\/\\]*build\n'
)


def remove_fields_from_example_post(field_names: tuple[str, ...]) -> None:
    example_post_path = Path('posts') / 'example.md'
    with example_post_path.open('r') as post:
        lines = post.readlines()
    with example_post_path.open('w') as post:
        for line in lines:
            for field_name in field_names:
                if field_name in line:
                    break
            else:
                post.write(line)
