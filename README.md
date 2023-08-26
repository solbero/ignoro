<p align="center"><img src="https://raw.githubusercontent.com/solbero/ignoro/main/logo.png" alt="Logo" /></p>
<p align="center"><em>Create .gitignore files with ease from your command line!</em></p>
<p align="center">
  <a href="https://github.com/solbero/ignoro/actions/workflows/test.yml">
    <img alt="Tests" src="https://img.shields.io/github/actions/workflow/status/solbero/ignoro/test.yml?label=tests">
  </a>
  <a href="https://github.com/solbero/ignoro/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/github/license/solbero/ignoro">
  </a>
</p>

## About

Ignoro is a command line interface designed to help you quickly create and modify `.gitignore` files for your projects. The CLI uses one or more of the 569 templates supplied by [gitignore.io](https://www.toptal.com/developers/gitignore) to craft the perfect `.gitignore` for your project.

### Features

* [x] Create a `.gitignore` file based on one or more templates.
* [x] List and search available templates from [gitignore.io](https://www.toptal.com/developers/gitignore).
* [ ] Add one or more templates from an existing `.gitignore` file.
* [ ] Remove one or more templates from an existing `.gitignore` file.
* [ ] Show templates used in an exiting `.gitignore` file.

## Usage

### `ignoro`

Create or modify gitignore files based on templates from [gitignore.io](https://www.toptal.com/developers/gitignore). 

```
> ignoro [OPTIONS] COMMAND [ARGS]
```

**Options**

* `--install-completion`: Install completion for the current shell. 
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**

* `create`: Create a new gitignore file.
* `list`: List available gitignore templates

### `ignoro list`

Lists all gitignore templates. If no search term is provided, all available templates will be listed.

```sh
> ignoro [OPTIONS] list [TERM]
```

**Options**

* `--help`: Show this message and exit.

**Arguments**

* `term`: Term used to search available templates. 

### `ignoro create`

Create a new gitignore file. If no path is provided, the file will be created in the current directory.

```sh
> ignoro create [OPTIONS] TEMPLATES...
```

**Options**

* `--path`: Create a gitignore file at this path.
* `--show-gitignore`:  Show the content of the gitignore instead of creating a file.
* `--help`: Show this message and exit.’

**Arguments**

*  `templates`: Templates to include in gitignore file. [required]
