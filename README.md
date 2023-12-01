<div align="center"><img src="https://raw.githubusercontent.com/solbero/ignoro/main/logo.png" alt="Logo" /></div>
<p align="center"><em>Create .gitignore files with ease from your command line!</em></p>
<p align="center">
  <a href="https://github.com/solbero/ignoro/actions/workflows/test.yml">
    <img alt="Tests" src="https://img.shields.io/github/actions/workflow/status/solbero/ignoro/test.yml?label=tests"/>
  </a>
  <a href="https://codecov.io/gh/solbero/ignoro">
    <img alt="Coverage" src="https://img.shields.io/codecov/c/github/solbero/ignoro"/>
  </a>
  <a href="https://pypi.org/project/ignoro/">
    <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/ignoro">
  </a>
  <a href="https://pypi.org/project/ignoro/">
    <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/ignoro"/>
  </a>
  <a href="https://github.com/solbero/ignoro/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/github/license/solbero/ignoro">
  </a>
</p>

## About

Ignoro is a command line interface designed to help you quickly create and modify `.gitignore` files for your projects. The CLI uses one or more of the 550+ templates supplied by [gitignore.io](https://www.toptal.com/developers/gitignore) to craft the perfect `.gitignore` for your project.

## Features

* [x] Search for templates at [gitignore.io](https://www.toptal.com/developers/gitignore).
* [x] Show the content of a template from [gitignore.io](https://www.toptal.com/developers/gitignore).
* [x] Create a `.gitignore` file based on one or more templates.
* [x] List templates used in a `.gitignore` file.
* [x] Add one or more templates to a `.gitignore` file.
* [x] Remove one or more templates from a `.gitignore` file.

## Installation

**Using `pipx` (recommended)**

```sh
pipx install ignoro
```

**Using `pip`**

```sh
pip install --user ignoro
```

## Usage

### `ignoro`

Create or modify a `.gitignore` file based on templates from [gitignore.io](https://www.toptal.com/developers/gitignore).

```
ignoro [OPTIONS] COMMAND [ARGS]...
```

**Options**

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**

* `add`: Add templates to a `.gitignore` file.
* `create`: Create a `.gitignore` file.
* `list`: List templates in a `.gitignore` file.
* `remove`: Remove templates from a `.gitignore` file.
* `search`: Search for templates at [gitignore.io](https://www.toptal.com/developers/gitignore).

### `ignoro add`

Add templates to a `.gitignore` file. If no path is provided, the templates will be added to the `.gitignore` file in the current directory.

```sh
ignoro add [OPTIONS] TEMPLATES...
```

**Arguments**

*  `TEMPLATES`: Templates to add to `.gitignore` file. [required]

**Options**

* `--path`: Add templates to `.gitignore` file at this path.
* `--show-gitignore`:  Show the result of the add command instead of writing a file.
* `--help`: Show this message and exit.

### `ignoro create`

Create a `.gitignore` file. If no path is provided, the `.gitignore` file will be created in the current directory.

```sh
ignoro create [OPTIONS] TEMPLATES...
```

**Arguments**

*  `TEMPLATES`: Templates to include in `.gitignore` file. [required]

**Options**

* `--path`: Create a `.gitignore` file at this path.
* `--show-gitignore`:  Show the result of the create command instead of writing a file.
* `--help`: Show this message and exit.

### `ignoro list`

List templates in a `.gitignore` file. If no path is provided, the templates from the .gitignore file in the current directory will be listed.

```sh
ignoro list [OPTIONS]
```

**Options**

* `--path`: List templates in `.gitignore` file at this path.
* `--help`: Show this message and exit.

### `ignoro remove`

Remove templates from a `.gitignore` file. If no path is provided, the templates will be removed from the `.gitignore` file in the current directory.

```sh
ignoro remove [OPTIONS] TEMPLATES...
```

**Arguments**

*  `TEMPLATES`: Templates to remove from `.gitignore` file. [required]

**Options**

* `--path`: Remove templates from `.gitignore` file at this path.

* `--show-gitignore`:  Show the result of the remove command instead of writing a file.
* `--help`: Show this message and exit.’

### `ignoro search`

Search for templates at [gitignore.io](https://www.toptal.com/developers/gitignore). If no search term is provided, all available templates will be listed.

```sh
ignoro search [OPTIONS] [TERM]
```

**Arguments**

*  `TERM`: Term used to search [gitignore.io](https://www.toptal.com/developers/gitignore).

**Options**

* `--help`: Show this message and exit.’

### `ignoro show`

Show a template from [gitignore.io](https://www.toptal.com/developers/gitignore). If no no match is found, an error will be raised.

```sh
ignoro show [OPTIONS] TEMPLATE
```

**Arguments**

* `TEMPLATE`:  Template to show from gitignore.io. [required]

**Options**

* `--help`: Show this message and exit.

## Development

**Setup**

Ignoro uses [PDM](https://pdm.fming.dev/) to manage dependencies and virtual environments. To get started, first [install PDM](https://pdm-project.org/latest/#installation). Then, install the project dependencies using the command:

```sh
pdm install
```

**Run**

To run the CLI, use the command:

```sh
pdm run ignoro
```

**Test**

Ignoro uses [pytest](https://docs.pytest.org/) for testing. To run the test suite, use the following command:

```sh
pdm run pytest
```

**Formating and Linting**

Ignoro uses [black](https://black.readthedocs.io/en/stable/) and [Ruff](https://docs.astral.sh/ruff/)