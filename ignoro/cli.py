import pathlib

import jinja2
import requests
import rich
import rich.columns
import rich.console
import rich.prompt
import typer
from typing_extensions import Annotated

import ignoro.api

app = typer.Typer(rich_markup_mode="rich")
stdout = rich.console.Console(color_system="auto")
stderr = rich.console.Console(color_system="auto", stderr=True, style="red")

env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="templates"))
jinja_template = env.get_template("gitignore.j2")

gitignore_templates = ignoro.api.TemplateList()


@app.command("list")
def list_(
    term: Annotated[
        str,
        typer.Argument(help="Term used to search available templates."),
    ] = ""
):
    """
    List available gitignore templates.

    If no term is provided, all available templates will be listed.
    """
    try:
        result = gitignore_templates.name_contains(term) if term else gitignore_templates.all
    except requests.exceptions.ConnectionError:
        stderr.print(
            "Could not list templates: Failed to connect to [link=https://www.toptal.com/developers/gitignore]gitignore.io[/link]."
        )
        raise typer.Exit(1)

    if not result:
        stderr.print(f"Could not list templates: Found no matching templates for term '{term}'.")
        raise typer.Exit(1)

    formatted = [template.name.replace(term, f"[underline]{term}[/underline]") for template in result]

    columns = rich.columns.Columns(formatted, equal=True, expand=True)
    stdout.print(columns)

    typer.Exit(0)


@app.command("create")
def create(
    templates: Annotated[
        list[str],
        typer.Argument(
            help="Templates to include in gitignore file.",
            autocompletion=gitignore_templates.name_startswith,
            show_default=False,
        ),
    ],
    path: Annotated[
        pathlib.Path,
        typer.Option("--path", help="Create a gitignore file at this path."),
    ] = (pathlib.Path.cwd() / ".gitignore"),
    echo: Annotated[
        bool,
        typer.Option("--show-gitignore", help="Show the content of the gitignore instead of creating a file."),
    ] = False,
):
    """
    Create a new gitignore file.

    If no path is provided, the file will be created in the current directory.
    """
    try:
        results = gitignore_templates.name_exactly_matches(templates)
    except requests.exceptions.ConnectionError:
        stderr.print(
            "Could not create gitignore file: Failed to connect to [link=https://www.toptal.com/developers/gitignore]gitignore.io[/link]."
        )
        raise typer.Exit(1)

    if not results:
        stderr.print(
            f"Could not create gitignore file: Found no matching templates for terms '{', '.join(templates)}'."
        )
        raise typer.Exit(1)

    gitignore = jinja_template.render(templates=results)

    if echo:
        stdout.print(gitignore)
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
        with path.open("w") as file:
            file.write(gitignore)
    except PermissionError:
        stderr.print(f"Could not create gitignore file. Permission denied for '{path.absolute()}'.")
        raise typer.Exit(1)

    typer.Exit(0)


@app.callback()
def main():
    """Create or modify gitignore files based on templates from [link=https://www.toptal.com/developers/gitignore]gitignore.io[/link]."""
    ...


if __name__ == "__main__":
    app()
