import os


def remove_fields_from_example_post(field_names):
    with open(os.path.join('posts', 'example.md'), 'r') as post:
        lines = post.readlines()
    with open(os.path.join('posts', 'example.md'), 'w') as post:
        for line in lines:
            for field_name in field_names:
                if field_name in line:
                    break
            else:
                post.write(line)
