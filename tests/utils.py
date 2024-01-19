from pathlib import Path


def remove_fields_from_example_post(field_names):
    with (Path('posts') / 'example.md').open('r') as post:
        lines = post.readlines()
    with (Path('posts') / 'example.md').open('w') as post:
        for line in lines:
            for field_name in field_names:
                if field_name in line:
                    break
            else:
                post.write(line)
