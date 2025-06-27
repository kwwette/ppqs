# SPDX-FileCopyrightText: 2025 Karl Wette
#
# SPDX-License-Identifier: MIT

"""Test find_pyproject()."""

import pytest

from py_proj_quick_scripts import (
    MissingPyProjectError,
    find_pyproject,
)

from . import in_dir, write_file


def test_find_pyproject(tmp_path):
    """Test find_pyproject()."""

    with in_dir(tmp_path):
        with pytest.raises(MissingPyProjectError):
            find_pyproject()

    pyproject_path = tmp_path / "pyproject.toml"
    write_file(pyproject_path, "[tool.ppqs.scripts]")

    with in_dir(pyproject_path.parent):
        assert find_pyproject() == pyproject_path

    with in_dir(pyproject_path.parent / "subdir"):
        assert find_pyproject() == pyproject_path

    with in_dir(pyproject_path.parent / "subdir" / "subdir"):
        assert find_pyproject() == pyproject_path
