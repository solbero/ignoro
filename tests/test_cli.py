import pathlib

import requests
import requests_mock
import typer.testing
from typing_extensions import Sequence

import ignoro.api as api
import ignoro.cli as cli


def assert_in_string(fragments: Sequence[str], string: str):
    __tracebackhide__ = True
    for fragment in fragments:
        assert fragment.lower() in string.lower()


def test_create_error_connection(
    runner: typer.testing.CliRunner, requests_mock: requests_mock.Mocker, tmp_path: pathlib.Path
):
    requests_mock.get(api.TemplateList._api, exc=requests.ConnectionError)
    requests_mock.get(f"{api.Template._api}/go", exc=requests.ConnectionError)
    path = tmp_path / ".gitignore"
    result = runner.invoke(cli.app, ["create", "go", "--path", str(path)])
    assert result.exit_code == 1
    assert_in_string(["failed to connect"], result.stdout)


def test_list_error_connection(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
):
    requests_mock.get(api.TemplateList._api, exc=requests.exceptions.ConnectionError)
    result = runner.invoke(cli.app, ["list"])
    assert result.exit_code == 1
    assert_in_string(["failed to connect"], result.stdout)


def test_list(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    template_names: list[str],
):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    result = runner.invoke(cli.app, ["list"])
    assert result.exit_code == 0
    assert str.split(result.stdout) == template_names


def test_list_filter(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    template_names: list[str],
):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    result = runner.invoke(cli.app, ["list", "ja"])
    assert result.exit_code == 0
    assert str.split(result.stdout) == ["django", "java", "javascript"]


def test_list_filter_no_result(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    template_names: list[str],
):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    result = runner.invoke(cli.app, ["list", "foobar"])
    assert result.exit_code == 1
    assert_in_string(["foobar", "found no matching"], result.stdout)


def test_create(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    template_names: list[str],
    template_content: str,
    tmp_path: pathlib.Path,
):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    requests_mock.get(f"{api.Template._api}/go", text=template_content)
    path = tmp_path / ".gitignore"
    result = runner.invoke(cli.app, ["create", "go", "--path", str(path)])
    assert result.exit_code == 0
    with open(path, "r") as file:
        assert file.readlines()[3:-1] == template_content.splitlines(keepends=True)[3:-1]


def test_create_already_exists(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    template_names: list[str],
    template_content: str,
    tmp_path: pathlib.Path,
):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    requests_mock.get(f"{api.Template._api}/go", text=template_content)
    path = tmp_path / ".gitignore"
    path.touch()
    result = runner.invoke(cli.app, ["create", "go", "--path", str(path)], input="y\n")
    assert result.exit_code == 0
    assert_in_string(["already exists", "overwrite"], result.stdout)
    with open(path, "r") as file:
        assert file.readlines()[3:-1] == template_content.splitlines(keepends=True)[3:-1]


def test_create_error_path_already_exists(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    template_names: list[str],
    template_content: str,
    tmp_path: pathlib.Path,
):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    requests_mock.get(f"{api.Template._api}/go", text=template_content)
    path = tmp_path / ".gitignore"
    path.touch()
    result = runner.invoke(cli.app, ["create", "go", "--path", str(path)], input="n\n")
    assert result.exit_code == 1
    assert_in_string(["aborted"], result.stdout)


def test_create_error_template_not_found(
    runner: typer.testing.CliRunner, requests_mock: requests_mock.Mocker, template_names: list[str]
):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    result = runner.invoke(cli.app, ["create", "foobar"])
    assert result.exit_code == 1
    assert_in_string(["foobar", "found no matching templates"], result.stdout)


def test_create_error_path_is_dir(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    template_names: list[str],
    template_content: str,
    tmp_path: pathlib.Path,
):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    requests_mock.get(f"{api.Template._api}/go", text=template_content)
    path = pathlib.Path(tmp_path)
    result = runner.invoke(cli.app, ["create", "go", "--path", str(path)])
    assert result.exit_code == 1
    assert_in_string([f"{path}", "is a directory"], result.stdout)


def test_create_error_path_is_not_writable(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    template_names: list[str],
    template_content: str,
    tmp_path: pathlib.Path,
):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    requests_mock.get(f"{api.Template._api}/go", text=template_content)
    tmp_path.chmod(0o0555)
    path = tmp_path / ".gitignore"
    result = runner.invoke(cli.app, ["create", "go", "--path", str(path)])
    assert result.exit_code == 1
    assert_in_string([f"{path}", "permission denied"], result.stdout)
