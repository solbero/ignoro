import pathlib

import requests
import rich
import rich.columns
import rich.console
import rich.prompt
import typer
from typing_extensions import Annotated, Optional

import ignoro

__all__ = ["app"]

app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")
stdout = rich.console.Console(color_system="auto")
stderr = rich.console.Console(color_system="auto", stderr=True, style="red")


@app.command("list")
def list_(
    term: Annotated[
        str,
        typer.Argument(help="Term used to search available templates."),
    ] = ""
):
    """
    List names of available gitignore templates.

    If no search term is provided, all available template names will be listed.
    """
    try:
        template_list = ignoro.api.TemplateList(populate=True)
    except requests.exceptions.ConnectionError:
        stderr.print(
            "Could not list template names: Failed to connect to [link=https://www.toptal.com/developers/gitignore]gitignore.io[/link]."
        )
        raise typer.Exit(1)

    result = template_list.contains(term)
    if not result:
        stderr.print(f"Could not list template names: Found no matching names for search term '{term}'.")
        raise typer.Exit(1)

    template_list.sort()
    formatted_template_names = [template.name.replace(term, f"[underline]{term}[/underline]") for template in result]

    columns = rich.columns.Columns(formatted_template_names, equal=True, expand=False)
    stdout.print(columns)

    typer.Exit(0)


@app.command("create")
def create(
    names: Annotated[
        list[str],
        typer.Argument(
            help="Name of templates to include in gitignore file.",
            show_default=False,
        ),
    ],
    path: Annotated[
        Optional[pathlib.Path],
        typer.Option("--path", help="Create a gitignore file at this path.", show_default=False),
    ] = None,
    echo: Annotated[
        bool,
        typer.Option("--show-gitignore", help="Show the content of the gitignore instead of creating a file."),
    ] = False,
):
    """
    Create a new gitignore file.

    If no path is provided, the file will be created in the current directory.
    """
    if path is None:
        path = pathlib.Path.cwd() / ".gitignore"

    try:
        template_list = ignoro.TemplateList(populate=True)
    except requests.exceptions.ConnectionError:
        stderr.print(
            "Could not create gitignore file: Failed to connect to [link=https://www.toptal.com/developers/gitignore]gitignore.io[/link]."
        )
        raise typer.Exit(1)

    template_matches = template_list.exactly_matches(names)
    if not template_matches:
        stderr.print(
            f"Could not create gitignore file: Found no matching template names for terms '{', '.join(names)}'."
        )
        raise typer.Exit(1)

    template_matches.sort()
    gitignore = ignoro.Gitignore(template_matches)

    if echo:
        stdout.print(gitignore.dumps())
        raise typer.Exit(0)

    try:
        if path.is_dir():
            stderr.print(f"Could not create gitignore file: Path '{path.absolute()}' is a directory.")
            raise typer.Exit(1)
    except PermissionError:
        stderr.print(f"Could not create gitignore file: Permission denied for '{path.absolute()}'.")
        raise typer.Exit(1)

    if path.exists():
        overwrite = rich.prompt.Confirm.ask(
            f"File [green]'{path.absolute()}'[/green] already exists. Do you wish to overwrite it?"
        )
        if not overwrite:
            raise typer.Abort()

    try:
        gitignore.dump(path)
    except PermissionError:
        stderr.print(f"Could not create gitignore file: Permission denied for '{path.absolute()}'.")
        raise typer.Exit(1)

    typer.Exit(0)


@app.command("show")
def show(
    path: Annotated[
        Optional[pathlib.Path],
        typer.Option("--path", help="Show template names from a gitignore file at this path.", show_default=False),
    ] = None,
):
    """
    Show template names from a gitignore file.

    If no path is provided, the template names from the gitignore file in the current directory will be shown.
    """
    if path is None:
        path = pathlib.Path.cwd() / ".gitignore"

    try:
        gitignore = ignoro.Gitignore.load(path)
    except FileNotFoundError:
        stderr.print(f"Could not show gitignore file: File '{path.absolute()}' does not exist.")
        raise typer.Exit(1)
    except PermissionError:
        stderr.print(f"Could not show gitignore file: Permission denied for '{path.absolute()}'.")
        raise typer.Exit(1)
    except IsADirectoryError:
        stderr.print(f"Could not show gitignore file: Path '{path.absolute()}' is a directory.")
        raise typer.Exit(1)
    except ValueError:
        stderr.print(f"Could not show gitignore file: File '{path.absolute()}' is not valid.")
        raise typer.Exit(1)

    gitignore.template_list.sort()
    names = [template.name for template in gitignore.template_list]

    columns = rich.columns.Columns(names, equal=True, expand=False)
    stdout.print(columns)

    typer.Exit(0)


