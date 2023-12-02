import pathlib

import pytest
import requests
import requests_mock

import ignoro
from tests.conftest import MockErrors, TemplateMock, assert_in_string


class TestTemplate:
    def test_template_from_local(self, foo_template_mock: TemplateMock):
        template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)

        assert template.name == foo_template_mock.name
        assert template.body == foo_template_mock.body

    def test_template_from_remote(self, foo_template_mock: TemplateMock):
        template = ignoro.Template(foo_template_mock.name)

        assert template.name == foo_template_mock.name
        assert template.body == foo_template_mock.body

    def test_template_string(self, foo_template_mock: TemplateMock, bar_template_mock: TemplateMock):
        template1 = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template2 = ignoro.Template(bar_template_mock.name)

        assert str(template1) == foo_template_mock.content
        assert str(template2) == bar_template_mock.content

    @pytest.mark.parametrize(
        ("error", "fragments"),
        [
            (MockErrors.NOT_FOUND, ["failed", "fetch"]),
            (MockErrors.CONNECTION, ["failed", "connect"]),
            (MockErrors.TIMEOUT, ["connection", "timed", "out"]),
        ],
    )
    def test_template_error_from_remote(self, error: MockErrors, fragments: list[str]):
        template = ignoro.Template(error)

        with pytest.raises(ignoro.exceptions.ApiError) as excinfo:
            template.body

        assert_in_string(fragments, str(excinfo.value))

    def test_template_parse(self, foo_template_mock: TemplateMock):
        template = ignoro.Template.parse(foo_template_mock.content)

        assert template.name == foo_template_mock.name
        assert template.body == foo_template_mock.body

    def test_template_error_parse_empty(self):
        with pytest.raises(ignoro.exceptions.ParseError) as excinfo:
            ignoro.Template.parse("")

        assert_in_string(["missing", "header"], str(excinfo.value))

    def test_template_error_parse_missing_header(self, foo_template_mock: TemplateMock):
        with pytest.raises(ignoro.exceptions.ParseError) as excinfo:
            ignoro.Template.parse(foo_template_mock.body)

        assert_in_string(["missing", "header"], str(excinfo.value))

    def test_template_error_parse_multiple_headers(
        self, foo_template_mock: TemplateMock, bar_template_mock: TemplateMock
    ):
        with pytest.raises(ignoro.exceptions.ParseError) as excinfo:
            ignoro.Template.parse(foo_template_mock.content + "\n" + bar_template_mock.content)

        assert_in_string(["multiple", "headers"], str(excinfo.value))

    def test_template_error_parse_missing_body(self, foo_template_mock: TemplateMock):
        with pytest.raises(ignoro.exceptions.ParseError) as excinfo:
            ignoro.Template.parse(foo_template_mock.header)

        assert_in_string(["missing", "body", foo_template_mock.name], str(excinfo.value))

    def test_template_set_body(self, foo_template_mock: TemplateMock, bar_template_mock: TemplateMock):
        template = ignoro.Template(foo_template_mock.name)
        template.body = bar_template_mock.body

        assert template.name == foo_template_mock.name
        assert template.body == bar_template_mock.body

    def test_template_equal(self, foo_template_mock: TemplateMock):
        template1 = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template2 = ignoro.Template(foo_template_mock.name, foo_template_mock.body)

        assert template1 == template2

    def test_template_not_equal(self, foo_template_mock: TemplateMock, bar_template_mock: TemplateMock):
        template1 = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template2 = ignoro.Template(bar_template_mock.name, bar_template_mock.body)

        assert template1 != template2


