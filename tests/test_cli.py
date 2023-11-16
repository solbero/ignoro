import pathlib

import pytest
import requests
import requests_mock
import typer
from conftest import TestRunner, assert_in_string

import ignoro.cli


def test_create_error_connection(
    console: TestRunner,
    requests_mock: requests_mock.Mocker,
    tmp_path: pathlib.Path,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=requests.ConnectionError)
    requests_mock.get(f"{ignoro.BASE_URL}/connerror", exc=requests.ConnectionError)
    path = tmp_path / ".gitignore"

    result = console.runner.invoke(ignoro.cli.app, ["create", "connerror", "--path", str(path)])

    assert result.exit_code == 1
    assert_in_string(["failed", "connect"], result.stderr)


def test_list_error_connection(
    console: TestRunner,
    requests_mock: requests_mock.Mocker,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=requests.exceptions.ConnectionError)

    result = console.runner.invoke(ignoro.app, ["list"])

    assert result.exit_code == 1
    assert_in_string(["failed", "connect"], result.stderr)


def test_add_error_connection(
    console: TestRunner,
    requests_mock: requests_mock.Mocker,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=requests.ConnectionError)
    requests_mock.get(f"{ignoro.BASE_URL}/connerror", exc=requests.ConnectionError)
    template_list = ignoro.TemplateList([ignoro.Template("foo")])
    gitignore = ignoro.Gitignore(template_list)
    path = pathlib.Path(console.cwd) / ".gitignore"
    gitignore.dump(path)

    result = console.runner.invoke(ignoro.app, ["add", "connerror"])

    assert result.exit_code == 1
    assert_in_string(["failed", "connect"], result.stderr)


class TestListCommand:
    def test_list(
        self,
        test_runner: TestRunner,
        template_list_names_mock: list[str],
    ):
        result = test_runner.runner.invoke(ignoro.app, ["list"])

        assert result.exit_code == 0
        assert str.split(result.stdout) == template_list_names_mock

    def test_list_search(
        self,
        test_runner: TestRunner,
    ):
        result = test_runner.runner.invoke(ignoro.app, ["list", "do"])

        assert result.exit_code == 0
        assert str.split(result.stdout) == ["dotdot", "double-dash"]

    def test_list_search_no_result(
        self,
        test_runner: TestRunner,
    ):
        result = test_runner.runner.invoke(ignoro.app, ["list", "foobar"])

        assert result.exit_code == 1
        assert_in_string(["foobar", "found", "no matching"], result.stderr)


