# Python project quick scripts

**Define simple project management scripts in `pyproject.toml`**

Developing a Python project usually involves many tasks: setting up, installing
prerequisites, building, testing, cleaning up build products, etc. It can be
difficult to remember which program to run to perform a given task for a given
project, particularly when many different tools are being used.

**ppqs** defines simple (*"quick"*) scripts in `pyproject.toml`, and provides a
command-line utility -- `ppqs` -- to run them. In this way **ppqs** hides the
details of whatever dependency/virtual environment manager, build front-end,
test harness, etc. the project uses behind a simple interface.

Here is an example of **ppqs** being used for its own project:

```
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

```
$ ppqs print-something Hi
Hi
```

`ppqs` can recursively run its own scripts, however it will only run any script
once. For example, given the following script:

```toml
[tool.ppqs.scripts]
task-init = """
echo task init
"""
task-a = """
ppqs task-init
echo task 1
"""
task-b = """
ppqs task-init
echo task 2
"""
all-tasks = """
ppqs task-a
ppqs task-b
"""
```

running `ppqs all-tasks` will only run `ppqs task-init` once:
```
$ ppqs all-tasks
task init
task 1
task 2
```

The following only applies to scripts defined as lists of lists:

* If a command argument is itself a list, it is concatenated into a path
  appropriate for the current operating system. For example,

  ```toml
  [tool.ppqs.scripts]
  do-something = [["do-something-to", ["subdir", "afile"]]]
  ```

  would run the command `do-something-to subdir/afile` on a Unix-based operating
  system.

  If the last element of the path contains a wildcard (`*`), the path is
  expanded at runtime into a list of files/directories matching the wildcard
  expression. For example, if the directory `subdir/` contained the files
  `file1.txt`, `file2.txt`, and `file3.dat`, then:

  ```toml
  [tool.ppqs.scripts]
  do-something = [["do-something-to", ["subdir", "*.txt"]]]
  ```

  would run the command `do-something-to subdir/file1.txt subdir/file2.txt`

Scripts may also be defined in their own section, which permit a few options:

```toml
[tool.ppqs.scripts.init]
description = "Initialise project"
print-header = true
script = """
command
"""

[tool.ppqs.scripts.build]
script = [
    ["command1", "-v"],
    ["command2", "-q"],
]
```

where:

* `description` *(optional)*: description of the script which appears in `ppqs
  --help`. Default is `Run {name} script` where `name` is the script name.

* `print-header` *(optional)*: If true, print a header before running each
  command in the script. The header consists of the script name and the command
  to be run, centred on the console and padded with `*`s. Default is false.

The default value of some options may be overridden in the
`[tool.ppqs.defaults]` section, e.g.

```
[tool.ppqs.defaults]
print-header = true
```

Note that commands are *not* passed to the shell, so shell features are not
available. The recommended solution is to write a helper script,
e.g. `scripts/lots-to-do.py`, which may then be called by `ppqs` as:

```toml
[tool.ppqs.scripts]
lots-to-do = [["python", "scripts/lots-to-do.py"]]
```

## Bash completion

`ppqs` support Bash command-line completion. Simply add the following command to
your `~/.bashrc` file:

```bash
complete -C "ppqs --bash-completion" ppqs
```

Typing `ppqs ` and hitting `TAB` will then show scripts available for the
current project. Typing part of a script name and hitting `TAB` will show
matching script name(s), or else complete the full name if unambiguous.

By default, Bash completion will only complete names of scripts. Each script may
additionally define a glob pattern, given as the option
`bash-complete-file-glob` under `[tool.ppqs.scripts.<script-name>]`. Files
matching that pattern (relative to the project root directory) will then be
available as completions for additional arguments to the script. Example:

```
[tool.ppqs.scripts.test]
bash-complete-file-glob = "test/**/test_*.py"
script = "run-tests ..."
```

This script will complete on any files matching `test/**/test_*.py`, and pass
the file names to the command `run-tests`.
