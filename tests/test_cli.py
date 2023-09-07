import pathlib

import requests
import requests_mock
from conftest import TestConsole
from typing_extensions import Sequence

import ignoro.cli


def assert_in_string(fragments: Sequence[str], string: str):
    __tracebackhide__ = True
    for fragment in fragments:
        assert fragment.lower() in string.lower()


def test_create_error_connection(
    console: TestConsole,
    requests_mock: requests_mock.Mocker,
    tmp_path: pathlib.Path,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=requests.ConnectionError)
    requests_mock.get(f"{ignoro.BASE_URL}/go", exc=requests.ConnectionError)
    path = tmp_path / ".gitignore"

    result = console.runner.invoke(ignoro.cli.app, ["create", "go", "--path", str(path)])

    assert result.exit_code == 1
    assert_in_string(["failed to connect"], result.stderr)


def test_list_error_connection(
    console: TestConsole,
    requests_mock: requests_mock.Mocker,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=requests.exceptions.ConnectionError)

    result = console.runner.invoke(ignoro.app, ["list"])

    assert result.exit_code == 1
    assert_in_string(["failed to connect"], result.stderr)


class TestListCommand:
    def test_list(
        self,
        console: TestConsole,
        mock_template_list_names: list[str],
    ):
        result = console.runner.invoke(ignoro.app, ["list"])

        assert result.exit_code == 0
        assert str.split(result.stdout) == mock_template_list_names

    def test_list_search(
        self,
        console: TestConsole,
    ):
        result = console.runner.invoke(ignoro.app, ["list", "ja"])

        assert result.exit_code == 0
        assert str.split(result.stdout) == ["django", "java", "javascript"]

    def test_list_search_no_result(
        self,
        console: TestConsole,
    ):
        result = console.runner.invoke(ignoro.app, ["list", "foobar"])

        assert result.exit_code == 1
        assert_in_string(["foobar", "found no matching"], result.stderr)


class TestCreateCommand:
    def test_create_file(
        self,
        console: TestConsole,
    ):
        path = pathlib.Path(console.cwd) / ".gitignore"
        result = console.runner.invoke(ignoro.app, ["create", "go"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-1] == str(ignoro.Template("go")).splitlines(keepends=True)

    def test_create_file_at_path(
        self,
        console: TestConsole,
    ):
        subdir = pathlib.Path(console.cwd) / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"

        result = console.runner.invoke(ignoro.app, ["create", "go", "--path", str(path)])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-1] == str(ignoro.Template("go")).splitlines(keepends=True)

    def test_create_string(
        self,
        console: TestConsole,
    ):
        result = console.runner.invoke(ignoro.app, ["create", "go", "--show-gitignore"])

        assert result.exit_code == 0
        assert "".join(result.stdout.splitlines()[3:-2]) == str(ignoro.Template("go")).replace("\n", "")

    def test_create_file_with_two_templates(
        self,
        console: TestConsole,
        tmp_path: pathlib.Path,
    ):
        path = tmp_path / ".gitignore"

        path = pathlib.Path(console.cwd) / ".gitignore"
        result = console.runner.invoke(ignoro.app, ["create", "go", "ruby"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-1] == (
                str(ignoro.Template("go")).splitlines(keepends=True)
                + str(ignoro.Template("ruby")).splitlines(keepends=True)
            )

    def test_create_error_template_not_found(
        self,
        console: TestConsole,
    ):
        result = console.runner.invoke(ignoro.app, ["create", "foobar"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["foobar", "found no matching templates"], result.stderr)

    def test_create_file_already_exists(
        self,
        console: TestConsole,
    ):
        path = pathlib.Path(console.cwd) / ".gitignore"
        path.touch()
        result = console.runner.invoke(ignoro.app, ["create", "go"], input="y\n")

        assert result.exit_code == 0
        assert_in_string(["already exists", "overwrite"], result.stdout)
        with open(path, "r") as file:
            assert file.readlines()[3:-1] == str(ignoro.Template("go")).splitlines(keepends=True)

    def test_create_error_file_already_exists(
        self,
        console: TestConsole,
    ):
        path = pathlib.Path(console.cwd) / ".gitignore"
        path.touch()
        result = console.runner.invoke(ignoro.app, ["create", "go"], input="n\n")

        assert result.exit_code == 1
        assert_in_string(["already exists", "overwrite"], result.stdout)
        assert_in_string(["aborted"], result.stderr)

    def test_create_error_path_is_dir(
        self,
        console: TestConsole,
    ):
        result = console.runner.invoke(ignoro.app, ["create", "go", "--path", str(console.cwd)])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string([str(console.cwd), "is a directory"], result.stderr.replace("\n", " "))

    def test_create_error_path_is_not_writable(
        self,
        console: TestConsole,
    ):
        pathlib.Path(console.cwd).chmod(0o0555)
        result = console.runner.invoke(ignoro.app, ["create", "go"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string([str(console.cwd), "permission denied"], result.stderr)


class TestShowCommand:
    def test_show(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go"), ignoro.Template("ruby")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        path.write_text(gitignore.dumps())

        result = console.runner.invoke(ignoro.app, ["show"])

        assert result.exit_code == 0
        assert result.stdout.split() == ["go", "ruby"]

    def test_show_at_path(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go"), ignoro.Template("ruby")])
        gitignore = ignoro.Gitignore(template_list)
        subdir = pathlib.Path(console.cwd) / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        path.write_text(gitignore.dumps())

        result = console.runner.invoke(ignoro.app, ["show", "--path", f"{str(path)}"])

        assert result.exit_code == 0
        assert result.stdout.split() == ["go", "ruby"]

    def test_show_empty_file(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        path.write_text(gitignore.dumps())

        result = console.runner.invoke(ignoro.app, ["show"])

        assert result.exit_code == 0
        assert result.stdout.split() == []

    def test_show_error_parse(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go"), ignoro.Template("ruby")])
        path = pathlib.Path(console.cwd) / ".gitignore"
        path.write_text(str(template_list))

        result = console.runner.invoke(ignoro.app, ["show"])

        assert result.exit_code == 1
        assert_in_string([str(console.cwd), "not a valid ignoro gitignore file"], result.stderr)
