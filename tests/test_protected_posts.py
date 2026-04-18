from pathlib import Path
import shutil

from click.testing import CliRunner
from htmd.cli.build import build
import niquests

from utils import (
    get_example_field,
    get_post_field,
    http_get,
    set_example_password_value,
    wait_for_str_not_in_file,
)
from utils_preview import run_preview


def test_set_protected_during_preview(run_start: CliRunner) -> None:
    post_path = Path('posts') / 'example.md'
    with (
        run_preview(run_start) as base_url,
        niquests.Session() as session,
    ):
        response = http_get(
            base_url + f'/2014/10/30/{post_path.stem}/',
            session=session,
        )
        set_example_password_value('')
        assert response.status_code == 200  # noqa: PLR2004
        expected = 'password-protect.js'
        assert response.text is not None
        assert expected not in response.text
        wait_for_str_not_in_file(post_path, 'password: \n')
        password = get_example_field('password')
        assert password != ''
        response = http_get(
            base_url + f'/2014/10/30/{post_path.stem}/',
            session=session,
        )
        assert response.status_code == 200  # noqa: PLR2004
        assert response.text is not None
        assert expected in response.text


def test_new_protected_post_during_preview(run_start: CliRunner) -> None:
    set_example_password_value('')
    password_dir = Path('posts') / 'password-protect'

    shutil.copy(Path('posts') / 'example.md', Path('copy.md'))
    with run_preview(run_start) as base_url:
        post_path = Path('posts') / 'copy.md'
        shutil.copy(Path('copy.md'), post_path)
        wait_for_str_not_in_file(post_path, 'password: \n')
        password = get_post_field(post_path.stem, 'password')
        assert password != ''
        response = http_get(base_url + f'/2014/10/30/{post_path.stem}/')
        assert response.status_code == 200  # noqa: PLR2004
        assert response.text is not None
        assert 'password-protect.js' in response.text

        # create new post in password-protect/
        password_dir.mkdir(exist_ok=True)
        post_path = Path('copy.md').rename(password_dir / 'dst.md')
        wait_for_str_not_in_file(post_path, 'password: \n')
        post_path_in_posts_dir = str(post_path.relative_to('posts').with_suffix(''))
        password = get_post_field(post_path_in_posts_dir, 'password')
        assert password != ''
        post_url = post_path_in_posts_dir.replace('password-protect/', '')
        response = http_get(base_url + f'/2014/10/30/{post_url}/')
        assert response.status_code == 200  # noqa: PLR2004
        assert response.text is not None
        assert 'password-protect.js' in response.text


def test_new_protected_post_in_sub_dir_during_preview(run_start: CliRunner) -> None:
    set_example_password_value('')
    password_dir = Path('posts') / 'password-protect'

    shutil.copy(Path('posts') / 'example.md', Path('copy.md'))
    subdir = Path('posts') / 'subdir'
    subdir.mkdir()
    with run_preview(run_start) as base_url:
        post_path = subdir / 'copy.md'
        shutil.copy(Path('copy.md'), post_path)
        wait_for_str_not_in_file(post_path, 'password: \n')
        post_url = str(post_path.relative_to('posts').with_suffix(''))
        password = get_post_field(post_url, 'password')
        assert password != ''
        response = http_get(base_url + f'/2014/10/30/{post_url}/')
        assert response.status_code == 200  # noqa: PLR2004
        assert response.text is not None
        assert 'password-protect.js' in response.text

        # create new post in password-protect/
        password_dir.mkdir(exist_ok=True)
        password_sub_dir = password_dir / 'subdir'
        password_sub_dir.mkdir()
        post_path = Path('copy.md').rename(password_sub_dir / 'dst.md')
        wait_for_str_not_in_file(post_path, 'password: \n')
        post_path_in_posts_dir = str(post_path.relative_to('posts').with_suffix(''))
        password = get_post_field(post_path_in_posts_dir, 'password')
        assert password != ''
        post_url = post_path_in_posts_dir.replace('password-protect/', '')
        response = http_get(base_url + f'/2014/10/30/{post_url}/')
        assert response.status_code == 200  # noqa: PLR2004
        assert response.text is not None
        assert 'password-protect.js' in response.text


def test_password_protect_in_sub_directory(run_start: CliRunner) -> None:
    protected_dir = Path('posts') / 'password-protect' / 'private' / 'secrets'
    protected_dir.mkdir(parents=True, exist_ok=True)

    post_file = protected_dir / 'hidden.md'

    post_content = (
        '---\n'
        'title: Secret Post\n'
        'published: 2026-04-18\n'
        'author: Author\n'
        'password: true\n'
        '...\n'
        '<p>This is encrypted content.</p>\n'
    )
    post_file.write_text(post_content)

    result = run_start.invoke(build)
    assert result.exit_code == 0

    build_path = (
        Path('build') / '2026' / '04' / '18'
        / 'private' / 'secrets' / 'hidden' / 'index.html'
    )
    assert build_path.is_file()
    contents = build_path.read_text()

    assert 'cipherHTML' in contents
    assert 'This is encrypted content.' not in contents
