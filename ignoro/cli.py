import functools
import pathlib

import rich
import rich.columns
import rich.console
import rich.panel
import rich.prompt
import typer
from typing_extensions import Annotated, Optional

import ignoro

__all__ = ["app"]

app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")
stdout = rich.console.Console(color_system="auto", highlight=False)
stderr = rich.console.Console(color_system="auto", stderr=True, highlight=False)
columns = functools.partial(rich.columns.Columns, column_first=True, equal=True, padding=(0, 2))
panel = functools.partial(rich.panel.Panel, border_style="red", title="Error", title_align="left")


@app.command("search")
def search(
    term: Annotated[
        str,
        typer.Argument(help="Term used to search [link=https://www.toptal.com/developers/gitignore]gitignore.io[/]."),
    ] = ""
):
    """
    Search for templates at [link=https://www.toptal.com/developers/gitignore]gitignore.io[/].

    If no search term is provided, all available templates will be listed.
    """
    try:
        template_list = ignoro.api.TemplateList(populate=True)
    except ignoro.exceptions.ApiError as err:
        stderr.print(panel(f"{err}."))
        raise typer.Exit(1)

    template_names = tuple(template.name for template in template_list.contains(term))
    if not template_names:
        stderr.print(panel(f"No matching templates for term: '{term}'."))
        raise typer.Exit(1)

    template_names_formatted = tuple(name.replace(term, f"[underline]{term}[/underline]") for name in template_names)

    stdout.print(columns(template_names_formatted))


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
        template_list = ignoro.api.TemplateList(populate=True)
    except ignoro.exceptions.ApiError as err:
        stderr.print(f"Could not create gitignore file: {err}.")
        raise typer.Exit(1)

    matching_templates = template_list.findall(names)
    if not matching_templates:
        stderr.print(
            f"Could not create gitignore file: Found no matching template names for terms '{', '.join(names)}'."
        )
        raise typer.Exit(1)

    gitignore = ignoro.Gitignore(matching_templates)

    if echo:
        stdout.print(gitignore.dumps())
        raise typer.Exit(0)

    if path.exists():
        overwrite = rich.prompt.Confirm.ask(
            f"File [green]'{path.absolute()}'[/green] already exists. Do you wish to overwrite it?"
        )
        if not overwrite:
            raise typer.Abort()

    try:
        gitignore.dump(path)
    except (IsADirectoryError, PermissionError) as err:
        stderr.print(f"Could not create gitignore file: {err}.")
        raise typer.Exit(1)


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
    except (FileNotFoundError, PermissionError, IsADirectoryError, ignoro.exceptions.ParseError) as err:
        stderr.print(f"Could not show gitignore file: {err}.")
        raise typer.Exit(1)

    template_names = tuple(template.name for template in gitignore.template_list)

    stdout.print(columns(template_names))


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
    except (FileNotFoundError, PermissionError, IsADirectoryError, ignoro.exceptions.ParseError) as err:
        stderr.print(f"Could not add to gitignore file: {err}.")
        raise typer.Exit(1)

    template_list = ignoro.api.TemplateList(populate=True)

    template_matches = template_list.findall(names)
    if len(template_matches) != len(names):
        names_not_found = tuple(
            name for name in names if name not in tuple(template.name for template in template_matches)
        )
        stderr.print(
            f"Could not add to gitignore file: Found no matching template names for terms '{', '.join(names_not_found)}'."
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
        gitignore.dump(path)
    except (IsADirectoryError, PermissionError) as err:
        stderr.print(f"Could not add to gitignore file: {err}.")
        raise typer.Exit(1)


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
    except (FileNotFoundError, PermissionError, IsADirectoryError, ignoro.exceptions.ParseError) as err:
        stderr.print(f"Could not remove from gitignore file: {err}.")
        raise typer.Exit(1)

    names_not_found = tuple(
        name for name in names if name not in tuple(template.name for template in gitignore.template_list)
    )
    if names_not_found:
        stderr.print(
            f"Could not remove from gitignore file: Found no matching template names for terms '{', '.join(names_not_found)}'."
        )
        raise typer.Exit(1)

    template_matches = gitignore.template_list.findall(names)

    for template in template_matches:
        gitignore.template_list.remove(template)

    if echo:
        stdout.print(gitignore.dumps())
        raise typer.Exit(0)

    try:
        gitignore.dump(path)
    except (IsADirectoryError, PermissionError) as err:
        stderr.print(f"Could not remove from gitignore file: {err}.")
        raise typer.Exit(1)


@app.callback()
def main():
    """Create or modify a .gitignore file based on templates from [link=https://www.toptal.com/developers/gitignore]gitignore.io[/link]."""
    ...


if __name__ == "__main__":
    app()
