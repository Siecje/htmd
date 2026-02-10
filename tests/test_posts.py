import datetime

from click.testing import CliRunner
from htmd.site.posts import Posts
import requests

from utils import http_get, remove_fields_from_post, set_example_field
from utils_preview import run_preview


def test_Posts_without_app() -> None:  # noqa: N802
    posts = Posts()
    assert posts._app is None  # noqa: SLF001
    assert posts.published_posts == []
    assert posts.show_drafts is False
    # Doesn't error and can still change show_drafts
    posts.reload(show_drafts=True)
    assert posts.show_drafts is True
    assert posts.published_posts == []


def test_tag_with_draft_without_published(run_start: CliRunner) -> None:
    tag = 'first'
    remove_fields_from_post('example', ('published',))
    set_example_field('tags', f'[{tag}]')
    set_example_field('draft', 'true')
    today = datetime.datetime.now(tz=datetime.UTC)
    year = today.year
    month = today.strftime('%m')
    day = today.strftime('%d')
    with (
        run_preview(run_start, ['--drafts']) as base_url,
        requests.Session() as session,
    ):
        response = http_get(base_url + f'/tags/{tag}/', session=session)
        assert response.status_code == 200  # noqa: PLR2004
        response = http_get(
            base_url + f'/{year}/{month}/{day}/example/',
            session=session,
        )
        assert response.status_code == 200  # noqa: PLR2004
