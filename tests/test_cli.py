import pathlib

import requests
import requests_mock
from conftest import TestConsole, assert_in_string

import ignoro.cli


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
    assert_in_string(["failed", "connect"], result.stderr)


def test_list_error_connection(
    console: TestConsole,
    requests_mock: requests_mock.Mocker,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=requests.exceptions.ConnectionError)

    result = console.runner.invoke(ignoro.app, ["list"])

    assert result.exit_code == 1
    assert_in_string(["failed", "connect"], result.stderr)


def test_add_error_connection(
    console: TestConsole,
    requests_mock: requests_mock.Mocker,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=requests.ConnectionError)
    requests_mock.get(f"{ignoro.BASE_URL}/ruby", exc=requests.ConnectionError)
    template_list = ignoro.TemplateList([ignoro.Template("go")])
    gitignore = ignoro.Gitignore(template_list)
    path = pathlib.Path(console.cwd) / ".gitignore"
    gitignore.dump(path)

    result = console.runner.invoke(ignoro.app, ["add", "ruby"])

    assert result.exit_code == 1
    assert_in_string(["failed", "connect"], result.stderr)


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
        assert_in_string(["foobar", "found", "no matching"], result.stderr)


class TestCreateCommand:
    def test_create_file(
        self,
        console: TestConsole,
    ):
        path = pathlib.Path(console.cwd) / ".gitignore"
        result = console.runner.invoke(ignoro.app, ["create", "go"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == str(ignoro.Template("go")).splitlines(keepends=True)

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
            assert file.readlines()[3:-2] == str(ignoro.Template("go")).splitlines(keepends=True)

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
            assert file.readlines()[3:-2] == (
                str(ignoro.Template("go")).splitlines(keepends=True)
                + ["\n"]
                + str(ignoro.Template("ruby")).splitlines(keepends=True)
            )

    def test_create_error_template_not_found(
        self,
        console: TestConsole,
    ):
        result = console.runner.invoke(ignoro.app, ["create", "foobar"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["foobar", "found", "no matching"], result.stderr)

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
            assert file.readlines()[3:-2] == str(ignoro.Template("go")).splitlines(keepends=True)

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
        assert_in_string([str(console.cwd), "directory"], result.stderr)

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
        gitignore.dump(path)

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
        gitignore.dump(path)

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
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["show"])

        assert result.exit_code == 0
        assert result.stdout.split() == []

    def test_show_error_file_not_exists(
        self,
        console: TestConsole,
    ):
        result = console.runner.invoke(ignoro.app, ["show"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["does not exist"], result.stderr)

    def test_show_error_parse(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go"), ignoro.Template("ruby")])
        path = pathlib.Path(console.cwd) / ".gitignore"
        path.write_text(str(template_list))

        result = console.runner.invoke(ignoro.app, ["show"])

        assert result.exit_code == 1
        assert_in_string([str(console.cwd), "not valid"], result.stderr)


class TestAddCommand:
    def test_add(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["add", "ruby"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == (
                str(ignoro.Template("go")).splitlines(keepends=True)
                + ["\n"]
                + str(ignoro.Template("ruby")).splitlines(keepends=True)
            )

    def test_add_at_path(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go")])
        gitignore = ignoro.Gitignore(template_list)
        subdir = pathlib.Path(console.cwd) / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["add", "ruby", "--path", f"{str(path)}"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == (
                str(ignoro.Template("go")).splitlines(keepends=True)
                + ["\n"]
                + str(ignoro.Template("ruby")).splitlines(keepends=True)
            )

    def test_add_error_path_is_dir(
        self,
        console: TestConsole,
    ):
        result = console.runner.invoke(ignoro.app, ["add", "ruby", "--path", str(console.cwd)])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string([str(console.cwd), "directory"], result.stderr)

    def test_add_error_template_not_found(self, console: TestConsole):
        template_list = ignoro.TemplateList([ignoro.Template("go")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["add", "foobar"])

        assert result.exit_code == 1
        assert_in_string(["foobar", "found", "no matching"], result.stderr)

    def test_add_error_parse(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go")])
        path = pathlib.Path(console.cwd) / ".gitignore"
        path.write_text(str(template_list))

        result = console.runner.invoke(ignoro.app, ["add", "ruby"])

        assert result.exit_code == 1
        assert_in_string([str(console.cwd), "not valid"], result.stderr)

    def test_add_to_existing(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["add", "go"], input="y\n")

        assert result.exit_code == 0
        assert_in_string(["already exists", "replace"], result.stdout)
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == str(ignoro.Template("go")).splitlines(keepends=True)

    def test_add_to_existing_error(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["add", "go"], input="n\n")

        assert result.exit_code == 0
        assert_in_string(["already exists", "replace"], result.stdout)

    def test_add_error_file_not_exists(
        self,
        console: TestConsole,
    ):
        result = console.runner.invoke(ignoro.app, ["add", "go"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["does not exist"], result.stderr)

    def test_add_add_string(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["add", "go", "--show-gitignore"])

        assert result.exit_code == 0
        assert "".join(result.stdout.splitlines()[3:-2]) == str(ignoro.Template("go")).replace("\n", "")


class TestAddCommand:
    def test_add(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["add", "ruby"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == (
                str(ignoro.Template("go")).splitlines(keepends=True)
                + ["\n"]
                + str(ignoro.Template("ruby")).splitlines(keepends=True)
            )

    def test_add_at_path(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go")])
        gitignore = ignoro.Gitignore(template_list)
        subdir = pathlib.Path(console.cwd) / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["add", "ruby", "--path", f"{str(path)}"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == (
                str(ignoro.Template("go")).splitlines(keepends=True)
                + ["\n"]
                + str(ignoro.Template("ruby")).splitlines(keepends=True)
            )

    def test_add_error_path_is_dir(
        self,
        console: TestConsole,
    ):
        result = console.runner.invoke(ignoro.app, ["add", "ruby", "--path", str(console.cwd)])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string([str(console.cwd), "directory"], result.stderr)

    def test_add_error_template_not_found(self, console: TestConsole):
        template_list = ignoro.TemplateList([ignoro.Template("go")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["add", "foobar"])

        assert result.exit_code == 1
        assert_in_string(["foobar", "found", "no matching"], result.stderr)

    def test_add_error_parse(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go")])
        path = pathlib.Path(console.cwd) / ".gitignore"
        path.write_text(str(template_list))

        result = console.runner.invoke(ignoro.app, ["add", "ruby"])

        assert result.exit_code == 1
        assert_in_string([str(console.cwd), "not valid"], result.stderr)

    def test_add_to_existing(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["add", "go"], input="y\n")

        assert result.exit_code == 0
        assert_in_string(["already exists", "replace"], result.stdout)
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == str(ignoro.Template("go")).splitlines(keepends=True)

    def test_add_to_existing_error(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["add", "go"], input="n\n")

        assert result.exit_code == 0
        assert_in_string(["already exists", "replace"], result.stdout)

    def test_add_error_file_not_exists(
        self,
        console: TestConsole,
    ):
        result = console.runner.invoke(ignoro.app, ["add", "go"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["does not exist"], result.stderr)

    def test_add_add_string(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["add", "go", "--show-gitignore"])

        assert result.exit_code == 0
        assert "".join(result.stdout.splitlines()[3:-2]) == str(ignoro.Template("go")).replace("\n", "")


class TestRemove:
    def test_remove(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go"), ignoro.Template("ruby")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        gitignore.dump(path)

        result = console.runner.invoke(ignoro.app, ["remove", "go"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == str(ignoro.Template("ruby")).splitlines(keepends=True)

    def test_remove_at_path(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go"), ignoro.Template("ruby")])
        gitignore = ignoro.Gitignore(template_list)
        subdir = pathlib.Path(console.cwd) / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        gitignore.dump(path)
        result = console.runner.invoke(ignoro.app, ["remove", "go", "--path", f"{str(path)}"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == str(ignoro.Template("ruby")).splitlines(keepends=True)

    def test_remove_string(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go"), ignoro.Template("ruby")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        gitignore.dump(path)
        result = console.runner.invoke(ignoro.app, ["remove", "go", "--show-gitignore"])

        assert result.exit_code == 0
        assert "".join(result.stdout.splitlines()[3:-2]) == str(ignoro.Template("ruby")).replace("\n", "")

    def test_remove_error_path_is_dir(
        self,
        console: TestConsole,
    ):
        result = console.runner.invoke(ignoro.app, ["remove", "go", "--path", str(console.cwd)])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string([str(console.cwd), "directory"], result.stderr)

    def test_remove_error_parse(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go"), ignoro.Template("ruby")])
        path = pathlib.Path(console.cwd) / ".gitignore"
        path.write_text(str(template_list))
        result = console.runner.invoke(ignoro.app, ["remove", "go"])

        assert result.exit_code == 1
        assert_in_string([str(console.cwd), "not valid"], result.stderr)

    def test_remove_template_not_in_gitignore(
        self,
        console: TestConsole,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("ruby")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(console.cwd) / ".gitignore"
        gitignore.dump(path)
        result = console.runner.invoke(ignoro.app, ["remove", "go"])

        assert result.exit_code == 0
        assert_in_string(["go", "does not exist"], result.stderr)

    def test_remove_error_file_not_exists(
        self,
        console: TestConsole,
    ):
        result = console.runner.invoke(ignoro.app, ["remove", "go"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["does not exist"], result.stderr)
