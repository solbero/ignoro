import functools
import pathlib
from typing import Annotated, Optional

import rich
import rich.columns
import rich.console
import rich.panel
import rich.prompt
import typer

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
    ] = "",
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

    template_names = [template.name for template in template_list.contains(term)]
    if not template_names:
        stderr.print(panel(f"No matching templates for term: '{term}'."))
        raise typer.Exit(1)

    names_underlined = [name.replace(term, f"[underline]{term}[/underline]") for name in template_names]

    stdout.print(columns(names_underlined))


@app.command("create")
def create(
    templates: Annotated[
        list[str],
        typer.Argument(
            help="Templates to include in .gitignore file.",
            show_default=False,
        ),
    ],
    path: Annotated[
        Optional[pathlib.Path],
        typer.Option("--path", help="Create a .gitignore file at this path.", show_default=False),
    ] = None,
    echo: Annotated[
        bool,
        typer.Option("--show-gitignore", help="Show the result of the create command instead of writing a file."),
    ] = False,
):
    """
    Create a .gitignore file.

    If no path is provided, the .gitignore file will be created in the current directory.
    """
    if path is None:
        path = pathlib.Path.cwd() / ".gitignore"

    try:
        template_list = ignoro.api.TemplateList(populate=True)
    except ignoro.exceptions.ApiError as err:
        stderr.print(panel(f"{err}."))
        raise typer.Exit(1)

    templates_matching_names = template_list.findall(templates)

    names_not_found = [
        name for name in templates if name not in [template.name for template in templates_matching_names]
    ]
    if names_not_found:
        names_quoted = [f"'{name}'" for name in names_not_found]
        stderr.print(
            panel(
                f"No matching templates for {'terms' if len(names_not_found) > 1 else 'term'}: "
                f"{', '.join(name for name in names_quoted)}.",
            )
        )
        raise typer.Exit(1)

    gitignore = ignoro.Gitignore(templates_matching_names)

    if echo:
        stdout.print(gitignore.dumps())
        raise typer.Exit(0)

    if path.exists():
        overwrite = rich.prompt.Confirm.ask(f"File {path.absolute()} already exists. Do you wish to overwrite it?")
        if not overwrite:
            raise typer.Abort()

    try:
        gitignore.dump(path)
    except (IsADirectoryError, PermissionError, ignoro.exceptions.ApiError) as err:
        stderr.print(panel(f"{err}."))
        raise typer.Exit(1)


@app.command("list")
def list_(
    path: Annotated[
        Optional[pathlib.Path],
        typer.Option("--path", help="List templates in .gitignore file at this path.", show_default=False),
    ] = None,
):
    """
    List templates in a .gitignore file.

    If no path is provided, the templates from the .gitignore file in the current directory will be listed.
    """
    if path is None:
        path = pathlib.Path.cwd() / ".gitignore"

    try:
        gitignore = ignoro.Gitignore.load(path)
    except (FileNotFoundError, PermissionError, IsADirectoryError, ignoro.exceptions.ParseError) as err:
        stderr.print(panel(f"{err}."))
        raise typer.Exit(1)

    template_names = [template.name for template in gitignore.template_list]
    if not template_names:
        stderr.print(panel(f"No templates found in '{path.absolute()}'."))
        raise typer.Exit(1)

    stdout.print(columns(template_names))


