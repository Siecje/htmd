import datetime
from pathlib import Path

from click.testing import CliRunner
from htmd.cli.build import build

from utils import (
    get_example_field,
    remove_fields_from_post,
    set_example_field,
)


def test_build_post_404_invalid_date_year(run_start: CliRunner) -> None:
    # Linking to a post with incorrect values
    # for dates will cause 404 and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /14/10/30/example/\n"
    )

    about_path = Path('pages') / 'about.html'
    with about_path.open('r') as about_file:
        lines = about_file.readlines()

    new_line = '''<p><a href="{{ url_for('posts.post', year=14, month='10', day='30', path='example') }}">DNE link</a></p>\n'''  # noqa: E501
    with about_path.open('w') as about_file:
        for line in lines:
            if '<p>This is the about page.</p>' in line:
                about_file.write(new_line)
            else:
                about_file.write(line)

    result = run_start.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_post_404_invalid_date_month(run_start: CliRunner) -> None:
    # Linking to a post with incorrect values
    # for dates will cause 404 and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /2014/1/30/example/\n"
    )

    about_path = Path('pages') / 'about.html'
    with about_path.open('r') as about_file:
        lines = about_file.readlines()

    new_line = '''<p><a href="{{ url_for('posts.post', year=2014, month='1', day='30', path='example') }}">DNE link</a></p>\n'''  # noqa: E501
    with about_path.open('w') as about_file:
        for line in lines:
            if '<p>This is the about page.</p>' in line:
                about_file.write(new_line)
            else:
                about_file.write(line)

    result = run_start.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_post_404_invalid_date_day(run_start: CliRunner) -> None:
    # Linking to a post with incorrect values
    # for dates will cause 404 and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /2014/10/3/example/\n"
    )

    about_path = Path('pages') / 'about.html'
    with about_path.open('r') as about_file:
        lines = about_file.readlines()

    new_line = '''<p><a href="{{ url_for('posts.post', year=2014, month='10', day='3', path='example') }}">DNE link</a></p>\n'''  # noqa: E501
    with about_path.open('w') as about_file:
        for line in lines:
            if '<p>This is the about page.</p>' in line:
                about_file.write(new_line)
            else:
                about_file.write(line)

    result = run_start.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_post_404_different_date(run_start: CliRunner) -> None:
    # Linking to a page with the wrong date
    # will cause a 404 status code
    # and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /2014/10/29/example/\n"
    )
    about_path = Path('pages') / 'about.html'
    with about_path.open('r') as about_file:
        lines = about_file.readlines()

    new_line = '''<p><a href="{{ url_for('posts.post', year=2014, month='10', day='29', path='example') }}">DNE link</a></p>\n'''  # noqa: E501
    with about_path.open('w') as about_file:
        for line in lines:
            if '<p>This is the about page.</p>' in line:
                about_file.write(new_line)
            else:
                about_file.write(line)

    result = run_start.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_year_404_incorrect(run_start: CliRunner) -> None:
    # Linking to a page with the wrong date
    # will cause a 404 status code
    # and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /14/\n"
    )

    about_path = Path('pages') / 'about.html'
    with about_path.open('r') as about_file:
        lines = about_file.readlines()

    new_line = '''<p><a href="{{ url_for('posts.year_view', year=14) }}">DNE link</a></p>\n'''  # noqa: E501
    with about_path.open('w') as about_file:
        for line in lines:
            if '<p>This is the about page.</p>' in line:
                about_file.write(new_line)
            else:
                about_file.write(line)

    result = run_start.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_year_404_no_posts(run_start: CliRunner) -> None:
    # Linking to a page with the wrong date
    # will cause a 404 status code
    # and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /2013/\n"
    )
    about_path = Path('pages') / 'about.html'
    with about_path.open('r') as about_file:
        lines = about_file.readlines()

    new_line = '''<p><a href="{{ url_for('posts.year_view', year=2013) }}">DNE link</a></p>\n'''  # noqa: E501
    with about_path.open('w') as about_file:
        for line in lines:
            if '<p>This is the about page.</p>' in line:
                about_file.write(new_line)
            else:
                about_file.write(line)

    result = run_start.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_month_404_no_posts(run_start: CliRunner) -> None:
    # Linking to a page with the wrong date
    # will cause a 404 status code
    # and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /2014/01/\n"
    )

    about_path = Path('pages') / 'about.html'
    with about_path.open('r') as about_file:
        lines = about_file.readlines()

    new_line = '''<p><a href="{{ url_for('posts.month_view', year=2014, month='01') }}">DNE link</a></p>\n'''  # noqa: E501
    with about_path.open('w') as about_file:
        for line in lines:
            if '<p>This is the about page.</p>' in line:
                about_file.write(new_line)
            else:
                about_file.write(line)

    result = run_start.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_day_404_no_posts(run_start: CliRunner) -> None:
    # Linking to a page with the wrong date
    # will cause a 404 status code
    # and stop the build
    expected_output = (
        'All posts are correctly formatted.\n'
        "Unexpected status '404 NOT FOUND' on URL /2014/10/29/\n"
    )

    about_path = Path('pages') / 'about.html'
    with about_path.open('r') as about_file:
        lines = about_file.readlines()

    new_line = '''<p><a href="{{ url_for('posts.day_view', year=2014, month='10', day='29') }}">DNE link</a></p>\n'''  # noqa: E501
    with about_path.open('w') as about_file:
        for line in lines:
            if '<p>This is the about page.</p>' in line:
                about_file.write(new_line)
            else:
                about_file.write(line)

    result = run_start.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_time_is_added_to_dates(run_start: CliRunner) -> None:
    # published and updated are dates without times
    # both field should have time 00:00 added
    before_published = '2014-10-30'
    before_updated = '2026-01-03'
    set_example_field('published', before_published)
    set_example_field('updated', before_updated)
    example_path = Path('posts') / 'example.md'

    result = run_start.invoke(build)
    assert result.exit_code == 0

    with example_path.open('r') as post_file:
        a_lines = post_file.readlines()
    after_published = next(
        line.replace('published: ', '').strip()
        for line in a_lines
        if 'published: ' in line
    )
    after_updated = next(
        line.replace('updated: ', '').strip()
        for line in a_lines
        if 'updated: ' in line
    )

    # Time should be added to published
    assert after_published is not None
    assert after_published.startswith(before_published)
    assert 'T' in after_published
    assert len(after_published) > len(before_published)
    b_published_datetime = datetime.datetime.fromisoformat(before_published)
    a_published_datetime = datetime.datetime.fromisoformat(after_published)

    # Before didn't have a time
    assert b_published_datetime.hour == 0
    assert b_published_datetime.minute == 0
    assert b_published_datetime.second == 0

    assert a_published_datetime == datetime.datetime.combine(
        b_published_datetime.date(),
        datetime.time.min,
        tzinfo=datetime.UTC,
    )

    # Time should be added to updated
    assert after_updated is not None
    assert 'T' in after_updated
    assert len(after_updated) > len(before_updated)
    b_updated_datetime_str = before_updated.replace('updated:', '').strip()
    a_updated_datetime_str = after_updated.replace('updated:', '').strip()
    b_updated_datetime = datetime.datetime.fromisoformat(b_updated_datetime_str)
    a_updated_datetime = datetime.datetime.fromisoformat(a_updated_datetime_str)

    # Before didn't have a time
    assert b_updated_datetime.hour == 0
    assert b_updated_datetime.minute == 0
    assert b_updated_datetime.second == 0

    assert a_updated_datetime == datetime.datetime.combine(
        b_updated_datetime,
        datetime.time.min,
        tzinfo=datetime.UTC,
    )


