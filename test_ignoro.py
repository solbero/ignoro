import pathlib

import pytest
import requests
import requests_mock
import typer.testing
from typing_extensions import Sequence

import ignoro

TEMPLATE_NAMES = [
    "c",
    "c#",
    "c++",
    "django",
    "go",
    "java",
    "javascript",
    "php",
    "python",
    "ruby",
    "rust",
    "swift",
    "typescript",
]

TEMPLATE_CONTENT = """# Created by https://www.toptal.com/developers/gitignore/api/go
# Edit at https://www.toptal.com/developers/gitignore?templates=go

### Go ###
# If you prefer the allow list template instead of the deny list, see community template:
# https://github.com/github/gitignore/blob/main/community/Golang/Go.AllowList.gitignore
#
# Binaries for programs and plugins
*.exe
*.exe~
*.dll
*.so
*.dylib

# Test binary, built with `go test -c`
*.test

# Output of the go coverage tool, specifically when used with LiteIDE
*.out

# Dependency directories (remove the comment below to include it)
# vendor/

# Go workspace file
go.work

# End of https://www.toptal.com/developers/gitignore/api/go"""


def assert_in_string(fragments: Sequence[str], string: str):
    __tracebackhide__ = True
    for fragment in fragments:
        assert fragment.lower() in string.lower()


@pytest.fixture()
def runner() -> typer.testing.CliRunner:
    return typer.testing.CliRunner()


@pytest.fixture()
def templates() -> ignoro.TemplateList:
    return ignoro.TemplateList()


class TestHTTPErrors:
    def test_create_error_connection(
        self, runner: typer.testing.CliRunner, requests_mock: requests_mock.Mocker, tmp_path: pathlib.Path
    ):
        requests_mock.get(ignoro.TemplateList._api, exc=requests.ConnectionError)
        requests_mock.get(f"{ignoro.Template._api}/go", exc=requests.ConnectionError)
        path = tmp_path / ".gitignore"
        result = runner.invoke(ignoro.cli, ["create", "go", "--path", str(path)])
        assert result.exit_code == 1
        assert_in_string(["failed to connect"], result.stdout)

    def test_list_error_connection(
        self,
        runner: typer.testing.CliRunner,
        requests_mock: requests_mock.Mocker,
    ):
        requests_mock.get(ignoro.TemplateList._api, exc=requests.exceptions.ConnectionError)
        result = runner.invoke(ignoro.cli, ["list"])
        assert result.exit_code == 1
        assert_in_string(["failed to connect"], result.stdout)


