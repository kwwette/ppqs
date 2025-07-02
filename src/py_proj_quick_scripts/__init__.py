# SPDX-FileCopyrightText: 2025 Karl Wette
#
# SPDX-License-Identifier: MIT

"""Python project quick scripts."""

import glob
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

__author__ = "Karl Wette"


class MissingPyProjectError(Exception):
    """Raise if 'pyproject.toml' could not be found."""

    pass


class InvalidScriptError(Exception):
    """Raise for invalid 'pyproject.toml' script errors."""

    def __init__(self, pyproject_path, msg):
        """Initialise exception."""
        self.pyproject_path = pyproject_path
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self):
        return f"{self.pyproject_path}: {self.msg}"


def find_pyproject():
    """Look for pyproject.toml in current/parent directories."""

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
    """Parse scripts from pyproject.toml."""

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

    # Get defaults
    try:
        default_script_print_header = bool(
            pyproject_toml["tool"]["ppqs"]["defaults"]["print-header"]
        )
    except KeyError:
        default_script_print_header = False
    try:
        default_bash_complete_file_glob = bool(
            pyproject_toml["tool"]["ppqs"]["defaults"]["bash-complete-file-glob"]
        )
    except KeyError:
        default_bash_complete_file_glob = None

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
        script_print_header = default_script_print_header
        script_bash_complete_file_glob = default_bash_complete_file_glob
        script_commands_toml = script_toml

        if isinstance(script_toml, dict):

            # Check for invalid keys
            invalid_keys = [
                k
                for k in script_toml.keys()
                if k
                not in (
                    "description",
                    "print-header",
                    "bash-complete-file-glob",
                    "script",
                )
            ]
            if len(invalid_keys) > 0:
                invalid_keys_str = "', '".join(invalid_keys)
                msg = (
                    f"script '{script_name}' may not contain keys '{invalid_keys_str}'"
                )
                raise InvalidScriptError(pyproject_path, msg)

            script_description = str(script_toml.get("description", script_description))
            script_print_header = bool(
                script_toml.get("print-header", script_print_header)
            )
            script_bash_complete_file_glob = script_toml.get(
                "bash-complete-file-glob", script_bash_complete_file_glob
            )
            if script_bash_complete_file_glob is not None:
                script_bash_complete_file_glob = str(script_bash_complete_file_glob)
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
                        if any("*" in a for a in arg[:-1]):
                            msg2 = f"path argument '{arg_path}' may contain wildcards only in the last element"
                            raise InvalidScriptError(pyproject_path, msg2)
                        if arg_path.is_absolute():
                            msg2 = f"path argument '{arg_path}' must be a relative path"
                            raise InvalidScriptError(pyproject_path, msg2)

                        script_line.append(arg_path)

                    else:
                        script_line.append(arg)

                script_commands.append(script_line)

        else:
            raise InvalidScriptError(pyproject_path, msg)

        scripts[script_name] = {
            "description": script_description,
            "print-header": script_print_header,
            "bash-complete-file-glob": script_bash_complete_file_glob,
            "commands": script_commands,
        }

    # Check that recursively run scripts exist
    for script in scripts.values():
        for command in script["commands"]:
            cmd_exec = command[0]
            if cmd_exec == "ppqs":
                script_name_r = command[1]
                if script_name_r not in scripts:
                    msg = f"script {script_name_r}' does not exist"
                    raise InvalidScriptError(pyproject_path, msg)

    return project_name, scripts


def print_help(project_name, scripts):
    """Print help."""
    script_names = ",".join(scripts.keys())
    max_script_name_len = max(len(script_name) for script_name in scripts)
    list_of_scripts = "\n".join(
        "  "
        + script_name.ljust(max_script_name_len, " ")
        + "  "
        + script["description"][0].upper()
        + script["description"][1:]
        for script_name, script in scripts.items()
    )
    print(
        textwrap.dedent(
            f"""\
            Quick scripts for Python project: {project_name}

            Usage: ppqs {{{script_names}}}

            Scripts:
            """
        )
        + list_of_scripts
    )