def test_build_published_time_is_added(run_start: CliRunner) -> None:
    # If there is no published/updated time then
    # build will add it
    # verify that time is not there
    # ensure correct time is added
    remove_fields_from_post('example', ('updated',))
    example_path = Path('posts') / 'example.md'
    with example_path.open('r') as post_file:
        b_lines = post_file.readlines()
    before_published = next(
        line.replace('published: ', '').strip()
        for line in b_lines
        if 'published: ' in line
    )

    result = run_start.invoke(build)
    assert result.exit_code == 0
    with example_path.open('r') as post_file:
        a_lines = post_file.readlines()

    after_published = next(
        line.replace('published: ', '').strip()
        for line in a_lines
        if 'published: ' in line
    )
    # verify updated is not added
    assert 'updated' not in ''.join(a_lines)

    assert after_published.startswith(before_published)
    assert len(after_published) > len(before_published)
    b_datetime = datetime.datetime.fromisoformat(before_published)
    a_datetime = datetime.datetime.fromisoformat(after_published)

    # Before didn't have a time
    assert b_datetime.hour == 0
    assert b_datetime.minute == 0
    assert b_datetime.second == 0

    assert a_datetime == datetime.datetime.combine(
        b_datetime.date(),
        datetime.time.min,
        tzinfo=datetime.UTC,
    )


def test_build_updated_is_added(run_start: CliRunner) -> None:
    """
    Verify updated is added.

    If published has a time and there is no updated
    then build will add updated with time.
    """
    remove_fields_from_post('example', ('updated',))

    # First build adds time to published
    result = run_start.invoke(build)
    assert result.exit_code == 0

    # Change post so that updated will be added.
    set_example_field('title', 'test_build_updated_is_added')

    # Second build adds updated with time
    result2 = run_start.invoke(build)
    assert result2.exit_code == 0

    example_path = Path('posts') / 'example.md'
    with example_path.open('r') as post_file:
        a_lines = post_file.readlines()
    for a_line in a_lines:  # pragma: no branch
        if 'updated: ' in a_line:
            a_updated = a_line
            break

    a_datetime_str = a_updated.replace('updated: ', '').strip()
    a_datetime = datetime.datetime.fromisoformat(a_datetime_str)

    date_with_current_time = datetime.datetime.now(datetime.UTC).replace(
        year=a_datetime.year,
        month=a_datetime.month,
        day=a_datetime.day,
    )
    time_difference = abs(a_datetime - date_with_current_time)

    # Verify published time is close to now
    threshold_seconds = 60
    assert time_difference.total_seconds() < threshold_seconds


