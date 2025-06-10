import os

import pytest

from py_proj_quick_scripts import InvalidScriptError, cli

from . import in_dir, write_file


@pytest.fixture
def pyproject_path(tmp_path):
    """
    Write pyproject.toml for command-line tests.
    """

    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_toml = """
    [project]
    name = "test"
    [tool.ppqs.scripts.exit]
    description = "Exits"
    print-header = true
    script = "python -c 'import sys; sys.exit(1)'"
    [tool.ppqs.scripts.echo]
    description = "Echoes"
    script = [
        ["python", "-c", "import sys; print(*sys.argv[1:])", "..."],
    ]
    [tool.ppqs.scripts.echo-path]
    script = [
        ["python", "-c", "import sys; print(*sys.argv[1:])", ["afile"], ["subdir", "bfile"]],
    ]
    [tool.ppqs.scripts.echo-wildcard]
    script = [
        ["python", "-c", "import sys; print(*sys.argv[1:])", ["subdir", "*.txt"]],
    ]
    """

    write_file(pyproject_path, pyproject_toml)

    return pyproject_path


def test_help(pyproject_path):
    """
    Test command line help.
    """

    with in_dir(pyproject_path.parent):
        with pytest.raises(SystemExit):
            cli("--help")


def test_notest(pyproject_path):
    """
    Test a non-existent test.
    """

    with in_dir(pyproject_path.parent):
        with pytest.raises(InvalidScriptError):
            cli("notest")


def test_exit(pyproject_path):
    """
    Test `exit` script.
    """

    with in_dir(pyproject_path.parent):
        with pytest.raises(SystemExit):
            cli("exit")


def test_echo(pyproject_path, capfd):
    """
    Test `echo` script.
    """

    with in_dir(pyproject_path.parent):
        cli("echo", "Hello")
        captured = capfd.readouterr()
        assert captured.out == "Hello\n"
        assert captured.err == ""


def test_echo_path(pyproject_path, capfd):
    """
    Test `echo-path` script.
    """

    with in_dir(pyproject_path.parent):
        cli("echo-path")
        captured = capfd.readouterr()
        assert captured.out == "afile subdir/bfile\n".replace("/", os.sep)
        assert captured.err == ""


def test_echo_wildcard(pyproject_path, capfd):
    """
    Test `echo-wildcard` script.
    """

    with in_dir(pyproject_path.parent) as wd:
        subdir = wd / "subdir"
        subdir.mkdir()
        write_file(subdir / "a.txt", "Some text")
        write_file(subdir / "b.txt", "Some more text")
        cli("echo-wildcard")
        captured = capfd.readouterr()
        assert captured.out == "subdir/a.txt subdir/b.txt\n".replace("/", os.sep)
        assert captured.err == ""