def run_script(scripts, script_name, argv, cwd, has_been_run):
    """Run a script."""

    col_width = shutil.get_terminal_size().columns

    # Mark script has having been run
    has_been_run.add(script_name)

    script = scripts[script_name]
    for command in script["commands"]:
        cmd = []

        for arg in command:
            if isinstance(arg, Path):
                if "*" in arg.parts[-1]:

                    # Expand wildcards in last path element
                    cmd.extend(sorted(glob.glob(str(arg), recursive=False)))

                else:
                    cmd.append(str(arg))

            elif arg == "...":

                # Replace "..." in command with arguments
                cmd.extend(argv)

            else:
                cmd.append(arg)

        if cmd[0] == "ppqs":

            # Recursively run script
            # - silently ignore scripts which have already been run
            script_name_r = cmd[1]
            if script_name_r not in has_been_run:
                run_script(scripts, script_name_r, cmd[2:], cwd, has_been_run)
            continue

        elif cmd[0] == "python":

            # Use same Python as ppqs to run Python scripts
            cmd[0] = sys.executable

        # Print header
        if script["print-header"]:
            cmd_str = " ".join(cmd)
            header = f"*** ppqs {script_name}: {cmd_str} ***".center(col_width, "*")
            print(header, flush=True)

        # Run command
        retn = subprocess.run(cmd, shell=False, cwd=cwd)
        if retn.returncode != 0:
            raise SystemExit(retn.returncode)


def bash_completion():  # pragma: no cover
    """Perform Bash command-line completion."""

    # Parse scripts
    pyproject_path = find_pyproject()
    _, scripts = parse_scripts(pyproject_path)

    # Get current command line
    line = os.environ["COMP_LINE"]
    words = line.split()

    if line.endswith(" ") and len(words) == 1:

        # Complete full script name, e.g.:
        # $ ppqs <TAB><TAB>
        for script_name in scripts:
            print(script_name)
        return

    if not line.endswith(" ") and len(words) == 2:

        # Complete partial script name, e.g.:
        # $ ppqs nam<TAB>
        for script_name in scripts:
            if script_name.startswith(words[-1]):
                print(script_name)
        return

    script_name = words[1]
    script_bash_complete_file_glob = scripts[script_name]["bash-complete-file-glob"]
    if script_bash_complete_file_glob is not None:

        # Generate list of files to complete on
        project_dir = pyproject_path.parent
        files = [
            str(f.relative_to(project_dir))
            for f in project_dir.glob(script_bash_complete_file_glob)
        ]

        if line.endswith(" "):

            # Complete full script name, e.g.:
            # $ ppqs script <TAB><TAB>
            for file_name in files:
                print(file_name)
            return

        else:

            # Complete partial script name, e.g.:
            # $ ppqs script fil<TAB>
            for file_name in files:
                if file_name.startswith(words[-1]):
                    print(file_name)
            return


def cli(*argv):
    """Parse command line."""

    argv = [str(a) for a in (argv or sys.argv[1:] or ["--help"])]

    if argv[0] == "--bash-completion":  # pragma: no cover

        # Perform Bash command-line completion, suppress any errors
        try:
            bash_completion()
        except Exception:
            pass

    else:

        # Parse scripts
        pyproject_path = find_pyproject()
        project_name, scripts = parse_scripts(pyproject_path)

        # Parse command line
        if argv[0] in ("-h", "-help", "--help"):
            print_help(project_name, scripts)
            raise SystemExit(1)
        elif argv[0] not in scripts:
            msg = f"unknown script '{argv[0]}'"
            raise InvalidScriptError(pyproject_path, msg)
        else:
            cwd = pyproject_path.parent
            has_been_run = set()
            run_script(scripts, argv[0], argv[1:], cwd, has_been_run)