def test_build_updated_is_added_once(run_start: CliRunner) -> None:
    remove_fields_from_post('example', ('updated',))

    # First build adds published time
    result = run_start.invoke(build)
    assert result.exit_code == 0

    with (Path('posts') / 'example.md').open('a') as example_file:
        example_file.write('\nAnother line to change the hash.\n')

    # Second build adds updated
    result2 = run_start.invoke(build)
    assert result2.exit_code == 0

    example_path = Path('posts') / 'example.md'
    with example_path.open('r') as post_file:
        a_lines = post_file.readlines()
    count = 0
    for a_line in a_lines:
        if 'updated' in a_line:
            count += 1

    assert count == 1


def test_build_without_published(run_start: CliRunner) -> None:
    remove_fields_from_post('example', ('published', 'updated'))

    # First build adds published time
    result = run_start.invoke(build)
    assert result.exit_code == 0
    example_path = Path('posts') / 'example.md'
    with example_path.open('r') as post_file:
        a_lines = post_file.readlines()
    count = 0
    for a_line in a_lines:
        if 'published' in a_line:
            count += 1

    assert count == 1


def test_build_with_post_in_each_month(run_start: CliRunner) -> None:
    post_path = Path('posts') / 'example.md'
    with post_path.open('r') as post_file:
        lines = post_file.readlines()
    for month in range(1, 13):
        with post_path.open('w') as post_file:
            for line in lines:
                if 'published:' in line:
                    post_file.write(f'published: 2014-{month:02}-03\n')
                else:
                    post_file.write(line)

        result = run_start.invoke(build)
        assert result.exit_code == 0


def test_published_date_updated_datetime(run_start: CliRunner) -> None:
    before_published = get_example_field('published')
    assert isinstance(before_published, str)
    before_dt = datetime.date.fromisoformat(before_published)
    assert not isinstance(before_dt, datetime.datetime)

    utc_now = datetime.datetime.now(datetime.UTC)
    set_example_field('updated', utc_now.isoformat())

    result = run_start.invoke(build)
    assert result.exit_code == 0

    # published time was added
    published_str = get_example_field('published')
    assert isinstance(published_str, str)
    published = datetime.datetime.fromisoformat(published_str)
    assert isinstance(published, datetime.datetime)
    assert published.time() == datetime.time.min


def test_without_published_updated_datetime(run_start: CliRunner) -> None:
    updated_dt = datetime.datetime(
        year=2026,
        month=1,
        day=4,
        tzinfo=datetime.UTC,
    )
    set_example_field('updated', updated_dt.isoformat())
    remove_fields_from_post('example', ('published',))

    # Change hash so post is considered updated
    set_example_field(
        '_hash',
        'testwithoutpublishedupdateddatetime',
    )

    now = datetime.datetime.now(datetime.UTC)
    result = run_start.invoke(build)
    assert result.exit_code == 0

    # published is set to updated
    published_str = get_example_field('published')
    assert isinstance(published_str, str)
    published = datetime.datetime.fromisoformat(published_str)
    assert published == updated_dt

    # updated is set to now
    updated_str = get_example_field('updated')
    assert isinstance(updated_str, str)
    updated = datetime.datetime.fromisoformat(updated_str)
    assert updated.date() == now.date()


def test_without_published_updated_date(run_start: CliRunner) -> None:
    updated_date = datetime.date(year=2026, month=1, day=4)
    set_example_field('updated', updated_date.isoformat())
    remove_fields_from_post('example', ('published',))

    result = run_start.invoke(build)
    assert result.exit_code == 0

    # published is set to updated date with time 00:00
    published_str = get_example_field('published')
    assert isinstance(published_str, str)
    published = datetime.datetime.fromisoformat(published_str)
    assert published.date() == updated_date
    assert published.time() == datetime.time.min

    # updated date is unchanged and time is set to 00:00
    updated_str = get_example_field('updated')
    assert isinstance(updated_str, str)
    updated = datetime.datetime.fromisoformat(updated_str)
    assert updated.date() == updated_date
    assert updated.time() == datetime.time.min


def test_without_published_updated_date_hash_changed(run_start: CliRunner) -> None:
    updated_date = datetime.date(year=2026, month=1, day=4)
    set_example_field('updated', updated_date.isoformat())
    remove_fields_from_post('example', ('published',))

    set_example_field('_hash', 'testwithoutpublishedupdateddatehashchanged')
    result = run_start.invoke(build)
    assert result.exit_code == 0

    # published is set to updated date with time 00:00
    published_str = get_example_field('published')
    assert isinstance(published_str, str)
    published = datetime.datetime.fromisoformat(published_str)
    assert published.date() == updated_date
    assert published.time() == datetime.time.min

    # updated date is unchanged and time is set to 00:00
    updated_str = get_example_field('updated')
    assert isinstance(updated_str, str)
    updated = datetime.datetime.fromisoformat(updated_str)
    assert updated.date() == updated_date
    assert updated.time() == datetime.time.min
