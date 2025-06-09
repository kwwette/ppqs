import os
import re
import sys
from pathlib import Path

if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

__author__ = "Karl Wette"
__version__ = "0.1"


class MissingPyProjectError(Exception):
    """
    Raise if 'pyproject.toml' could not be found.
    """

    pass


class InvalidScriptError(Exception):
    """
    Raise for invalid 'pyproject.toml' script errors.
    """

    def __init__(self, pyproject_path, msg):
        self.pyproject_path = pyproject_path
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self):
        return f"{self.pyproject_path}: {self.msg}"


def find_pyproject():
    """
    Look for pyproject.toml in current/parent directories.
    """

    # Start in the current directory
    current_dir = starting_dir = Path.cwd()

    # Traverse down directory parents until just before root
    while len(current_dir.parts) > 1:

        # Stop when user no longer has write access to parent directory
        # - excludes any pyproject.toml in home directory, /tmp, etc.
        if not os.access(current_dir.parent, os.W_OK):
            break

        # If pyproject.toml is in this directory, return its path
        pyproject_path = current_dir / "pyproject.toml"
        if os.access(pyproject_path, os.F_OK | os.R_OK):
            return pyproject_path

        # Look in parent directory
        current_dir = current_dir.parent

    msg = f"'pyproject.toml' could not be found in '{starting_dir}' or its parent directories"
    raise MissingPyProjectError(msg)


def parse_scripts(pyproject_path):
    """
    Parse scripts from pyproject.toml.
    """

    # Read pyproject.toml
    pyproject_toml = tomllib.load(pyproject_path.open("rb"))
    project_name = pyproject_toml["project"]["name"]
    try:
        scripts_toml = pyproject_toml["tool"]["ppqs"]["scripts"]
    except KeyError:
        scripts_toml = {}
    if not scripts_toml:
        msg = "does not contain a non-empty '[tool.ppqs.scripts]' section"
        raise InvalidScriptError(pyproject_path, msg)

    # Parse scripts
    scripts = {}
    for script_name, script_toml in scripts_toml.items():

        # Check name
        if script_name.startswith("-"):
            msg = "script name '{script_name}' may not start with '-'"
            raise InvalidScriptError(pyproject_path, msg)
        invalid_chars = re.sub(r"[a-z-]", "", script_name)
        if len(invalid_chars) > 0:
            msg = f"script name '{script_name}' may not contain characters '{invalid_chars}'"
            raise InvalidScriptError(pyproject_path, msg)

        # Create default description
        script_description = f"Run {script_name} script"
        script_commands_toml = script_toml

        if isinstance(script_toml, dict):

            # Check for invalid keys
            invalid_keys = [
                k for k in script_toml.keys() if k not in ("description", "script")
            ]
            if len(invalid_keys) > 0:
                invalid_keys_str = "', '".join(invalid_keys)
                msg = (
                    f"script '{script_name}' may not contain keys '{invalid_keys_str}'"
                )
                raise InvalidScriptError(pyproject_path, msg)

            script_description = str(script_toml.get("description", script_description))
            script_commands_toml = script_toml["script"]

        msg = f"script '{script_name}' may be either a string or a list of lists"
        if isinstance(script_commands_toml, str):

            # Parse a script as a string
            script_commands = [
                line.split()
                for line in script_commands_toml.splitlines()
                if len(line.strip()) > 0
            ]

        elif isinstance(script_commands_toml, list):

            # Parse a script as a list of lists
            script_commands = []
            for line in script_commands_toml:
                if not isinstance(line, list):
                    raise InvalidScriptError(pyproject_path, msg)
                script_line = []
                for arg in line:
                    if isinstance(arg, list):

                        # List arguments are treated as paths
                        arg_path = Path(*arg)
                        if arg_path.is_absolute():
                            msg2 = f"path argument '{arg_path}' must be a relative path"
                            raise InvalidScriptError(pyproject_path, msg2)

                        script_line.append(str(arg_path))

                    else:
                        script_line.append(arg)

                script_commands.append(script_line)

        else:
            raise InvalidScriptError(pyproject_path, msg)

        scripts[script_name] = {
            "description": script_description,
            "commands": script_commands,
        }

    return project_name, scripts
