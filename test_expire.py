import pytest
from expire import expire
from datetime import datetime, timedelta


@pytest.fixture
def no_extent():
    return [
        '-r', '* * * * *',
    ]


@pytest.fixture
def one_minute():
    return [
        '-r', '* * * * * +1 minute',
    ]


def test_help(cli_runner):
    result = cli_runner.invoke(expire, ['--help'])
    assert "A tool for expiring old backups." in result.output


def test_empty_directory(cli_runner, no_extent):
    with cli_runner.isolated_filesystem():
        result = cli_runner.invoke(expire, no_extent + ['-d', '.'])
        assert result.output == "warning: no files to delete\n"


def test_empty_tmpdir(cli_runner, tmpdir, no_extent):
    tmpdir.mkdir("sub")
    result = cli_runner.invoke(expire, no_extent + ['-d', tmpdir / 'sub'])
    assert result.output == "warning: no files to delete\n"


def test_occupied_tmpdir(cli_runner, tmpdir, no_extent):
    p = tmpdir.mkdir("sub").join("hello.txt")
    p.write("content")
    result = cli_runner.invoke(expire, no_extent + ['-d', tmpdir / 'sub'])
    assert result.output.startswith('would keep')
    assert result.output.split('\n')[0].endswith('hello.txt')


# hmmmm -- should this raise an exception instead?
def test_nonexistent_tmpdir(cli_runner, tmpdir, no_extent):
    tmpdir.mkdir("sub")
    result = cli_runner.invoke(expire, no_extent + ['-d', tmpdir / 'bus'])
    assert result.output == "warning: no files to delete\n"


def test_with_freezegun(cli_runner, tmpdir, one_minute, freezer):
    now = datetime.now()
    two_minutes = timedelta(minutes=2)
    p = tmpdir.mkdir("sub").join("hello.txt")
    p.write("content")
    result = cli_runner.invoke(expire, one_minute + ['-d', tmpdir / 'sub'])
    assert result.output.startswith('would keep')
    assert result.output.split('\n')[0].endswith('hello.txt')
    freezer.move_to(str(now + two_minutes))
    result = cli_runner.invoke(expire, one_minute + ['-d', tmpdir / 'sub'])
    assert result.output.startswith('would delete')
    assert result.output.split('\n')[0].endswith('hello.txt')
    assert p.read() == "content"


def test_with_freezegun_nodryrun(cli_runner, tmpdir, one_minute, freezer):
    now = datetime.now()
    two_minutes = timedelta(minutes=2)
    p = tmpdir.mkdir("sub").join("hello.txt")
    p.write("content")
    result = cli_runner.invoke(expire, one_minute + ['-d', tmpdir / 'sub',
                                                     '--no-dryrun'])
    assert result.output.startswith('kept')
    assert result.output.split('\n')[0].endswith('hello.txt')
    assert p.read() == "content"
    freezer.move_to(str(now + two_minutes))
    result = cli_runner.invoke(expire, one_minute + ['-d', tmpdir / 'sub',
                                                     '--no-dryrun'])
    assert result.output.startswith('deleted')
    assert result.output.split('\n')[0].endswith('hello.txt')
    assert not p.exists()
