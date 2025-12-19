import datetime
from pathlib import Path

from click.testing import CliRunner
from htmd.cli.build import build

from utils import remove_fields_from_post


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

    new_line = '''<p><a href="{{ url_for('post', year=14, month='10', day='30', path='example') }}">DNE link</a></p>\n'''  # noqa: E501
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

    new_line = '''<p><a href="{{ url_for('post', year=2014, month='1', day='30', path='example') }}">DNE link</a></p>\n'''  # noqa: E501
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

    new_line = '''<p><a href="{{ url_for('post', year=2014, month='10', day='3', path='example') }}">DNE link</a></p>\n'''  # noqa: E501
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

    new_line = '''<p><a href="{{ url_for('post', year=2014, month='10', day='29', path='example') }}">DNE link</a></p>\n'''  # noqa: E501
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

    new_line = '''<p><a href="{{ url_for('year_view', year=14) }}">DNE link</a></p>\n'''
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

    new_line = '''<p><a href="{{ url_for('year_view', year=2013) }}">DNE link</a></p>\n'''  # noqa: E501
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

    new_line = '''<p><a href="{{ url_for('month_view', year=2014, month='01') }}">DNE link</a></p>\n'''  # noqa: E501
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

    new_line = '''<p><a href="{{ url_for('day_view', year=2014, month='10', day='29') }}">DNE link</a></p>\n'''  # noqa: E501
    with about_path.open('w') as about_file:
        for line in lines:
            if '<p>This is the about page.</p>' in line:
                about_file.write(new_line)
            else:
                about_file.write(line)

    result = run_start.invoke(build)
    assert result.exit_code == 1
    assert result.output == expected_output


def test_build_updated_time_is_added(run_start: CliRunner) -> None:
    # If there is no published/updated time then
    # build will add it
    # verify that time is not there
    # ensure correct time is added
    example_path = Path('posts') / 'example.md'
    with example_path.open('r') as post_file:
        b_lines = post_file.readlines()
    result = run_start.invoke(build)
    assert result.exit_code == 0
    with example_path.open('r') as post_file:
        a_lines = post_file.readlines()
    for b_line, a_line in zip(b_lines, a_lines, strict=True):
        if 'updated' in b_line:
            b_updated = b_line
            a_updated = a_line
        if 'published' in b_line:
            b_published = b_line
            a_published = a_line

    # Verify published didn't change
    assert a_published is not None
    assert b_published.strip() == a_published.strip()

    assert a_updated.startswith(b_updated.strip())
    assert len(a_updated) > len(b_updated)
    b_datetime_str = b_updated.replace('updated:', '').strip()
    a_datetime_str = a_updated.replace('updated:', '').strip()
    b_datetime = datetime.datetime.fromisoformat(b_datetime_str)
    a_datetime = datetime.datetime.fromisoformat(a_datetime_str)

    # Before didn't have a time
    assert b_datetime.hour == 0
    assert b_datetime.minute == 0
    assert b_datetime.second == 0

    date_with_current_time = datetime.datetime.now(tz=datetime.UTC).replace(
        year=a_datetime.year,
        month=a_datetime.month,
        day=a_datetime.day,
    )
    time_difference = abs(a_datetime - date_with_current_time)

    # Verify updated time is close to now
    threshold_seconds = 60
    assert time_difference.total_seconds() < threshold_seconds


def test_build_published_time_is_added(run_start: CliRunner) -> None:
    # If there is no published/updated time then
    # build will add it
    # verify that time is not there
    # ensure correct time is added
    remove_fields_from_post('example', ('updated',))
    example_path = Path('posts') / 'example.md'
    with example_path.open('r') as post_file:
        b_lines = post_file.readlines()
    result = run_start.invoke(build)
    assert result.exit_code == 0
    with example_path.open('r') as post_file:
        a_lines = post_file.readlines()
    for b_line, a_line in zip(b_lines, a_lines, strict=True):
        if 'published' in b_line:
            b_published = b_line
            a_published = a_line

    assert a_published.startswith(b_published.strip())
    assert len(a_published) > len(b_published)
    b_datetime_str = b_published.replace('published:', '').strip()
    a_datetime_str = a_published.replace('published:', '').strip()
    b_datetime = datetime.datetime.fromisoformat(b_datetime_str)
    a_datetime = datetime.datetime.fromisoformat(a_datetime_str)

    # Before didn't have a time
    assert b_datetime.hour == 0
    assert b_datetime.minute == 0
    assert b_datetime.second == 0

    date_with_current_time = datetime.datetime.now(datetime.UTC).replace(
        year=a_datetime.year,
        month=a_datetime.month,
        day=a_datetime.day,
    )
    time_difference = abs(a_datetime - date_with_current_time)

    # Verify published time is close to now
    threshold_seconds = 60
    assert time_difference.total_seconds() < threshold_seconds

    # verify updated is not added
    assert 'updated' not in ''.join(a_lines)


def test_build_updated_is_added(run_start: CliRunner) -> None:
    """
    Verify updated is added.

    If published has a time and there is no updated
    then build will add updated with time.
    """
    # Remove updated from example post
    remove_fields_from_post('example', ('updated',))
    # First build adds time to published
    result = run_start.invoke(build)
    assert result.exit_code == 0
    # Second build adds updated with time
    result2 = run_start.invoke(build)
    assert result2.exit_code == 0
    example_path = Path('posts') / 'example.md'
    with example_path.open('r') as post_file:
        a_lines = post_file.readlines()
    for a_line in a_lines:
        if 'updated' in a_line:
            a_updated = a_line

    a_datetime_str = a_updated.replace('updated:', '').strip()
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
    # Remove updated from example post
    example_path = Path('posts') / 'example.md'
    with example_path.open('r') as post_file:
        b_lines = post_file.readlines()
    with example_path.open('w') as post_file:
        for line in b_lines:
            if 'updated' not in line:
                post_file.write(line)
        # add "..." to post content
        post_file.write('...\n')

    # First build adds published time
    result = run_start.invoke(build)
    assert result.exit_code == 0
    # Second build adds updated
    result2 = run_start.invoke(build)
    assert result2.exit_code == 0
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
                if 'published' in line:
                    post_file.write(f'published: 2014-{month:02}-03\n')
                else:
                    post_file.write(line)

        result = run_start.invoke(build)
        assert result.exit_code == 0
