import pytest
from expire import expire


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


def test_cwd_no_extent(cli_runner, no_extent):
    result = cli_runner.invoke(expire, no_extent + ['-d', '.'])
    assert "would keep" in result.output


def test_cwd_short_extent(cli_runner, one_minute):
    result = cli_runner.invoke(expire, one_minute + ['-d', '.'])
    assert "would delete" in result.output


def test_empty_directory(cli_runner, no_extent):
    with cli_runner.isolated_filesystem():
        result = cli_runner.invoke(expire, no_extent + ['-d', '.'])
        assert result.output == ""


def test_empty_tmpdir(cli_runner, tmpdir, no_extent):
    tmpdir.mkdir("sub")
    result = cli_runner.invoke(expire, no_extent + ['-d', tmpdir / 'sub'])
    assert result.output == ''


def test_occupied_tmpdir(cli_runner, tmpdir, no_extent):
    p = tmpdir.mkdir("sub").join("hello.txt")
    p.write("content")
    result = cli_runner.invoke(expire, no_extent + ['-d', tmpdir / 'sub'])
    assert result.output.startswith('would keep')
    assert result.output.strip().endswith('hello.txt')


# hmmmm
def test_nonexistent_tmpdir(cli_runner, tmpdir, no_extent):
    tmpdir.mkdir("sub")
    result = cli_runner.invoke(expire, no_extent + ['-d', tmpdir / 'bus'])
    assert result.output == ''
