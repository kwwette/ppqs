import os
import textwrap
from contextlib import contextmanager
from pathlib import Path


def write_file(path, contents):
    """
    Write `contents` to a text file `path`.
    """
    path.write_text(textwrap.dedent(contents).strip())


@contextmanager
def in_dir(path):
    """
    Temporarily change working directory to `path`, creating as needed.
    """
    path.mkdir(parents=True, exist_ok=True)
    cwd = Path.cwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(cwd)
