from pathlib import Path
import shutil

from click.testing import CliRunner
import requests

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
        requests.Session() as session,
    ):
        response = http_get(
            base_url + f'/2014/10/30/{post_path.stem}/',
            session=session,
        )
        set_example_password_value('')
        assert response.status_code == 200  # noqa: PLR2004
        expected = 'password-protect.js'
        assert expected not in response.text
        wait_for_str_not_in_file(post_path, 'password: \n')
        password = get_example_field('password')
        assert password != ''
        response = http_get(
            base_url + f'/2014/10/30/{post_path.stem}/',
            session=session,
        )
        assert response.status_code == 200  # noqa: PLR2004
        assert expected in response.text


def test_new_protected_post_during_preview(run_start: CliRunner) -> None:
    set_example_password_value('')
    shutil.copy(Path('posts') / 'example.md', Path('copy.md'))
    with run_preview(run_start) as base_url:
        post_path = Path('copy.md').rename(Path('posts') / 'copy.md')
        wait_for_str_not_in_file(post_path, 'password: \n')
        password = get_post_field(post_path.stem, 'password')
        assert password != ''
        response = http_get(base_url + f'/2014/10/30/{post_path.stem}/')
        assert response.status_code == 200  # noqa: PLR2004
        assert 'password-protect.js' in response.text
