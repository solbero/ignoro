import pathlib

import pytest
import requests

import ignoro
from tests.conftest import assert_in_string


class TestTemplate:
    def test_template_str(self, mock_template_go: str):
        template_name = "go"
        # remove template name header
        template_content = "\n".join(mock_template_go.splitlines()[1:])
        template = ignoro.Template(template_name, template_content)

        assert str(template) == f"### {template_name.upper()} ###\n{template_content}\n"

    def test_template_from_remote(self, mock_template_go: str):
        template_name = "go"
        # remove template name header
        template_content = "\n".join(mock_template_go.splitlines()[1:])

        template = ignoro.Template(template_name)

        assert template.name == template_name
        assert template.content == template_content

    def test_template_from_remote_does_not_exist(self):
        template_name = "foobar"

        template = ignoro.Template(template_name)

        assert template.name == template_name
        with pytest.raises(requests.exceptions.HTTPError):
            template.content

    def test_template_from_local(self, mock_template_go: str):
        template_name = "go"
        template_content = "\n".join(mock_template_go.splitlines()[1:])  # remove template header

        template = ignoro.Template(template_name, template_content)

        assert template.name == template_name
        assert template.content == template_content

    def test_template_parse(self, mock_template_go: str):
        template_name = "go"
        template_content = "\n".join(mock_template_go.splitlines()[1:])  # remove template header

        template = ignoro.Template.parse(mock_template_go)

        assert template.name == template_name
        assert template.content == template_content

    def test_template_error_parse_empty(self):
        with pytest.raises(ignoro.ParseError) as excinfo:
            ignoro.Template.parse("")

        assert_in_string(("missing header",), str(excinfo.value))

    def test_template_error_parse_missing_header(self, mock_template_go: str):
        template = "\n".join(mock_template_go.splitlines()[1:])  # remove template name header

        with pytest.raises(ignoro.ParseError) as excinfo:
            ignoro.Template.parse(template)

        assert_in_string(("missing header",), str(excinfo.value))

    def test_template_error_parse_multiple_headers(self, mock_template_go: str):
        with pytest.raises(ignoro.ParseError) as excinfo:
            ignoro.Template.parse(mock_template_go + "\n" + mock_template_go)

        assert_in_string(("multiple headers",), str(excinfo.value))

    def test_template_error_parse_missing_content(self):
        template = "### go ###\n"

        with pytest.raises(ignoro.ParseError) as excinfo:
            ignoro.Template.parse(template)

        assert_in_string(("missing content",), str(excinfo.value))


class TestTemplateList:
    def test_template_list(
        self,
        template_list_populated: ignoro.TemplateList,
        mock_template_list_names: list[str],
    ):
        template_list_names = [template.name for template in template_list_populated]

        assert template_list_names == mock_template_list_names

    def test_template_list_str(
        self,
        mock_template_go: str,
        mock_template_ruby: str,
    ):
        template_go = ignoro.Template.parse(mock_template_go)
        template_ruby = ignoro.Template.parse(mock_template_ruby)

        template_list = ignoro.TemplateList([ignoro.Template("go"), ignoro.Template("ruby")])

        assert str(template_list) == f"{template_go}\n{template_ruby}"

    def test_template_list_contains(
        self,
        template_list_populated: ignoro.TemplateList,
    ):
        results = [template.name for template in template_list_populated.contains("ja")]

        assert results == ["django", "java", "javascript"]

    def test_templates_list_contains_no_result(
        self,
        template_list_populated: ignoro.TemplateList,
    ):
        result = template_list_populated.contains("foobar")

        assert len(result) == 0

    def test_template_list_startswith(
        self,
        template_list_populated: ignoro.TemplateList,
    ):
        result = [template.name for template in template_list_populated.startswith("ja")]

        assert result == ["java", "javascript"]

    def test_template_list_startswith_no_result(
        self,
        template_list_populated: ignoro.TemplateList,
    ):
        result = [template.name for template in template_list_populated.startswith("foobar")]

        assert len(result) == 0

    def test_template_list_exact_match(
        self,
        template_list_populated: ignoro.TemplateList,
        mock_template_go: str,
    ):
        name = "go"
        # remove response header and footer and template name header
        content = "\n".join(mock_template_go.splitlines()[1:])

        result = template_list_populated.exactly_matches([name])

        assert len(result) == 1
        assert result[0].name == name
        assert result[0].content == content

    def test_template_list_exact_match_no_result(
        self,
        template_list_populated: ignoro.TemplateList,
    ):
        result = template_list_populated.exactly_matches(["foobar"])

        assert len(result) == 0

    def test_template_list_parse(
        self,
        mock_template_go: str,
        mock_template_ruby: str,
    ):
        text = mock_template_go + "\n" + mock_template_ruby + "\n"

        templates = ignoro.TemplateList.parse(text)

        assert len(templates) == 2
        assert templates[0].name.lower() == "go"
        assert templates[0].content == "\n".join(mock_template_go.splitlines()[1:])
        assert templates[1].name.lower() == "ruby"
        assert templates[1].content == "\n".join(mock_template_ruby.splitlines()[1:])

    def test_templates_parse_malformed(
        self,
        mock_template_go: str,
    ):
        text = "\n".join(mock_template_go.splitlines()[4:-1])

        with pytest.raises(ignoro.ParseError) as excinfo:
            ignoro.TemplateList.parse(text)

        assert_in_string(("missing template header",), str(excinfo.value))

    def test_template_list_replace_all(
        self,
        mock_template_go: str,
    ):
        template_orig = ignoro.Template.parse(mock_template_go)
        template_new = ignoro.Template.parse(mock_template_go)
        template_new.content = "foobar"
        templates = ignoro.TemplateList([template_orig])

        templates.replace_all([template_new])

        assert len(templates) == 1
        assert ignoro.Template("go") in templates
        assert templates[0].content == "foobar"

    def test_template_list_extend(
        self,
        mock_template_go: str,
        mock_template_ruby: str,
    ):
        templates = ignoro.TemplateList.parse(mock_template_go)
        templates.extend(ignoro.TemplateList.parse(mock_template_ruby))

        assert len(templates) == 2
        assert ignoro.Template("go") in templates
        assert ignoro.Template("ruby") in templates


class TestGitignore:
    def test_gitignore_write_and_read_string(
        self,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go"), ignoro.Template("ruby")])
        gitignore_write = ignoro.Gitignore(template_list)

        output = gitignore_write.dumps()
        gitignore_read = ignoro.Gitignore.loads(output)

        assert len(gitignore_read.template_list) == 2
        assert gitignore_write == gitignore_read

    def test_gitignore_write_and_read_file(
        self,
        tmp_path: pathlib.Path,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go"), ignoro.Template("ruby")])
        gitignore_write = ignoro.Gitignore(template_list)

        gitignore_write.dump(tmp_path / ".gitignore")
        gitignore_read = ignoro.Gitignore.load(tmp_path / ".gitignore")

        assert len(gitignore_read.template_list) == 2
        assert gitignore_write == gitignore_read
