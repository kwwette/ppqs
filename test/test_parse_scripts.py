# SPDX-FileCopyrightText: 2025 Karl Wette
#
# SPDX-License-Identifier: MIT

"""Test parse_scripts()."""

from contextlib import nullcontext
from pathlib import Path

import pytest

from py_proj_quick_scripts import (
    InvalidScriptError,
    parse_scripts,
)

from . import in_dir, write_file


@pytest.mark.parametrize(
    "script_toml,expectation",
    [
        pytest.param(
            """
            [some.section]
            """,
            pytest.raises(
                InvalidScriptError, match=r"non-empty '\[tool.ppqs.scripts\]' section"
            ),
            id="missing section",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts]
            """,
            pytest.raises(
                InvalidScriptError, match=r"non-empty '\[tool.ppqs.scripts\]' section"
            ),
            id="empty section",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts]
            init = 123
            """,
            pytest.raises(
                InvalidScriptError, match="either a string or a list of lists"
            ),
            id="wrong type",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts]
            init = "pip install -r requirements.txt"
            """,
            nullcontext(
                {
                    "init": {
                        "description": "Run init script",
                        "print-header": False,
                        "bash-complete-file-glob": None,
                        "commands": [["pip", "install", "-r", "requirements.txt"]],
                    }
                }
            ),
            id="string script",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts]
            init = '''
            pip install -r requirements.txt
            pre-commit install
            '''
            """,
            nullcontext(
                {
                    "init": {
                        "description": "Run init script",
                        "print-header": False,
                        "bash-complete-file-glob": None,
                        "commands": [
                            ["pip", "install", "-r", "requirements.txt"],
                            ["pre-commit", "install"],
                        ],
                    }
                }
            ),
            id="multi-line string script",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts]
            -invalid-name = "something"
            """,
            pytest.raises(InvalidScriptError, match="may not start with '-'"),
            id="script name starts with dash",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts]
            name_contains-2-invalid-characters = "something"
            """,
            pytest.raises(InvalidScriptError, match="may not contain characters '_2'"),
            id="script name invalid characters",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts]
            some-script = { description = "something", another_key = "invalid"}
            """,
            pytest.raises(
                InvalidScriptError, match="may not contain keys 'another_key'"
            ),
            id="script invalid keys",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts.init]
            description = "Initialise project"
            script = "pip install -r requirements.txt"
            """,
            nullcontext(
                {
                    "init": {
                        "description": "Initialise project",
                        "print-header": False,
                        "bash-complete-file-glob": None,
                        "commands": [["pip", "install", "-r", "requirements.txt"]],
                    }
                }
            ),
            id="string script with description",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts.init]
            description = "Initialise project"
            script = [
                "some_commands",
            ]
            """,
            pytest.raises(
                InvalidScriptError, match="either a string or a list of lists"
            ),
            id="script is not list of lists",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts]
            init = [
                ["pip", "install", "-r", "requirements.txt"],
            ]
            """,
            nullcontext(
                {
                    "init": {
                        "description": "Run init script",
                        "print-header": False,
                        "bash-complete-file-glob": None,
                        "commands": [["pip", "install", "-r", "requirements.txt"]],
                    }
                }
            ),
            id="list script",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts.init]
            description = "Initialise project"
            print-header = true
            script = [
                ["pip", "install", "-r", "requirements.txt"],
            ]
            """,
            nullcontext(
                {
                    "init": {
                        "description": "Initialise project",
                        "print-header": True,
                        "bash-complete-file-glob": None,
                        "commands": [["pip", "install", "-r", "requirements.txt"]],
                    }
                }
            ),
            id="list script with description",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts.init]
            description = "Initialise project"
            script = [
                ["pip", "install", "-r", "requirements.txt"],
                ["pre-commit", "install"],
            ]
            """,
            nullcontext(
                {
                    "init": {
                        "description": "Initialise project",
                        "print-header": False,
                        "bash-complete-file-glob": None,
                        "commands": [
                            ["pip", "install", "-r", "requirements.txt"],
                            ["pre-commit", "install"],
                        ],
                    }
                }
            ),
            id="multi-line list script with description",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts]
            paths = [
                ["echo", ["/tmp"]],
            ]
            """,
            pytest.raises(InvalidScriptError, match="must be a relative path"),
            id="list script with absolute path",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts]
            paths = [
                ["echo", ["a", "b"]],
            ]
            """,
            nullcontext(
                {
                    "paths": {
                        "description": "Run paths script",
                        "print-header": False,
                        "bash-complete-file-glob": None,
                        "commands": [["echo", Path("a", "b")]],
                    }
                }
            ),
            id="list script with relative path",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts]
            paths = [
                ["echo", ["*", "b"]],
            ]
            """,
            pytest.raises(
                InvalidScriptError,
                match="may contain wildcards only in the last element",
            ),
            id="list script with path and invalid wildcard",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts.no-script]
            script = "ppqs script-does-not-exist"
            """,
            pytest.raises(
                InvalidScriptError,
                match="does not exist",
            ),
            id="recursive script does not exist",
        ),
        pytest.param(
            """
            [tool.ppqs.scripts.test]
            bash-complete-file-glob = "test/**/test_*.py"
            script = "run-tests ..."
            """,
            nullcontext(
                {
                    "test": {
                        "description": "Run test script",
                        "print-header": False,
                        "bash-complete-file-glob": "test/**/test_*.py",
                        "commands": [["run-tests", "..."]],
                    }
                }
            ),
            id="string script with complete file glob",
        ),
    ],
)
def test_parse_scripts(tmp_path, script_toml, expectation):
    """Test parse_scripts()."""

    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_toml = f"""
    [project]
    name = "test"
    {script_toml}
    """

    write_file(pyproject_path, pyproject_toml)

    with in_dir(tmp_path):
        with expectation as expected_result:
            project_name, scripts = parse_scripts(pyproject_path)
            assert project_name == "test"
            assert scripts == expected_result