class TestCreateCommand:
    def test_create_file(
        self,
        test_runner: TestRunner,
    ):
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        result = test_runner.runner.invoke(ignoro.app, ["create", "foo"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == str(ignoro.Template("foo")).splitlines(keepends=True)

    def test_create_file_at_path(
        self,
        test_runner: TestRunner,
    ):
        subdir = pathlib.Path(test_runner.cwd) / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"

        result = test_runner.runner.invoke(ignoro.app, ["create", "foo", "--path", str(path)])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == str(ignoro.Template("foo")).splitlines(keepends=True)

    def test_create_string(
        self,
        test_runner: TestRunner,
    ):
        result = test_runner.runner.invoke(ignoro.app, ["create", "foo", "--show-gitignore"])

        assert result.exit_code == 0
        assert "".join(result.stdout.splitlines()[3:-2]) == str(ignoro.Template("foo")).replace("\n", "")

    def test_create_file_with_two_templates(
        self,
        test_runner: TestRunner,
        tmp_path: pathlib.Path,
    ):
        path = tmp_path / ".gitignore"

        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        result = test_runner.runner.invoke(ignoro.app, ["create", "foo", "bar"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == (
                str(ignoro.Template("bar")).splitlines(keepends=True)
                + ["\n"]
                + str(ignoro.Template("foo")).splitlines(keepends=True)
            )

    def test_create_error_template_not_found(
        self,
        test_runner: TestRunner,
    ):
        result = test_runner.runner.invoke(ignoro.app, ["create", "foobar"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["foobar", "found", "no matching"], result.stderr)

    def test_create_file_already_exists(
        self,
        test_runner: TestRunner,
    ):
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        path.touch()
        result = test_runner.runner.invoke(ignoro.app, ["create", "foo"], input="y\n")

        assert result.exit_code == 0
        assert_in_string(["already exists", "overwrite"], result.stdout)
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == str(ignoro.Template("foo")).splitlines(keepends=True)

    def test_create_error_file_already_exists(
        self,
        test_runner: TestRunner,
    ):
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        path.touch()
        result = test_runner.runner.invoke(ignoro.app, ["create", "foo"], input="n\n")

        assert result.exit_code == 1
        assert_in_string(["already exists", "overwrite"], result.stdout)
        assert_in_string(["aborted"], result.stderr)

    def test_create_error_path_is_dir(
        self,
        test_runner: TestRunner,
    ):
        result = test_runner.runner.invoke(ignoro.app, ["create", "foo", "--path", str(test_runner.cwd)])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string([str(test_runner.cwd), "directory"], result.stderr)

    def test_create_error_path_is_not_writable(
        self,
        test_runner: TestRunner,
    ):
        pathlib.Path(test_runner.cwd).chmod(0o0555)
        result = test_runner.runner.invoke(ignoro.app, ["create", "foo"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string([str(test_runner.cwd), "permission denied"], result.stderr)


class TestShowCommand:
    def test_show(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo"), ignoro.Template("bar")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["show"])

        assert result.exit_code == 0
        assert result.stdout.split() == ["bar", "foo"]

    def test_show_at_path(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo"), ignoro.Template("bar")])
        gitignore = ignoro.Gitignore(template_list)
        subdir = pathlib.Path(test_runner.cwd) / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["show", "--path", f"{str(path)}"])

        assert result.exit_code == 0
        assert result.stdout.split() == ["bar", "foo"]

    def test_show_empty_file(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["show"])

        assert result.exit_code == 1

    def test_show_error_file_not_exists(
        self,
        test_runner: TestRunner,
    ):
        result = test_runner.runner.invoke(ignoro.app, ["show"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["does not exist"], result.stderr)

    def test_show_error_parse(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo"), ignoro.Template("bar")])
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        path.write_text(str(template_list))

        result = test_runner.runner.invoke(ignoro.app, ["show"])

        assert result.exit_code == 1
        assert_in_string([str(test_runner.cwd), "not valid"], result.stderr)


class TestAddCommand:
    def test_add(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["add", "bar"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == (
                str(ignoro.Template("foo")).splitlines(keepends=True)
                + ["\n"]
                + str(ignoro.Template("bar")).splitlines(keepends=True)
            )

    def test_add_at_path(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo")])
        gitignore = ignoro.Gitignore(template_list)
        subdir = pathlib.Path(test_runner.cwd) / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["add", "bar", "--path", f"{str(path)}"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == (
                str(ignoro.Template("foo")).splitlines(keepends=True)
                + ["\n"]
                + str(ignoro.Template("bar")).splitlines(keepends=True)
            )

    def test_add_error_path_is_dir(
        self,
        test_runner: TestRunner,
    ):
        result = test_runner.runner.invoke(ignoro.app, ["add", "bar", "--path", str(test_runner.cwd)])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string([str(test_runner.cwd), "directory"], result.stderr)

    def test_add_error_template_not_found(self, test_runner: TestRunner):
        template_list = ignoro.TemplateList([ignoro.Template("foo")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["add", "foobar"])

        assert result.exit_code == 1
        assert_in_string(["foobar", "found", "no matching"], result.stderr)

    def test_add_error_parse(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo")])
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        path.write_text(str(template_list))

        result = test_runner.runner.invoke(ignoro.app, ["add", "bar"])

        assert result.exit_code == 1
        assert_in_string([str(test_runner.cwd), "not valid"], result.stderr)

    def test_add_to_existing(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["add", "foo"], input="y\n")

        assert result.exit_code == 0
        assert_in_string(["already exists", "replace"], result.stdout)
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == str(ignoro.Template("foo")).splitlines(keepends=True)

    def test_add_to_existing_error(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["add", "foo"], input="n\n")

        assert result.exit_code == 0
        assert_in_string(["already exists", "replace"], result.stdout)

    def test_add_error_file_not_exists(
        self,
        test_runner: TestRunner,
    ):
        result = test_runner.runner.invoke(ignoro.app, ["add", "foo"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["does not exist"], result.stderr)

    def test_add_add_string(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["add", "foo", "--show-gitignore"])

        assert result.exit_code == 0
        assert "".join(result.stdout.splitlines()[3:-2]) == str(ignoro.Template("foo")).replace("\n", "")


class TestAddCommand:
    def test_add(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["add", "bar"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == (
                str(ignoro.Template("foo")).splitlines(keepends=True)
                + ["\n"]
                + str(ignoro.Template("bar")).splitlines(keepends=True)
            )

    def test_add_at_path(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo")])
        gitignore = ignoro.Gitignore(template_list)
        subdir = pathlib.Path(test_runner.cwd) / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["add", "bar", "--path", f"{str(path)}"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == (
                str(ignoro.Template("foo")).splitlines(keepends=True)
                + ["\n"]
                + str(ignoro.Template("bar")).splitlines(keepends=True)
            )

    def test_add_error_path_is_dir(
        self,
        test_runner: TestRunner,
    ):
        result = test_runner.runner.invoke(ignoro.app, ["add", "bar", "--path", str(test_runner.cwd)])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string([str(test_runner.cwd), "directory"], result.stderr)

    def test_add_error_template_not_found(self, test_runner: TestRunner):
        template_list = ignoro.TemplateList([ignoro.Template("foo")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["add", "foobar"])

        assert result.exit_code == 1
        assert_in_string(["foobar", "found", "no matching"], result.stderr)

    def test_add_error_parse(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo")])
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        path.write_text(str(template_list))

        result = test_runner.runner.invoke(ignoro.app, ["add", "bar"])

        assert result.exit_code == 1
        assert_in_string([str(test_runner.cwd), "not valid"], result.stderr)

    def test_add_to_existing(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["add", "foo"], input="y\n")

        assert result.exit_code == 0
        assert_in_string(["already exists", "replace"], result.stdout)
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == str(ignoro.Template("foo")).splitlines(keepends=True)

    def test_add_to_existing_error(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["add", "foo"], input="n\n")

        assert result.exit_code == 0
        assert_in_string(["already exists", "replace"], result.stdout)

    def test_add_error_file_not_exists(
        self,
        test_runner: TestRunner,
    ):
        result = test_runner.runner.invoke(ignoro.app, ["add", "foo"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["does not exist"], result.stderr)

    def test_add_add_string(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["add", "bar", "--show-gitignore"])

        assert result.exit_code == 0


class TestRemove:
    def test_remove(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo"), ignoro.Template("bar")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)

        result = test_runner.runner.invoke(ignoro.app, ["remove", "foo"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == str(ignoro.Template("bar")).splitlines(keepends=True)

    def test_remove_at_path(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo"), ignoro.Template("bar")])
        gitignore = ignoro.Gitignore(template_list)
        subdir = pathlib.Path(test_runner.cwd) / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        gitignore.dump(path)
        result = test_runner.runner.invoke(ignoro.app, ["remove", "foo", "--path", f"{str(path)}"])

        assert result.exit_code == 0
        with open(path, "r") as file:
            assert file.readlines()[3:-2] == str(ignoro.Template("bar")).splitlines(keepends=True)

    def test_remove_string(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo"), ignoro.Template("bar")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)
        result = test_runner.runner.invoke(ignoro.app, ["remove", "foo", "--show-gitignore"])

        assert result.exit_code == 0
        assert "".join(result.stdout.splitlines()[3:-2]) == str(ignoro.Template("bar")).replace("\n", "")

    def test_remove_error_path_is_dir(
        self,
        test_runner: TestRunner,
    ):
        result = test_runner.runner.invoke(ignoro.app, ["remove", "foo", "--path", str(test_runner.cwd)])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string([str(test_runner.cwd), "directory"], result.stderr)

    def test_remove_error_parse(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("foo"), ignoro.Template("bar")])
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        path.write_text(str(template_list))
        result = test_runner.runner.invoke(ignoro.app, ["remove", "foo"])

        assert result.exit_code == 1
        assert_in_string([str(test_runner.cwd), "not valid"], result.stderr)

    def test_remove_template_not_in_gitignore(
        self,
        test_runner: TestRunner,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("bar")])
        gitignore = ignoro.Gitignore(template_list)
        path = pathlib.Path(test_runner.cwd) / ".gitignore"
        gitignore.dump(path)
        result = test_runner.runner.invoke(ignoro.app, ["remove", "foo"])

        assert result.exit_code == 0
        assert_in_string(["foo", "does not exist"], result.stderr)

    def test_remove_error_file_not_exists(
        self,
        test_runner: TestRunner,
    ):
        result = test_runner.runner.invoke(ignoro.app, ["remove", "foo"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["does not exist"], result.stderr)