@app.command("add")
def add(
    templates: Annotated[
        list[str],
        typer.Argument(
            help="Templates to add to .gitignore file.",
            show_default=False,
        ),
    ],
    path: Annotated[
        Optional[pathlib.Path],
        typer.Option(
            "--path",
            help="Add templates to .gitignore file at this path.",
            show_default=False,
        ),
    ] = None,
    echo: Annotated[
        bool,
        typer.Option("--show-gitignore", help="Show the result of the add command instead of writing a file."),
    ] = False,
):
    """
    Add templates to a .gitignore file.

    If no path is provided, the templates will be added to the .gitignore file in the current directory.
    """
    if path is None:
        path = pathlib.Path.cwd() / ".gitignore"

    try:
        gitignore = ignoro.Gitignore.load(path)
    except (FileNotFoundError, PermissionError, IsADirectoryError, ignoro.exceptions.ParseError) as err:
        stderr.print(panel(f"{err}."))
        raise typer.Exit(1)

    try:
        template_list = ignoro.api.TemplateList(populate=True)
    except ignoro.exceptions.ApiError as err:
        stderr.print(panel(f"{err}."))
        raise typer.Exit(1)

    templates_matching_names = template_list.findall(templates)

    names_not_found = tuple(
        name for name in templates if name not in tuple(template.name for template in templates_matching_names)
    )
    if names_not_found:
        names_quoted = tuple(f"'{name}'" for name in names_not_found)
        stderr.print(
            panel(
                f"No matching templates for {'terms' if len(names_not_found) > 1 else 'term'}: "
                f"{', '.join(name for name in names_quoted)}."
            )
        )
        raise typer.Exit(1)

    for template in templates_matching_names:
        if template in gitignore.template_list:
            overwrite = rich.prompt.Confirm.ask(
                f"Template '{template.name}' already exists in gitignore file. Do you wish to replace it?"
            )
            if overwrite:
                gitignore.template_list.replace(template)
        else:
            gitignore.template_list.append(template)

    if echo:
        stdout.print(gitignore.dumps())
        raise typer.Exit(0)

    try:
        gitignore.dump(path)
    except ignoro.exceptions.ApiError as err:
        stderr.print(panel(f"{err}."))
        raise typer.Exit(1)


@app.command("remove")
def remove(
    templates: Annotated[
        list[str],
        typer.Argument(
            help="Templates to remove from .gitignore file.",
            show_default=False,
        ),
    ],
    path: Annotated[
        Optional[pathlib.Path],
        typer.Option("--path", help="Remove templates from .gitignore file at this path.", show_default=False),
    ] = None,
    echo: Annotated[
        bool,
        typer.Option("--show-gitignore", help="Show the result of the remove command instead of writing a file."),
    ] = False,
):
    """
    Remove templates from a .gitignore file.

    If no path is provided, the templates will be removed from the gitignore file in the current directory.
    """
    if path is None:
        path = pathlib.Path.cwd() / ".gitignore"

    try:
        gitignore = ignoro.Gitignore.load(path)
    except (FileNotFoundError, PermissionError, IsADirectoryError, ignoro.exceptions.ParseError) as err:
        stderr.print(panel(f"{err}."))
        raise typer.Exit(1)

    names_not_found = tuple(
        name for name in templates if name not in tuple(template.name for template in gitignore.template_list)
    )
    if names_not_found:
        names_quoted = tuple(f"'{name}'" for name in names_not_found)
        stderr.print(
            panel(
                f"No matching templates for {'terms' if len(names_not_found) > 1 else 'term'}: "
                f"{', '.join(name for name in names_quoted)}."
            )
        )
        raise typer.Exit(1)

    templates_matching_names = gitignore.template_list.findall(templates)

    for template in templates_matching_names:
        gitignore.template_list.remove(template)

    if echo:
        stdout.print(gitignore.dumps())
        raise typer.Exit(0)

    gitignore.dump(path)


@app.command("show")
def show(
    template: Annotated[
        str,
        typer.Argument(
            help="Template to show from [link=https://www.toptal.com/developers/gitignore]gitignore.io[/].",
            show_default=False,
        ),
    ],
):
    """
    Show a template from [link=https://www.toptal.com/developers/gitignore]gitignore.io[/].

    If no match is found, an error will be raised.
    """
    try:
        template_list = ignoro.api.TemplateList(populate=True)
    except ignoro.exceptions.ApiError as err:
        stderr.print(panel(f"{err}."))
        raise typer.Exit(1)

    template_match = template_list.match(template)
    if not template_match:
        stderr.print(panel(f"No matching template for term: '{template}'."))
        raise typer.Exit(1)

    try:
        stdout.print(template_match)
    except ignoro.exceptions.ApiError as err:
        stderr.print(panel(f"{err}."))
        raise typer.Exit(1)


@app.callback()
def main():
    """Create or modify a .gitignore file based on templates from [link=https://www.toptal.com/developers/gitignore]gitignore.io[/link]."""
    ...


if __name__ == "__main__":
    app()