class TestCLI:
    def test_list(
        self,
        runner: typer.testing.CliRunner,
        requests_mock: requests_mock.Mocker,
    ):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        result = runner.invoke(ignoro.cli, ["list"])
        assert result.exit_code == 0
        assert str.split(result.stdout) == TEMPLATE_NAMES

    def test_list_filter(
        self,
        runner: typer.testing.CliRunner,
        requests_mock: requests_mock.Mocker,
    ):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        result = runner.invoke(ignoro.cli, ["list", "ja"])
        assert result.exit_code == 0
        assert str.split(result.stdout) == ["django", "java", "javascript"]

    def test_list_filter_no_result(
        self,
        runner: typer.testing.CliRunner,
        requests_mock: requests_mock.Mocker,
    ):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        result = runner.invoke(ignoro.cli, ["list", "foobar"])
        assert result.exit_code == 1
        assert_in_string(["foobar", "found no matching"], result.stdout)

    def test_create(self, runner: typer.testing.CliRunner, requests_mock: requests_mock.Mocker, tmp_path: pathlib.Path):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        requests_mock.get(f"{ignoro.Template._api}/go", text=TEMPLATE_CONTENT)
        path = tmp_path / ".gitignore"
        result = runner.invoke(ignoro.cli, ["create", "go", "--path", str(path)])
        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-1] == TEMPLATE_CONTENT.splitlines(keepends=True)[3:-1]

    def test_create_already_exists(
        self, runner: typer.testing.CliRunner, requests_mock: requests_mock.Mocker, tmp_path: pathlib.Path
    ):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        requests_mock.get(f"{ignoro.Template._api}/go", text=TEMPLATE_CONTENT)
        path = tmp_path / ".gitignore"
        path.touch()
        result = runner.invoke(ignoro.cli, ["create", "go", "--path", str(path)], input="y\n")
        assert result.exit_code == 0
        assert_in_string(["already exists", "overwrite"], result.stdout)
        with open(path, "r") as file:
            assert file.readlines()[3:-1] == TEMPLATE_CONTENT.splitlines(keepends=True)[3:-1]

    def test_create_error_path_already_exists(
        self, runner: typer.testing.CliRunner, requests_mock: requests_mock.Mocker, tmp_path: pathlib.Path
    ):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        requests_mock.get(f"{ignoro.Template._api}/go", text=TEMPLATE_CONTENT)
        path = tmp_path / ".gitignore"
        path.touch()
        result = runner.invoke(ignoro.cli, ["create", "go", "--path", str(path)], input="n\n")
        assert result.exit_code == 1
        assert_in_string(["aborted"], result.stdout)

    def test_create_error_template_not_found(
        self, runner: typer.testing.CliRunner, requests_mock: requests_mock.Mocker
    ):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        result = runner.invoke(ignoro.cli, ["create", "foobar"])
        assert result.exit_code == 1
        assert_in_string(["foobar", "found no matching templates"], result.stdout)

    def test_create_error_path_is_dir(
        self, runner: typer.testing.CliRunner, requests_mock: requests_mock.Mocker, tmp_path: pathlib.Path
    ):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        requests_mock.get(f"{ignoro.Template._api}/go", text=TEMPLATE_CONTENT)
        path = pathlib.Path(tmp_path)
        result = runner.invoke(ignoro.cli, ["create", "go", "--path", str(path)])
        assert result.exit_code == 1
        assert_in_string([f"{path}", "is a directory"], result.stdout)

    def test_create_error_path_is_not_writable(
        self, runner: typer.testing.CliRunner, requests_mock: requests_mock.Mocker, tmp_path: pathlib.Path
    ):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        requests_mock.get(f"{ignoro.Template._api}/go", text=TEMPLATE_CONTENT)
        tmp_path.chmod(0o0555)
        path = tmp_path / ".gitignore"
        result = runner.invoke(ignoro.cli, ["create", "go", "--path", str(path)])
        assert result.exit_code == 1
        assert_in_string([f"{path}", "permission denied"], result.stdout)


class TestTemplates:
    def test_list(self, requests_mock: requests_mock.Mocker, templates: ignoro.TemplateList):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        template_names = [template.name for template in templates.all]
        assert template_names == TEMPLATE_NAMES

    def test_contains(self, requests_mock: requests_mock.Mocker, templates: ignoro.TemplateList):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        result = templates.name_contains("ja")
        template_names = [template.name for template in result]
        assert template_names == ["django", "java", "javascript"]

    def test_contains_no_result(self, requests_mock: requests_mock.Mocker, templates: ignoro.TemplateList):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        result = templates.name_contains("foobar")
        assert len(result) == 0

    def test_startswith(self, requests_mock: requests_mock.Mocker, templates: ignoro.TemplateList):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        result = [template.name for template in templates.name_startswith("ja")]
        assert result == ["java", "javascript"]

    def test_startswith_no_result(self, requests_mock: requests_mock.Mocker, templates: ignoro.TemplateList):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        result = [template.name for template in templates.name_startswith("foobar")]
        assert len(result) == 0

    def test_matches_and_content(self, requests_mock: requests_mock.Mocker, templates: ignoro.TemplateList):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        requests_mock.get(f"{ignoro.Template._api}/go", text=TEMPLATE_CONTENT)
        result = templates.name_exactly_matches(["go"])
        assert len(result) == 1
        assert result[0].name == "go"
        assert result[0].content in TEMPLATE_CONTENT

    def test_matches_no_result(self, requests_mock: requests_mock.Mocker, templates: ignoro.TemplateList):
        requests_mock.get(ignoro.TemplateList._api, text="\n".join(TEMPLATE_NAMES))
        result = templates.name_exactly_matches(["foobar"])
        assert len(result) == 0
