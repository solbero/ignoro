import pathlib

import pytest
import requests_mock
import typer.testing
from typing_extensions import Iterator, NamedTuple, Sequence

import ignoro


def assert_in_string(fragments: Sequence[str], string: str):
    __tracebackhide__ = True
    for fragment in fragments:
        assert fragment.lower() in string.lower()


class TestConsole(NamedTuple):
    __test__ = False
    runner: typer.testing.CliRunner
    cwd: pathlib.Path


@pytest.fixture(scope="function")
def console(tmp_path: pathlib.Path) -> Iterator[TestConsole]:
    runner = typer.testing.CliRunner(mix_stderr=False)
    with runner.isolated_filesystem(tmp_path) as cwd:
        yield TestConsole(runner, pathlib.Path(cwd))


@pytest.fixture(scope="function")
def template_list() -> ignoro.TemplateList:
    return ignoro.TemplateList()


@pytest.fixture(scope="function")
def template_list_populated(template_list: ignoro.TemplateList) -> ignoro.TemplateList:
    template_list.populate()
    return template_list


@pytest.fixture(scope="function", autouse=True)
def mock_requests(
    requests_mock: requests_mock.Mocker,
    mock_template_list_names: list[str],
    mock_response_foo: str,
    mock_response_bar: str,
) -> None:
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_list_names))
    requests_mock.get(f"{ignoro.BASE_URL}/foo", text=mock_response_foo)
    requests_mock.get(f"{ignoro.BASE_URL}/bar", text=mock_response_bar)
    requests_mock.get(f"{ignoro.BASE_URL}/notfound", status_code=404)


@pytest.fixture(scope="session")
def mock_response_foo(mock_template_foo: str) -> str:
    return _add_header_and_footer(mock_template_foo, "foo")


@pytest.fixture(scope="session")
def mock_response_bar(mock_template_bar: str) -> str:
    return _add_header_and_footer(mock_template_bar, "bar")


@pytest.fixture(scope="session")
def mock_template_list_names() -> list[str]:
    return [
        "bar",
        "dotdot",
        "double-dash",
        "fizzbuzz",
        "foo",
        "hoppy",
    ]


@pytest.fixture(scope="session")
def mock_template_foo() -> str:
    return """### Foo ###

# Used by dotenv library to load environment variables.
.env

# Ignore compiled files
*.fooc

# Ignore virtual environment folder
env/

# Ignore log files
*.log

# Ignore database files
*.db

# Ignore cache files
*.cache

# Ignore sensitive information
secrets.txt"""


@pytest.fixture(scope="session")
def mock_template_bar() -> str:
    return """### Bar ###
# Ignore bundler config.
/.bundle

# Ignore all logfiles and tempfiles.
/log/*
/tmp/*

# Ignore the default SQLite database.
/db/*.sqlite3

# Ignore all .env files.
.env*"""


def _add_header_and_footer(template: str, name: str) -> str:
    return f"""# Created by https://www.toptal.com/developers/gitignore/api/{name}
# Edit at https://www.toptal.com/developers/gitignore?templates={name}

{template}

# End of https://www.toptal.com/developers/gitignore/api/{name}"""