class TestTemplateList:
    def test_template_list_populate(
        self,
    ):
        template_list1 = ignoro.TemplateList()
        template_list1.populate()
        template_list2 = ignoro.TemplateList(populate=True)

        assert template_list1 == template_list2

    def test_template_list_remote(
        self,
        template_list: ignoro.TemplateList,
        template_list_names_mock: list[str],
    ):
        template_list.populate()
        template_list_names = [template.name for template in template_list]

        assert template_list_names == template_list_names_mock

    def test_template_list_local(
        self,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_template, bar_template])
        template_list_names = [template.name for template in template_list]

        assert template_list_names == [foo_template_mock.name, bar_template_mock.name]

    def test_template_list_contains(
        self,
        template_list: ignoro.TemplateList,
    ):
        template_list.populate()
        results = [template.name for template in template_list.contains("do")]

        assert results == ["dotdot", "double-dash"]

    def test_template_list_contains_no_result(
        self,
        template_list: ignoro.TemplateList,
    ):
        template_list.populate()
        result = template_list.contains("fizzbuzz")

        assert len(result) == 0

    def test_template_list_startswith(
        self,
        template_list: ignoro.TemplateList,
    ):
        template_list.populate()
        result = [template.name for template in template_list.startswith("do")]

        assert result == ["dotdot", "double-dash"]

    def test_template_list_startswith_no_result(
        self,
        template_list: ignoro.TemplateList,
    ):
        template_list.populate()
        result = [template.name for template in template_list.startswith("fizzbuzz")]

        assert len(result) == 0

    def test_template_list_match(
        self,
        template_list: ignoro.TemplateList,
    ):
        template_list.populate()
        result = template_list.match("foo")

        assert result is not None
        assert result.name == "foo"

    def test_template_list_exact_match_no_result(
        self,
        template_list: ignoro.TemplateList,
    ):
        template_list.populate()
        result = template_list.match("fizzbuzz")

        assert result is None

    def test_template_list_findall(
        self,
        template_list: ignoro.TemplateList,
    ):
        template_list.populate()
        result = template_list.findall(["foo", "bar"])

        assert len(result) == 2
        assert result[0].name == "foo"
        assert result[1].name == "bar"

    def test_template_list_findall_no_result(
        self,
        template_list: ignoro.TemplateList,
    ):
        template_list.populate()
        result = template_list.findall(["fizz", "buzz"])

        assert len(result) == 0

    def test_template_list_parse(
        self,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        text = f"{foo_template_mock.content}\n{bar_template_mock.content}\n"
        template_list = ignoro.TemplateList.parse(text)

        assert len(template_list) == 2
        assert template_list[0].name == foo_template_mock.name
        assert template_list[0].body == foo_template_mock.body
        assert template_list[1].name == bar_template_mock.name
        assert template_list[1].body == bar_template_mock.body

    def test_template_list_parse_error_no_headers(
        self,
        foo_template_mock: TemplateMock,
    ):
        with pytest.raises(ignoro.exceptions.ParseError) as excinfo:
            ignoro.TemplateList.parse(foo_template_mock.body)

        assert_in_string(["missing", "template", "header"], str(excinfo.value))

    def test_template_list_replace(
        self,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        foo_template_new_body = ignoro.Template(foo_template_mock.name, bar_template_mock.body)

        templates = ignoro.TemplateList([foo_template])
        templates.replace(foo_template_new_body)

        assert len(templates) == 1
        assert templates[0].name == foo_template_mock.name
        assert templates[0].body == bar_template_mock.body

    def test_template_list_extend(
        self,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        templates = ignoro.TemplateList([foo_template])
        templates.extend(ignoro.TemplateList([bar_template]))

        assert len(templates) == 2
        assert templates[0] == foo_template
        assert templates[1] == bar_template

    @pytest.mark.parametrize(
        ("error", "fragments"),
        [
            (requests.exceptions.ConnectionError, ["failed", "connect"]),
            (requests.exceptions.Timeout, ["connection", "timed", "out"]),
        ],
    )
    def test_template_list_populate_error_remote(
        self,
        requests_mock: requests_mock.Mocker,
        error: requests.exceptions.RequestException,
        fragments: list[str],
    ):
        requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", exc=error)

        with pytest.raises(ignoro.exceptions.ApiError) as excinfo:
            ignoro.TemplateList().populate()

        assert_in_string(fragments, str(excinfo.value))

    def test_template_list_populate_error_not_found(
        self,
        requests_mock: requests_mock.Mocker,
    ):
        requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", status_code=404)

        with pytest.raises(ignoro.exceptions.ApiError) as excinfo:
            ignoro.TemplateList().populate()

        assert_in_string(["failed", "fetch"], str(excinfo.value))

    def test_template_list_sort(
        self,
        template_list: ignoro.TemplateList,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_template, bar_template])

        template_list.sort()

        assert template_list == [bar_template, foo_template]

    def test_template_list_insert(
        self,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_template])

        template_list.insert(0, bar_template)

        assert template_list == [bar_template, foo_template]

    def test_template_list_set(
        self,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_template])

        template_list[0] = bar_template

        assert template_list == [bar_template]

    def test_template_list_del(
        self,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([bar_template, foo_template])

        del template_list[0]

        assert template_list == [foo_template]

    def test_template_list_in(
        self,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList([foo_template])

        assert foo_template in template_list
        assert bar_template not in template_list

    def test_template_list_equal(
        self,
        foo_template_mock: TemplateMock,
    ):
        template1 = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list1 = ignoro.TemplateList([template1])
        template2 = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list2 = ignoro.TemplateList([template2])

        assert template_list1 == template_list2

    def test_template_list_not_equal(
        self,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        template1 = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list1 = ignoro.TemplateList([template1])
        template2 = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list2 = ignoro.TemplateList([template2])

        assert template_list1 != template_list2


class TestGitignore:
    def test_gitignore_write_and_read_string(
        self,
        template_list: ignoro.TemplateList,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList((foo_template, bar_template))

        writer = ignoro.Gitignore(template_list)
        output = writer.dumps()
        reader = ignoro.Gitignore.loads(output)

        assert len(reader) == 2
        assert writer == reader

    def test_gitignore_write_and_read_file(
        self,
        tmp_path: pathlib.Path,
        template_list: ignoro.TemplateList,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        foo_template = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        bar_template = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list = ignoro.TemplateList((foo_template, bar_template))

        path = tmp_path / ".gitignore"
        writer = ignoro.Gitignore(template_list)
        writer.dump(path)
        reader = ignoro.Gitignore.load(path)

        assert len(reader) == 2
        assert writer == reader

    def test_gitignore_write_and_read_empty_file(
        self,
        tmp_path: pathlib.Path,
    ):
        path = tmp_path / ".gitignore"
        writer = ignoro.Gitignore()
        writer.dump(path)
        reader = ignoro.Gitignore.load(path)

        assert len(reader) == 0
        assert writer == reader

    def test_gitignore_error_read_path_is_dir(
        self,
        tmp_path: pathlib.Path,
    ):
        with pytest.raises(IsADirectoryError):
            ignoro.Gitignore.load(tmp_path)

    def test_gitignore_error_read_file_not_exists(
        self,
        tmp_path: pathlib.Path,
    ):
        path = tmp_path / ".gitignore"

        with pytest.raises(FileNotFoundError):
            ignoro.Gitignore.load(path)

    def test_gitignore_error_read_parse_error(
        self,
        tmp_path: pathlib.Path,
        foo_template_mock: TemplateMock,
    ):
        path = tmp_path / ".gitignore"
        path.write_text(foo_template_mock.header)

        with pytest.raises(ignoro.exceptions.ParseError):
            ignoro.Gitignore.load(path)

    def test_gitignore_error_read_permission_denied(
        self,
        tmp_path: pathlib.Path,
    ):
        path = tmp_path / ".gitignore"
        path.touch()
        path.chmod(0o000)

        with pytest.raises(PermissionError):
            ignoro.Gitignore.load(path)
        path.chmod(0o755)

    def test_gitignore_error_write_path_is_dir(
        self,
        tmp_path: pathlib.Path,
        template_list: ignoro.TemplateList,
    ):
        with pytest.raises(IsADirectoryError):
            ignoro.Gitignore(template_list).dump(tmp_path)

    def test_gitignore_error_write_permission_denied(
        self,
        tmp_path: pathlib.Path,
        template_list: ignoro.TemplateList,
    ):
        path = tmp_path / ".gitignore"
        path.touch()
        path.chmod(0o000)

        with pytest.raises(PermissionError):
            ignoro.Gitignore(template_list).dump(path)
        path.chmod(0o755)

    def test_gitignore_equal(
        self,
        foo_template_mock: TemplateMock,
    ):
        template1 = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list1 = ignoro.TemplateList([template1])
        gitignore1 = ignoro.Gitignore(template_list1)

        template2 = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list2 = ignoro.TemplateList([template2])
        gitignore2 = ignoro.Gitignore(template_list2)

        assert gitignore1 == gitignore2

    def test_gitignore_not_equal(
        self,
        foo_template_mock: TemplateMock,
        bar_template_mock: TemplateMock,
    ):
        template1 = ignoro.Template(foo_template_mock.name, foo_template_mock.body)
        template_list1 = ignoro.TemplateList([template1])
        gitignore1 = ignoro.Gitignore(template_list1)

        template2 = ignoro.Template(bar_template_mock.name, bar_template_mock.body)
        template_list2 = ignoro.TemplateList([template2])
        gitignore2 = ignoro.Gitignore(template_list2)

        assert gitignore1 != gitignore2
