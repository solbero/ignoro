import pytest
import requests
import requests_mock
from conftest import TemplateMock, TestConsole, assert_in_string

import ignoro.cli
from ignoro.api import Gitignore


class TestSearchCommand:
    def test_search_all(
        self,
        test_console: TestConsole,
        template_list_names_mock: tuple[str, ...],
    ):
        result = test_console.runner.invoke(ignoro.app, ("search",))

        assert result.exit_code == 0
        assert tuple(str.split(result.stdout)) == template_list_names_mock

    def test_search_term(
        self,
        test_console: TestConsole,
    ):
        name = "do"
        result = test_console.runner.invoke(ignoro.app, ("search", name))

        assert result.exit_code == 0
        assert tuple(str.split(result.stdout)) == ("dotdot", "double-dash")

    def test_search_search_no_result(
        self,
        test_console: TestConsole,
    ):
        name = "fizzbuzz"
        result = test_console.runner.invoke(ignoro.app, ("search", name))

        assert result.exit_code == 1
        assert_in_string(("error", "no matching", name), result.stderr)

    @pytest.mark.parametrize(
        "error, fragments",
        (
            (requests.exceptions.Timeout, ("error", "connection", "timed", "out")),
            (requests.exceptions.ConnectionError, ("error", "failed", "connect")),
        ),
    )
    def test_search_error_remote_list_not_found(
        self,
        test_console: TestConsole,
        requests_mock: requests_mock.Mocker,
        error: requests.exceptions.RequestException,
        fragments: tuple[str, ...],
    ):
        requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=error)
        result = test_console.runner.invoke(ignoro.app, ("search",))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(fragments, result.stderr)


