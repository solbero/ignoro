import enum
import pathlib

import pytest
import requests
import requests_mock
import rich
import typer.testing
from typing_extensions import Iterator, NamedTuple, Sequence

import ignoro


def assert_in_string(fragments: Sequence[str], string: str):
    __tracebackhide__ = True
    for fragment in fragments:
        assert fragment.lower() in string.lower()


class TestRunner(NamedTuple):
    __test__ = False
    runner: typer.testing.CliRunner
    console: rich.console.Console
    cwd: pathlib.Path


class TemplateMock(NamedTuple):
    name: str
    header: str
    body: str
    content: str
    response: str


class MockErrors(str, enum.Enum):
    NOT_EXIST = "not-exist-error"
    NOT_FOUND = "not-found-error"
    SERVER = "server-error"
    TIMEOUT = "timeout-error"
    CONNECTION = "connection-error"


@pytest.fixture(scope="function")
def test_runner(tmp_path: pathlib.Path) -> Iterator[TestRunner]:
    runner = typer.testing.CliRunner(mix_stderr=False)
    console = rich.console.Console(record=True)
    with runner.isolated_filesystem(tmp_path) as cwd:
        yield TestRunner(runner, console, pathlib.Path(cwd))


@pytest.fixture(scope="function", autouse=True)
def mock_requests(
    requests_mock: requests_mock.Mocker,
    template_list_names_mock: tuple[str, ...],
    foo_template_mock: TemplateMock,
    bar_template_mock: TemplateMock,
) -> None:
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(template_list_names_mock))
    requests_mock.get(f"{ignoro.BASE_URL}/foo", text=foo_template_mock.response)
    requests_mock.get(f"{ignoro.BASE_URL}/bar", text=bar_template_mock.response)
    requests_mock.get(f"{ignoro.BASE_URL}/{MockErrors.NOT_FOUND.value}", status_code=404)
    requests_mock.get(f"{ignoro.BASE_URL}/{MockErrors.TIMEOUT.value}", exc=requests.exceptions.Timeout())
    requests_mock.get(f"{ignoro.BASE_URL}/{MockErrors.CONNECTION.value}", exc=requests.exceptions.ConnectionError)


@pytest.fixture(scope="function")
def template_list() -> ignoro.TemplateList:
    return ignoro.TemplateList()


@pytest.fixture(scope="session")
def foo_template_mock(foo_template_content_mock: str) -> TemplateMock:
    name = "foo"
    header = f"### {name.capitalize()} ###"
    body = foo_template_content_mock
    content = f"{header}\n{body}"
    response = api_response_mock(name, header, body)
    return TemplateMock(name, header, body, content, response)


@pytest.fixture(scope="session")
def bar_template_mock(bar_template_content_mock: str) -> TemplateMock:
    name = "bar"
    header = f"### {name.capitalize()} ###"
    body = bar_template_content_mock
    content = f"{header}\n{body}"
    response = api_response_mock(name, header, body)
    return TemplateMock(name, header, body, content, response)


@pytest.fixture(scope="session")
def template_list_names_mock() -> tuple[str, ...]:
    return (
        "bar",
        "dotdot",
        "double-dash",
        "fizzbuzz",
        "foo",
        "hoppy",
    )


@pytest.fixture(scope="session")
def foo_template_content_mock() -> str:
    return """# Used by dotenv library to load environment variables.
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
def bar_template_content_mock() -> str:
    return """# Ignore bundler config.
/.bundle

# Ignore all logfiles and tempfiles.
/log/*
/tmp/*

# Ignore the default SQLite database.
/db/*.sqlite3

# Ignore all .env files.
.env*"""


def api_response_mock(name: str, header: str, content: str) -> str:
    return f"""# Created by https://www.toptal.com/developers/gitignore/api/{name.lower()}
# Edit at https://www.toptal.com/developers/gitignore?templates={name.lower()}

{header}
{content}

# End of https://www.toptal.com/developers/gitignore/api/{name.lower()}"""
