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
        template_list_names_mock: list[str],
    ):
        result = test_console.runner.invoke(ignoro.app, ["search"])

        assert result.exit_code == 0
        assert result.stdout.split() == template_list_names_mock

    def test_search_term(
        self,
        test_console: TestConsole,
    ):
        result = test_console.runner.invoke(ignoro.app, ["search", "do"])

        assert result.exit_code == 0
        assert result.stdout.split() == ["dotdot", "double-dash"]

    def test_search_search_no_result(
        self,
        test_console: TestConsole,
    ):
        result = test_console.runner.invoke(ignoro.app, ["search", "fizzbuzz"])

        assert result.exit_code == 1
        assert_in_string(["error", "no matching", "fizzbuzz"], result.stderr)

    @pytest.mark.parametrize(
        ("error", "fragments"),
        [
            (requests.exceptions.Timeout, ["error", "connection", "timed", "out"]),
            (requests.exceptions.ConnectionError, ["error", "failed", "connect"]),
        ],
    )
    def test_search_error_remote_list_not_found(
        self,
        test_console: TestConsole,
        requests_mock: requests_mock.Mocker,
        error: requests.exceptions.RequestException,
        fragments: list[str],
    ):
        requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=error)
        result = test_console.runner.invoke(ignoro.app, ["search"])

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

        result = test_console.runner.invoke(ignoro.app, ["create", foo_template_mock.name])
        gitignore = Gitignore.load(path)
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)

        assert result.exit_code == 0
        assert result.stdout == ""
        assert gitignore.template_list == [foo_template]

    def test_create_file_at_path(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        subdir = test_console.cwd / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"

        result = test_console.runner.invoke(ignoro.app, ["create", foo_template_mock.name, "--path", str(path)])
        gitignore = Gitignore.load(path)
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)

        assert result.exit_code == 0
        assert result.stdout == ""
        assert gitignore.template_list == [foo_template]

    @pytest.mark.xfail(reason="Setting terminal width does not change the width of the terminal in the test.")
    def test_create_show(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        result = test_console.runner.invoke(
            ignoro.app, ["create", foo_template_mock.name, "--show-gitignore"], terminal_width=100
        )
        gitignore = Gitignore.loads(result.stdout)
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)

        assert result.exit_code == 0
        assert result.stdout == foo_template_mock.content
        assert gitignore.template_list == [foo_template]

    def test_create_file_two_templates(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        path = test_console.cwd / ".gitignore"

        result = test_console.runner.invoke(ignoro.app, ["create", foo_template_mock.name, bar_template_mock.name])
        gitignore = Gitignore.load(path)
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)

        assert result.exit_code == 0
        assert result.stdout == ""
        assert gitignore.template_list == [foo_template, bar_template]

    def test_create_file_already_exists_overwrite(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        path = test_console.cwd / ".gitignore"
        path.touch()

        result = test_console.runner.invoke(ignoro.app, ["create", foo_template_mock.name], input="y\n")
        gitignore = Gitignore.load(path)
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)

        assert result.exit_code == 0
        assert_in_string(["already", "exists", "overwrite"], result.stdout)
        assert gitignore.template_list == [foo_template]

    def test_create_file_already_exists_abort(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        path = test_console.cwd / ".gitignore"
        path.touch()

        result = test_console.runner.invoke(ignoro.app, ["create", foo_template_mock.name], input="n\n")
        gitignore = Gitignore.load(path)

        assert result.exit_code == 1
        assert_in_string(["already", "exists", "overwrite"], result.stdout)
        assert_in_string(["aborted"], result.stderr)
        assert gitignore.template_list == []

    @pytest.mark.parametrize(
        ("error", "fragments"),
        [
            (requests.exceptions.Timeout, ["error", "connection", "timed", "out"]),
            (requests.exceptions.ConnectionError, ["error", "failed", "connect"]),
        ],
    )
    def test_create_error_remote_template_list(
        self,
        test_console: TestConsole,
        requests_mock: requests_mock.Mocker,
        error: requests.exceptions.RequestException,
        fragments: list[str],
    ):
        requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=error)
        result = test_console.runner.invoke(ignoro.app, ("create", "foo"))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(fragments, result.stderr)

    @pytest.mark.parametrize(
        ("error", "fragments"),
        [
            (requests.exceptions.ConnectionError, ["error", "failed", "connect"]),
            (requests.exceptions.Timeout, ["error", "connection", "timed", "out"]),
        ],
    )
    def test_create_error_remote_template(
        self,
        test_console: TestConsole,
        requests_mock: requests_mock.Mocker,
        error: requests.exceptions.RequestException,
        fragments: list[str],
    ):
        requests_mock.get(f"{ignoro.BASE_URL}/foo", exc=error)
        result = test_console.runner.invoke(ignoro.app, ["create", "foo"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(fragments, result.stderr)

    def test_create_error_remote_template_not_found(
        self,
        test_console: TestConsole,
        requests_mock: requests_mock.Mocker,
    ):
        requests_mock.get(f"{ignoro.BASE_URL}/foo", status_code=404)
        result = test_console.runner.invoke(ignoro.app, ["create", "foo"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "failed", "fetch", "foo"], result.stderr)

    def test_create_error_template_not_exist(
        self,
        test_console: TestConsole,
    ):
        result = test_console.runner.invoke(ignoro.app, ["create", "fizzbuzz"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "no matching", "fizzbuzz"], result.stderr)

    def test_create_error_path_is_dir(
        self,
        test_console: TestConsole,
    ):
        result = test_console.runner.invoke(ignoro.app, ["create", "foo", "--path", str(test_console.cwd)], input="y\n")

        assert result.exit_code == 1
        assert_in_string(["already", "exists", "overwrite"], result.stdout)
        assert_in_string(["error", "directory"], result.stderr)

    def test_create_error_permission_denied(
        self,
        test_console: TestConsole,
    ):
        path = test_console.cwd / ".gitignore"
        path.touch()
        path.chmod(0o000)

        result = test_console.runner.invoke(ignoro.app, ["create", "foo"], input="y\n")
        path.chmod(0o755)

        assert result.exit_code == 1
        assert_in_string(["already", "exists", "overwrite"], result.stdout)
        assert_in_string(["error", "permission", "denied"], result.stderr)


class TestListCommand:
    def test_list(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_template, bar_template])
        gitignore = ignoro.Gitignore(template_list)

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ["list"])

        assert result.exit_code == 0
        assert result.stdout.split() == [foo_template_mock.name, bar_template_mock.name]

    def test_list_at_path(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_template, bar_template])
        gitignore = ignoro.Gitignore(template_list)

        subdir = test_console.cwd / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ["list", "--path", str(path)])

        assert result.exit_code == 0
        assert result.stdout.split() == [foo_template_mock.name, bar_template_mock.name]

    def test_list_error_file_not_exists(
        self,
        test_console: TestConsole,
    ):
        result = test_console.runner.invoke(ignoro.app, ["list"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "file", "not exist"], result.stderr)

    def test_list_error_permission_denied(
        self,
        test_console: TestConsole,
    ):
        path = test_console.cwd / ".gitignore"
        path.touch()
        path.chmod(0o000)

        result = test_console.runner.invoke(ignoro.app, ["list"])
        path.chmod(0o755)

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "permission", "denied"], result.stderr)

    def test_list_error_file_invalid(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        path = test_console.cwd / ".gitignore"
        path.write_text(foo_template_mock.body)

        result = test_console.runner.invoke(ignoro.app, ["list"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("error", "file", "invalid", "missing", "header"), result.stderr)

    def test_list_error_no_templates(
        self,
        test_console: TestConsole,
    ):
        gitignore = ignoro.Gitignore()

        path = test_console.cwd / ".gitignore"
        gitignore.dump(path)

        result = test_console.runner.invoke(ignoro.app, ["list"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "no", "templates", "found"], result.stderr)


class TestAddCommand:
    def test_add(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_template])

        path = test_console.cwd / ".gitignore"
        Gitignore(template_list).dump(path)

        result = test_console.runner.invoke(ignoro.app, ["add", bar_template.name])
        gitignore = Gitignore.load(path)

        assert result.exit_code == 0
        assert gitignore.template_list == [foo_template, bar_template]

    def test_add_at_path(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_temlate = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_temlate])

        subdir = test_console.cwd / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        Gitignore(template_list).dump(path)

        result = test_console.runner.invoke(ignoro.app, ["add", bar_template_mock.name, "--path", str(path)])
        gitignore = Gitignore.load(path)

        assert result.exit_code == 0
        assert gitignore.template_list == [foo_temlate, bar_template]

    @pytest.mark.xfail(reason="Setting terminal width does not change the width of the terminal in the test.")
    def test_add_show(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_template])

        path = test_console.cwd / ".gitignore"
        Gitignore(template_list).dump(path)

        result = test_console.runner.invoke(
            ignoro.app, ["add", bar_template_mock.name, "--show-gitignore"], terminal_width=100
        )
        gitignore = Gitignore.loads(result.stdout)

        assert result.exit_code == 0
        assert gitignore.template_list == [foo_template, bar_template]

    def test_add_to_existing_confirmed(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_bar_template = ignoro.Template(foo_template_mock.name, bar_template_mock.body)
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList([foo_bar_template])

        path = test_console.cwd / ".gitignore"
        Gitignore(template_list).dump(path)

        result = test_console.runner.invoke(ignoro.app, ["add", foo_template_mock.name], input="y\n")
        gitignore = Gitignore.load(path)

        assert result.exit_code == 0
        assert_in_string(("already exists", "replace"), result.stdout)
        assert gitignore.template_list == [foo_template]

    def test_add_to_existing_declined(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_bar_template = ignoro.Template(foo_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_bar_template])

        path = test_console.cwd / ".gitignore"
        Gitignore(template_list).dump(path)

        result = test_console.runner.invoke(ignoro.app, ["add", foo_template_mock.name], input="n\n")
        gitignore = Gitignore.load(path)

        assert result.exit_code == 0
        assert_in_string(("already exists", "replace"), result.stdout)
        assert gitignore.template_list == [foo_bar_template]

    def test_add_error_template_not_found(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList([foo_template])

        path = test_console.cwd / ".gitignore"
        Gitignore(template_list).dump(path)

        result = test_console.runner.invoke(ignoro.app, ["add", "fizzbuzz"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "no matching", "fizzbuzz"], result.stderr)

    def test_add_error_file_invalid(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        path = test_console.cwd / ".gitignore"
        path.write_text(foo_template_mock.body)

        result = test_console.runner.invoke(ignoro.app, ["add", bar_template_mock.name])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "file", "invalid", "missing", "header"], result.stderr)

    def test_add_error_file_not_exists(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        result = test_console.runner.invoke(ignoro.app, ["add", foo_template_mock.name])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "not exist"], result.stderr)

    def test_add_error_path_is_dir(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        result = test_console.runner.invoke(
            ignoro.app, ["add", foo_template_mock.name, "--path", str(test_console.cwd)]
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "directory"], result.stderr)

    def test_add_error_permission_denied(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList([foo_template])

        path = test_console.cwd / ".gitignore"
        Gitignore(template_list).dump(path)
        path.chmod(0o000)

        result = test_console.runner.invoke(ignoro.app, ["add", bar_template_mock.name])
        path.chmod(0o755)

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["permission", "denied"], result.stderr)

    @pytest.mark.parametrize(
        ("error", "fragments"),
        [
            (requests.exceptions.Timeout, ["error", "connection", "timed", "out"]),
            (requests.exceptions.ConnectionError, ["error", "failed", "connect"]),
        ],
    )
    def test_add_error_remote_template_list(
        self,
        test_console: TestConsole,
        requests_mock: requests_mock.Mocker,
        foo_template_mock: TemplateMock,
        error: requests.exceptions.RequestException,
        fragments: list[str],
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList([foo_template])

        path = test_console.cwd / ".gitignore"
        Gitignore(template_list).dump(path)

        requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=error)
        result = test_console.runner.invoke(ignoro.app, ["add", "bar"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(fragments, result.stderr)

    @pytest.mark.parametrize(
        ("error", "fragments"),
        [
            (requests.exceptions.Timeout, ["error", "connection", "timed", "out"]),
            (requests.exceptions.ConnectionError, ["error", "failed", "connect"]),
        ],
    )
    def test_add_error_remote_template(
        self,
        test_console: TestConsole,
        requests_mock: requests_mock.Mocker,
        foo_template_mock: TemplateMock,
        error: requests.exceptions.RequestException,
        fragments: list[str],
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList([foo_template])

        path = test_console.cwd / ".gitignore"
        Gitignore(template_list).dump(path)

        requests_mock.get(f"{ignoro.BASE_URL}/bar", exc=error)
        result = test_console.runner.invoke(ignoro.app, ["add", "bar"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(fragments, result.stderr)

    def test_add_error_remote_template_not_found(
        self,
        test_console: TestConsole,
        requests_mock: requests_mock.Mocker,
        foo_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list = ignoro.TemplateList([foo_template])

        path = test_console.cwd / ".gitignore"
        Gitignore(template_list).dump(path)

        requests_mock.get(f"{ignoro.BASE_URL}/bar", status_code=404)
        result = test_console.runner.invoke(ignoro.app, ["add", "bar"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "failed", "fetch", "bar"], result.stderr)


class TestRemoveCommand:
    def test_remove(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_template, bar_template])

        path = test_console.cwd / ".gitignore"
        Gitignore(template_list).dump(path)

        result = test_console.runner.invoke(ignoro.app, ["remove", foo_template.name])
        gitignore = Gitignore.load(path)

        assert result.exit_code == 0
        assert gitignore.template_list == [bar_template]

    def test_remove_at_path(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_template, bar_template])

        subdir = test_console.cwd / "subdir"
        subdir.mkdir()
        path = subdir / ".gitignore"
        Gitignore(template_list).dump(path)

        result = test_console.runner.invoke(ignoro.app, ["remove", foo_template_mock.name, "--path", str(path)])
        gitignore = Gitignore.load(path)

        assert result.exit_code == 0
        assert gitignore.template_list == [bar_template]

    @pytest.mark.xfail(reason="Setting terminal width does not change the width of the terminal in the test.")
    def test_remove_show(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_template, bar_template])

        path = test_console.cwd / ".gitignore"
        Gitignore(template_list).dump(path)

        result = test_console.runner.invoke(
            ignoro.app, ["remove", foo_template_mock.name, "--show-gitignore"], terminal_width=100
        )
        gitignore = Gitignore.loads(result.stdout)

        assert result.exit_code == 0
        assert gitignore.template_list == [bar_template]

    def test_remove_error_path_is_dir(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        result = test_console.runner.invoke(
            ignoro.app, ["remove", foo_template_mock.name, "--path", str(test_console.cwd)]
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "directory"], result.stderr)

    def test_remove_error_file_invalid(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        path = test_console.cwd / ".gitignore"
        path.write_text(foo_template_mock.body)

        result = test_console.runner.invoke(ignoro.app, ("remove", foo_template_mock.name))

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("error", "file", "invalid", "missing", "header"), result.stderr)

    def test_remove_error_template_not_found(
        self,
        test_console: TestConsole,
        bar_template_mock: TemplateMock,
    ):
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([bar_template])

        path = test_console.cwd / ".gitignore"
        Gitignore(template_list).dump(path)

        result = test_console.runner.invoke(ignoro.app, ["remove", "foo"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(("error", "no matching", "foo"), result.stderr)

    def test_remove_error_file_not_exists(
        self,
        test_console: TestConsole,
    ):
        result = test_console.runner.invoke(ignoro.app, ["remove", "foo"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "not exist"], result.stderr)

    def test_remove_error_write_permission_denied(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_template, bar_template])

        path = test_console.cwd / ".gitignore"
        Gitignore(template_list).dump(path)
        path.chmod(0o000)

        result = test_console.runner.invoke(ignoro.app, ["remove", foo_template_mock.name])
        path.chmod(0o755)

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "permission", "denied"], result.stderr)


class TestShowCommand:
    @pytest.mark.xfail(reason="Setting terminal width does not change the width of the terminal in the test.")
    def test_show(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        result = test_console.runner.invoke(ignoro.app, ["show", foo_template_mock.name], terminal_width=100)

        assert result.exit_code == 0
        assert result.stdout == foo_template_mock.content

    def test_show_error_template_not_found(
        self,
        test_console: TestConsole,
    ):
        result = test_console.runner.invoke(ignoro.app, ["show", "fizzbuzz"])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(["error", "no matching", "fizzbuzz"], result.stderr)

    @pytest.mark.parametrize(
        ("error", "fragments"),
        [
            (requests.exceptions.Timeout, ["error", "connection", "timed", "out"]),
            (requests.exceptions.ConnectionError, ["error", "failed", "connect"]),
        ],
    )
    def test_show_remote_template_list_not_found(
        self,
        test_console: TestConsole,
        requests_mock: requests_mock.Mocker,
        foo_template_mock: TemplateMock,
        error: requests.exceptions.RequestException,
        fragments: list[str],
    ):
        requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=error)
        result = test_console.runner.invoke(ignoro.app, ["show", foo_template_mock.name])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(fragments, result.stderr)

    @pytest.mark.parametrize(
        ("error", "fragments"),
        [
            (requests.exceptions.Timeout, ["error", "connection", "timed", "out"]),
            (requests.exceptions.ConnectionError, ["error", "failed", "connect"]),
        ],
    )
    def test_show_error_remote_template_not_found(
        self,
        test_console: TestConsole,
        requests_mock: requests_mock.Mocker,
        foo_template_mock: TemplateMock,
        error: requests.exceptions.RequestException,
        fragments: list[str],
    ):
        requests_mock.get(f"{ignoro.BASE_URL}/{foo_template_mock.name}", exc=error)
        result = test_console.runner.invoke(ignoro.app, ["show", foo_template_mock.name])

        assert result.exit_code == 1
        assert result.stdout == ""
        assert_in_string(fragments, result.stderr)


class TestIntegration:
    @pytest.mark.xfail(reason="Setting terminal width does not change the width of the terminal in the test.")
    def test_search_and_show(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)

        result = test_console.runner.invoke(ignoro.app, ["search", foo_template.name])

        assert result.exit_code == 0
        assert result.stdout.split() == ["foo", "foobar"]

        result = test_console.runner.invoke(ignoro.app, ["show", foo_template.name], terminal_width=100)
        gitignore = Gitignore.loads(result.stdout)

        assert result.exit_code == 0
        assert gitignore.template_list == [foo_template]

    def test_create_add_remove_and_list(
        self,
        test_console: TestConsole,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        path = test_console.cwd / ".gitignore"

        result = test_console.runner.invoke(ignoro.app, ["create", foo_template.name])
        gitignore = Gitignore.load(path)

        assert result.exit_code == 0
        assert gitignore.template_list == [foo_template]

        result = test_console.runner.invoke(ignoro.app, ["add", bar_template_mock.name])
        gitignore = Gitignore.load(path)

        assert result.exit_code == 0
        assert gitignore.template_list == [foo_template, bar_template]

        result = test_console.runner.invoke(ignoro.app, ["remove", foo_template_mock.name])
        gitignore = Gitignore.load(path)

        assert result.exit_code == 0
        assert gitignore.template_list == [bar_template]

        result = test_console.runner.invoke(ignoro.app, ["list"])

        assert result.exit_code == 0
        assert result.stdout.split() == [bar_template.name]