class TestCreateCommand:
    def test_create_file(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        path = test_console.cwd / ".gitignore"
        result = test_console.runner.invoke(ignoro.app, ("create", foo_template_mock.name))

        assert result.exit_code == 0
        assert str(Gitignore.load(path).template_list) == foo_template_mock.content

    def test_create_file_at_path(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        subdir = test_console.cwd / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"

        result = test_console.runner.invoke(ignoro.app, ("create", foo_template_mock.name, "--path", str(path)))

        assert result.exit_code == 0
        assert str(Gitignore.load(path).template_list) == foo_template_mock.content

    def test_create_show(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        result = test_console.runner.invoke(ignoro.app, ("create", foo_template_mock.name, "--show-gitignore"))

        assert result.exit_code == 0
        assert str(Gitignore.loads(result.stdout).template_list) == foo_template_mock.content

    def test_create_file_two_templates(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        path = test_console.cwd / ".gitignore"
        result = test_console.runner.invoke(ignoro.app, ("create", foo_template_mock.name, bar_template_mock.name))

        assert result.exit_code == 0
        assert str(Gitignore.load(path).template_list) == f"{foo_template_mock.content}\n{bar_template_mock.content}"

    def test_create_file_already_exists_overwrite(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        path = test_console.cwd / ".gitignore"
        path.touch()
        result = test_console.runner.invoke(ignoro.app, ("create", foo_template_mock.name), input="y\n")

        assert result.exit_code == 0
        assert_in_string(("already exists", "overwrite"), result.stdout)

    def test_create_file_already_exists_abort(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        path = test_console.cwd / ".gitignore"
        path.touch()
        result = test_console.runner.invoke(ignoro.app, ("create", foo_template_mock.name), input="n\n")

        assert result.exit_code == 1
        assert_in_string(("already exists", "overwrite"), result.stdout)
        assert_in_string(("aborted",), result.stderr)

    @pytest.mark.parametrize(
        "error, fragments",
        (
            (requests.exceptions.ConnectionError, ("error", "failed", "connect")),
            (requests.exceptions.Timeout, ("error", "connection", "timed", "out")),
        ),
    )
    def test_create_error_remote_template_not_found(
        self,
        test_console: TestConsole,
        requests_mock: requests_mock.Mocker,
        foo_template_mock: TemplateMock,
        error: requests.exceptions.RequestException,
        fragments: tuple[str, ...],
    ):
        requests_mock.get(f"{ignoro.BASE_URL}/{foo_template_mock.name}", exc=error)
        result = test_console.runner.invoke(ignoro.app, ("create", foo_template_mock.name))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(fragments, result.stderr)

    def test_create_error_template_not_found(
        self,
        test_console: TestConsole,
    ):
        name = "fizzbuzz"
        result = test_console.runner.invoke(ignoro.app, ("create", name))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("error", "no matching", name), result.stderr)

    def test_create_error_path_is_dir(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        result = test_console.runner.invoke(
            ignoro.app, ("create", foo_template_mock.name, "--path", str(test_console.cwd)), input="y\n"
        )

        assert result.exit_code == 1
        assert_in_string(("error", "directory"), result.stderr)

    def test_create_error_permission_denied(
        self,
        test_console: TestConsole,
    ):
        test_console.cwd.chmod(0o0555)
        result = test_console.runner.invoke(ignoro.app, ("create", "foo"))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("error", "permission denied"), result.stderr)


class TestListCommand:
    def test_list(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList((foo_template, bar_template))
        gitignore = ignoro.Gitignore(template_list)

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ("list",))

        assert result.exit_code == 0
        assert tuple(result.stdout.split()) == (foo_template_mock.name, bar_template_mock.name)

    def test_list_at_path(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList((foo_template, bar_template))
        gitignore = ignoro.Gitignore(template_list)

        subdir = test_console.cwd / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ("list", "--path", f"{str(path)}"))

        assert result.exit_code == 0
        assert tuple(result.stdout.split()) == (foo_template_mock.name, bar_template_mock.name)

    def test_list_error_file_not_exists(
        self,
        test_console: TestConsole,
    ):
        result = test_console.runner.invoke(ignoro.app, ("list",))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("error", "file", "not exist"), result.stderr)

    def test_list_error_permission_denied(
        self,
        test_console: TestConsole,
    ):
        path = test_console.cwd / ".gitignore"
        path.touch()
        path.chmod(0o000)

        result = test_console.runner.invoke(ignoro.app, ("list",))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("error", "permission denied"), result.stderr)

    def test_list_error_file_invalid(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList((foo_template,))

        path = test_console.cwd / ".gitignore"
        path.write_text(str(template_list))

        result = test_console.runner.invoke(ignoro.app, ("list",))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("error", "file", "invalid", "missing", "header", "footer"), result.stderr)

    def test_list_error_empty_body(
        self,
        test_console: TestConsole,
    ):
        template_list = ignoro.TemplateList()
        gitignore = ignoro.Gitignore(template_list)

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ("list",))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("error", "missing", "body"), result.stderr)


class TestAddCommand:
    def test_add(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList((foo_template,))
        gitignore = ignoro.Gitignore(template_list)

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ("add", bar_template_mock.name))

        assert result.exit_code == 0
        assert str(Gitignore.load(path).template_list) == f"{foo_template_mock.content}\n{bar_template_mock.content}"

    def test_add_at_path(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_temlate = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList((foo_temlate,))
        gitignore = ignoro.Gitignore(template_list)

        subdir = test_console.cwd / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ("add", bar_template_mock.name, "--path", str(path)))

        assert result.exit_code == 0
        assert str(Gitignore.load(path).template_list) == f"{foo_template_mock.content}\n{bar_template_mock.content}"

    def test_add_string(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList((foo_template,))
        gitignore = ignoro.Gitignore(template_list)

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ("add", bar_template_mock.name, "--show-gitignore"))

        assert result.exit_code == 0
        assert (
            str(Gitignore.loads(result.stdout).template_list)
            == f"{foo_template_mock.content}\n{bar_template_mock.content}"
        )

    def test_add_error_path_is_dir(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        result = test_console.runner.invoke(
            ignoro.app, ("add", foo_template_mock.name, "--path", str(test_console.cwd))
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("could not", "add", "directory"), result.stderr)

    def test_add_error_template_not_found(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList((foo_template,))
        gitignore = ignoro.Gitignore(template_list)

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ("add", "fizzbuzz"))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("fizzbuzz", "found", "no matching"), result.stderr)

    def test_add_error_parse(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_temlate = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList((foo_temlate,))

        path = test_console.cwd / ".gitignore"
        path.write_text(str(template_list))

        result = test_console.runner.invoke(ignoro.app, ("add", bar_template_mock.name))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("could not", "add"), result.stderr)

    def test_add_to_existing(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList((foo_template,))
        gitignore = ignoro.Gitignore(template_list)

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ("add", foo_template_mock.name), input="y\n")

        assert result.exit_code == 0
        assert_in_string(("already exists", "replace"), result.stdout)
        assert str(Gitignore.load(path).template_list) == foo_template_mock.content

    def test_add_to_existing_declined(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList((foo_template,))
        gitignore = ignoro.Gitignore(template_list)

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ("add", foo_template_mock.name), input="n\n")

        assert result.exit_code == 0
        assert_in_string(("already exists", "replace"), result.stdout)

    def test_add_error_file_not_exists(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        result = test_console.runner.invoke(ignoro.app, ("add", foo_template_mock.name))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("could not", "add", "does not exist"), result.stderr)

    def test_add_error_write_permission_denied(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList((foo_template,))
        gitignore = ignoro.Gitignore(template_list)

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)
        path.chmod(0o0555)

        result = test_console.runner.invoke(ignoro.app, ("add", bar_template_mock.name))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("could not", "add", "permission denied"), result.stderr)


