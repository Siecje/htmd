from htmd.site.posts import Posts


def test_Posts_without_app() -> None:  # noqa: N802
    posts = Posts()
    assert posts._app is None  # noqa: SLF001
    assert posts.published_posts == []
    assert posts.show_drafts is False
    # Doesn't error and can still change show_drafts
    posts.reload(show_drafts=True)
    assert posts.show_drafts is True
    assert posts.published_posts == []
