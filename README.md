# Python project quick scripts

**Define simple development scripts in `pyproject.toml`**

Developing a Python project usually involves many tasks: setting up, installing
prerequisites, building, testing, cleaning up build products, etc. It can be
difficult to remember which program to run to perform a given task for a given
project, particularly when many different tools are being used.

**ppqs** defines simple (*"quick"*) scripts in `pyproject.toml`, and provides a
command-line utility -- `ppqs` -- to run them. In this way **ppqs** hides the
details of whatever dependency/virtual environment manager, build front-end,
test harness, etc. the project uses behind a simple interface.

Here is an example of **ppqs** being used for its own project:

```bash
$ ppqs --help
Quick scripts for Python project: ppqs

Usage: ppqs {init,lint,build,test,clean}

Scripts:
  init   Initialise project
  lint   Perform linting checks
  build  Build project
  test   Run tests
  clean  Clean up build files
```

Scripts are always run from the project root directory, i.e. the directory
containing `pyproject.toml`. `ppqs` traverses back through parent directories
until it finds the root directory. It is therefore safe to run `ppqs` from any
sub-directory within the project directory tree.

## Script definition in `pyproject.toml`

**ppqs** scripts are simple lists of commands which are run in sequence. If a
command errors, the remainder of the script is aborted.

Scripts are defined in `pyproject.toml` under the `[tool.ppqs.scripts]`
section. Script names may contain only lowercase letters (`[a-z]`) and dashes
(`-`). Scripts may be single or multi-line strings: commands are separated by
newlines, and command arguments are separated by spaces.

```toml
[tool.ppqs.scripts]
init = "command"
lint = """
command
"""
build = """
command1 -v
command2 -q
"""
```

Scripts may also be defined as lists of lists, i.e. a list of commands, each of
which is a list of arguments:

```toml
[tool.ppqs.scripts]
test = [
    ["command1"],
    ["command2", "-vv"],
]
clean = [
    ["command"],
]
```

If a script contains an ellipsis (`...`) it is replaced with any additional
arguments passed to `ppqs`. For example, the following script:

```toml
[tool.ppqs.scripts]
print-something = "echo ..."
```

may be run as
```bash
$ ppqs print-something Hi
Hi
```

Scripts may also be defined in their own section, which permit a few options:

```toml
[tool.ppqs.scripts.init]
description = "Initialise project"
print_header = true
script = """
command
"""

[tool.ppqs.scripts.build]
# default description = "Run build script"
# default print_header = false
script = [
    ["command1", "-v"],
    ["command2", "-q"],
]
"""

```

where:

* `description` [optional]: description of the script which appears in `ppqs
  --help`. Default is `Run {name} script` where `name` is the script name.

* `print_header` [optional]: If true, print a header before running each command
  in the script. The header consists of the command to be run, centred on the
  console and padded with `*`s. Default is false.

Commands are *not* parsed to the shell, so e.g. wildcards are not expanded. If
the features of a shell script are needed (wildcards, conditional statements,
etc.), one can write a helper script, e.g. `scripts/lots-to-do.py`, which may
then be called by `ppqs` as:

```toml
[tool.ppqs.scripts]
lots-to-do = [["python", "scripts/lots-to-do.py"]]
```