class TestRemove:
    def test_remove(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList((foo_template, bar_template))
        gitignore = ignoro.Gitignore(template_list)

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ("remove", foo_template_mock.name))

        assert result.exit_code == 0
        assert str(Gitignore.load(path).template_list) == bar_template_mock.content

    def test_remove_at_path(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList((foo_template, bar_template))
        gitignore = ignoro.Gitignore(template_list)

        subdir = test_console.cwd / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ("remove", foo_template_mock.name, "--path", str(path)))

        assert result.exit_code == 0
        assert str(Gitignore.load(path).template_list) == bar_template_mock.content

    def test_remove_string(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList((foo_template, bar_template))
        gitignore = ignoro.Gitignore(template_list)

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)
        result = test_console.runner.invoke(ignoro.app, ("remove", foo_template_mock.name, "--show-gitignore"))

        assert result.exit_code == 0
        assert str(Gitignore.loads(result.stdout).template_list) == bar_template_mock.content

    def test_remove_error_path_is_dir(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        result = test_console.runner.invoke(
            ignoro.app, ("remove", foo_template_mock.name, "--path", str(test_console.cwd))
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("could not", "remove", "directory"), result.stderr)

    def test_remove_error_parse(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList((foo_template, bar_template))

        path = test_console.cwd / ".gitignore"
        path.write_text(str(template_list))

        result = test_console.runner.invoke(ignoro.app, ("remove", foo_template_mock.name))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("could not", "remove"), result.stderr)

    def test_remove_template_error_not_in_gitignore(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList((bar_template,))
        gitignore = ignoro.Gitignore(template_list)

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ("remove", foo_template_mock.name))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("could not", "remove", "found", "no matching", foo_template_mock.name), result.stderr)

    def test_remove_error_file_not_exists(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        result = test_console.runner.invoke(ignoro.app, ("remove", foo_template_mock.name))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("could not", "remove", "does not exist"), result.stderr)

    def test_remove_error_write_permission_denied(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList((foo_template, bar_template))
        gitignore = ignoro.Gitignore(template_list)

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)
        path.chmod(0o0555)

        result = test_console.runner.invoke(ignoro.app, ("remove", foo_template_mock.name))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("could not", "remove", "permission denied"), result.stderr)
