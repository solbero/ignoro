import pathlib

import requests
import requests_mock
import typer.testing
from typing_extensions import Sequence

import ignoro.cli


def assert_in_string(fragments: Sequence[str], string: str):
    __tracebackhide__ = True
    for fragment in fragments:
        assert fragment.lower() in string.lower()


def test_create_error_connection(
    runner: typer.testing.CliRunner, requests_mock: requests_mock.Mocker, tmp_path: pathlib.Path
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=requests.ConnectionError)
    requests_mock.get(f"{ignoro.BASE_URL}/go", exc=requests.ConnectionError)
    path = tmp_path / ".gitignore"
    result = runner.invoke(ignoro.cli.app, ["create", "go", "--path", str(path)])
    assert result.exit_code == 1
    assert_in_string(["failed to connect"], result.stderr)


def test_list_error_connection(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=requests.exceptions.ConnectionError)
    result = runner.invoke(ignoro.app, ["list"])
    assert result.exit_code == 1
    assert_in_string(["failed to connect"], result.stderr)


def test_list(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    mock_template_names: list[str],
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    result = runner.invoke(ignoro.app, ["list"])
    assert result.exit_code == 0
    assert str.split(result.stdout) == mock_template_names


def test_list_filter(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    mock_template_names: list[str],
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    result = runner.invoke(ignoro.app, ["list", "ja"])
    assert result.exit_code == 0
    assert str.split(result.stdout) == ["django", "java", "javascript"]


def test_list_filter_no_result(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    mock_template_names: list[str],
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    result = runner.invoke(ignoro.app, ["list", "foobar"])
    assert result.exit_code == 1
    assert_in_string(["foobar", "found no matching"], result.stdout)


def test_create(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    mock_template_names: list[str],
    mock_template_go: str,
    tmp_path: pathlib.Path,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    requests_mock.get(f"{ignoro.BASE_URL}/go", text=mock_template_go)
    path = tmp_path / ".gitignore"
    result = runner.invoke(ignoro.app, ["create", "go", "--path", str(path)])
    assert result.exit_code == 0
    with open(path, "r") as file:
        assert file.readlines()[3:-1] == str(ignoro.Template("go")).splitlines(keepends=True)


def test_create_two_templates(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    mock_template_names: list[str],
    mock_template_go: str,
    mock_template_ruby: str,
    tmp_path: pathlib.Path,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    requests_mock.get(f"{ignoro.BASE_URL}/go", text=mock_template_go)
    requests_mock.get(f"{ignoro.BASE_URL}/ruby", text=mock_template_ruby)
    path = tmp_path / ".gitignore"
    result = runner.invoke(ignoro.app, ["create", "go", "ruby", "--path", str(path)])
    assert result.exit_code == 0
    with open(path, "r") as file:
        assert file.readlines()[3:-1] == str(ignoro.Template("go")).splitlines(keepends=True) + str(
            ignoro.Template("ruby")
        ).splitlines(keepends=True)


def test_create_already_exists(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    mock_template_names: list[str],
    mock_template_go: str,
    tmp_path: pathlib.Path,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    requests_mock.get(f"{ignoro.BASE_URL}/go", text=mock_template_go)
    path = tmp_path / ".gitignore"
    path.touch()
    result = runner.invoke(ignoro.app, ["create", "go", "--path", str(path)], input="y\n")
    assert result.exit_code == 0
    assert_in_string(["already exists", "overwrite"], result.stdout)
    with open(path, "r") as file:
        assert file.readlines()[3:-1] == str(ignoro.Template("go")).splitlines(keepends=True)


def test_create_error_path_already_exists(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    mock_template_names: list[str],
    mock_template_go: str,
    tmp_path: pathlib.Path,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    requests_mock.get(f"{ignoro.BASE_URL}/go", text=mock_template_go)
    path = tmp_path / ".gitignore"
    path.touch()
    result = runner.invoke(ignoro.app, ["create", "go", "--path", str(path)], input="n\n")
    assert result.exit_code == 1
    assert_in_string(["already exists", "overwrite"], result.stdout)
    assert_in_string(["aborted"], result.stderr)


def test_create_error_template_not_found(
    runner: typer.testing.CliRunner, requests_mock: requests_mock.Mocker, mock_template_names: list[str]
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    result = runner.invoke(ignoro.app, ["create", "foobar"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert_in_string(["foobar", "found no matching templates"], result.stderr)


def test_create_error_path_is_dir(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    mock_template_names: list[str],
    mock_template_go: str,
    tmp_path: pathlib.Path,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    requests_mock.get(f"{ignoro.BASE_URL}/go", text=mock_template_go)
    result = runner.invoke(ignoro.app, ["create", "go", "--path", str(tmp_path)])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert_in_string([f"{tmp_path}", "is a directory"], result.stderr)


def test_create_error_path_is_not_writable(
    runner: typer.testing.CliRunner,
    requests_mock: requests_mock.Mocker,
    mock_template_names: list[str],
    mock_template_go: str,
    tmp_path: pathlib.Path,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    requests_mock.get(f"{ignoro.BASE_URL}/go", text=mock_template_go)
    tmp_path.chmod(0o0555)
    path = tmp_path / ".gitignore"
    result = runner.invoke(ignoro.app, ["create", "go", "--path", str(path)])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert_in_string([f"{path}", "permission denied"], result.stderr)
