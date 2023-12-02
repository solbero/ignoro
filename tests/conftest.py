import enum
import pathlib
from collections.abc import Iterable, Iterator

import pytest
import requests
import requests_mock
import typer.testing
from typing_extensions import NamedTuple

import ignoro


def assert_in_string(fragments: Iterable[str], string: str):
    __tracebackhide__ = True
    for fragment in fragments:
        assert fragment.lower() in string.lower()


class TestConsole(NamedTuple):
    __test__ = False
    runner: typer.testing.CliRunner
    cwd: pathlib.Path


class TemplateMock(NamedTuple):
    name: str
    header: str
    body: str
    content: str
    response: str


class MockErrors(str, enum.Enum):
    NOT_FOUND = "not-found-error"
    TIMEOUT = "timeout-error"
    CONNECTION = "connection-error"


@pytest.fixture()
def test_console(tmp_path: pathlib.Path) -> Iterator[TestConsole]:
    runner = typer.testing.CliRunner(mix_stderr=False)
    with runner.isolated_filesystem(tmp_path) as cwd:
        yield TestConsole(runner, pathlib.Path(cwd))


@pytest.fixture(autouse=True)
def _mock_requests(
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


@pytest.fixture()
def template_list() -> ignoro.TemplateList:
    return ignoro.TemplateList()


@pytest.fixture(scope="session")
def foo_template_mock(foo_template_body_mock: str) -> TemplateMock:
    name = "foo"
    header = ignoro.Template._create_header(name)
    body = foo_template_body_mock
    content = f"{header}\n{body}"
    response = api_response_mock(name, body)
    return TemplateMock(name, header, body, content, response)


@pytest.fixture(scope="session")
def bar_template_mock(bar_template_body_mock: str) -> TemplateMock:
    name = "bar"
    header = ignoro.Template._create_header(name)
    body = bar_template_body_mock
    content = f"{header}\n{body}"
    response = api_response_mock(name, body)
    return TemplateMock(name, header, body, content, response)


@pytest.fixture(scope="session")
def template_list_names_mock() -> list[str]:
    return [
        "bar",
        "dotdot",
        "double-dash",
        "foo",
        "foobar",
        "hoppy",
    ]


@pytest.fixture(scope="session")
def foo_template_body_mock() -> str:
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
secrets.txt
"""


@pytest.fixture(scope="session")
def bar_template_body_mock() -> str:
    return """# Ignore bundler config.
/.bundle

# Ignore all logfiles and tempfiles.
/log/*
/tmp/*

# Ignore the default SQLite database.
/db/*.sqlite3

# Ignore all .env files.
.env*
"""


def api_response_mock(name: str, body: str) -> str:
    return f"""# Created by https://www.toptal.com/developers/gitignore/api/{name.lower()}
# Edit at https://www.toptal.com/developers/gitignore?templates={name.lower()}

### {name.capitalize()} ###
{body}

# End of https://www.toptal.com/developers/gitignore/api/{name.lower()}
"""