@app.command("add")
def add(
    names: Annotated[
        list[str],
        typer.Argument(
            help="Name of templates to add to gitignore file.",
            show_default=False,
        ),
    ],
    path: Annotated[
        Optional[pathlib.Path],
        typer.Option("--path", help="Add templates to gitignore file at this path.", show_default=False),
    ] = None,
    echo: Annotated[
        bool,
        typer.Option("--show-gitignore", help="Show the content of the gitignore instead of adding to file."),
    ] = False,
):
    """
    Add templates to an existing gitignore file.

    If no path is provided, the templates will be added to the gitignore file in the current directory.
    """
    if path is None:
        path = pathlib.Path.cwd() / ".gitignore"

    try:
        gitignore = ignoro.Gitignore.load(path)
    except FileNotFoundError:
        stderr.print(f"Could not read gitignore file: File '{path.absolute()}' does not exist.")
        raise typer.Exit(1)
    except PermissionError:
        stderr.print(f"Could not read gitignore file: Permission denied for '{path.absolute()}'.")
        raise typer.Exit(1)
    except IsADirectoryError:
        stderr.print(f"Could not read gitignore file: Path '{path.absolute()}' is a directory.")
        raise typer.Exit(1)
    except ValueError:
        stderr.print(f"Could not read gitignore file: File '{path.absolute()}' is not valid.")
        raise typer.Exit(1)

    try:
        template_list = ignoro.TemplateList(populate=True)
    except requests.exceptions.ConnectionError:
        stderr.print(
            "Could not add to gitignore file: Failed to connect to [link=https://www.toptal.com/developers/gitignore]gitignore.io[/link]."
        )
        raise typer.Exit(1)

    template_matches = template_list.exactly_matches(names)
    if not template_matches:
        stderr.print(
            f"Could not add to gitignore file: Found no matching template names for terms '{', '.join(names)}'."
        )
        raise typer.Exit(1)

    for template in template_matches:
        if template in gitignore.template_list:
            overwrite = rich.prompt.Confirm.ask(
                f"Template [green]'{template.name}'[/green] already exists in gitignore file. Do you wish to replace it?"
            )
            if not overwrite:
                continue
        gitignore.template_list.replace(template)

    if echo:
        stdout.print(gitignore.dumps())
        raise typer.Exit(0)

    try:
        if path.is_dir():
            stderr.print(f"Could not add to gitignore file: Path '{path.absolute()}' is a directory.")
            raise typer.Exit(1)
    except PermissionError:
        stderr.print(f"Could not add to gitignore file: Permission denied for '{path.absolute()}'.")
        raise typer.Exit(1)

    try:
        gitignore.dump(path)
    except PermissionError:
        stderr.print(f"Could not add to gitignore file: Permission denied for '{path.absolute()}'.")
        raise typer.Exit(1)

    typer.Exit(0)


@app.command("remove")
def remove(
    names: Annotated[
        list[str],
        typer.Argument(
            help="Name of templates to remove from gitignore file.",
            show_default=False,
        ),
    ],
    path: Annotated[
        Optional[pathlib.Path],
        typer.Option("--path", help="Remove templates from gitignore file at this path.", show_default=False),
    ] = None,
    echo: Annotated[
        bool,
        typer.Option("--show-gitignore", help="Show the content of the gitignore instead of removing from file."),
    ] = False,
):
    """
    Remove templates from an existing gitignore file.

    If no path is provided, the templates will be removed from the gitignore file in the current directory.
    """
    if path is None:
        path = pathlib.Path.cwd() / ".gitignore"

    try:
        gitignore = ignoro.Gitignore.load(path)
    except FileNotFoundError:
        stderr.print(f"Could not read gitignore file: File '{path.absolute()}' does not exist.")
        raise typer.Exit(1)
    except PermissionError:
        stderr.print(f"Could not read gitignore file: Permission denied for '{path.absolute()}'.")
        raise typer.Exit(1)
    except IsADirectoryError:
        stderr.print(f"Could not read gitignore file: Path '{path.absolute()}' is a directory.")
        raise typer.Exit(1)
    except ValueError:
        stderr.print(f"Could not read gitignore file: File '{path.absolute()}' is not valid.")
        raise typer.Exit(1)

    template_matches = gitignore.template_list.exactly_matches(names)

    for name in names:
        if name not in [template.name for template in gitignore.template_list]:
            stderr.print(f"Could not remove from gitignore file: Template '{name}' does not exist in gitignore file.")

    for template in template_matches:
        gitignore.template_list.remove(template)

    if echo:
        stdout.print(gitignore.dumps())
        raise typer.Exit(0)

    try:
        if path.is_dir():
            stderr.print(f"Could not remove from gitignore file: Path '{path.absolute()}' is a directory.")
            raise typer.Exit(1)
    except PermissionError:
        stderr.print(f"Could not remove from gitignore file: Permission denied for '{path.absolute()}'.")
        raise typer.Exit(1)

    try:
        gitignore.dump(path)
    except PermissionError:
        stderr.print(f"Could not remove from gitignore file: Permission denied for '{path.absolute()}'.")
        raise typer.Exit(1)

    typer.Exit(0)


@app.callback()
def main():
    """Create or modify gitignore files based on templates from [link=https://www.toptal.com/developers/gitignore]gitignore.io[/link]."""
    ...


if __name__ == "__main__":
    app()
