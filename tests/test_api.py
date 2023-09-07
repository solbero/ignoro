import pathlib

import ignoro


class TestTemplate:
    def test_template_content_from_remote(self, mock_template_go: str):
        template_name = "go"
        # remove response header and footer and template name header
        template_content = "\n".join(mock_template_go.splitlines()[4:-1])

        template = ignoro.Template(template_name)

        assert template.name == template_name
        assert template.content == template_content
        assert str(template) == f"### {template_name.upper()} ###\n{template_content}\n"

    def test_template_content_from_local(self, mock_template_go: str):
        template_name = "go"
        # remove response header and footer and template name header
        template_content = "\n".join(mock_template_go.splitlines()[4:-1])
        template = ignoro.Template(template_name, template_content)

        assert template.name == template_name
        assert template.content == template_content
        assert str(template) == f"### {template_name.upper()} ###\n{template_content}\n"


class TestTemplateList:
    def test_template_list(
        self,
        template_list_populated: ignoro.TemplateList,
        mock_template_list_names: list[str],
    ):
        template_list_names = [template.name for template in template_list_populated]

        assert template_list_names == mock_template_list_names

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
        content = "\n".join(mock_template_go.splitlines()[4:-1])

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
        # remove response header and footer
        template_go = "\n".join(mock_template_go.splitlines()[3:-1])
        template_ruby = "\n".join(mock_template_ruby.splitlines()[3:-1])
        text = template_go + "\n" + template_ruby + "\n"

        templates = ignoro.TemplateList.parse(text)

        assert len(templates) == 2
        assert templates[0].name.lower() == "go"
        assert templates[0].content == "\n".join(mock_template_go.splitlines()[4:-1])
        assert templates[1].name.lower() == "ruby"
        assert templates[1].content == "\n".join(mock_template_ruby.splitlines()[4:-1])

    def test_templates_parse_malformed(
        self,
        mock_template_go: str,
    ):
        # remove response header and footer and template name header
        text = "\n".join(mock_template_go.splitlines()[4:-1])

        templates = ignoro.TemplateList.parse(text)

        assert len(templates) == 0


class TestGitignore:
    def test_gitignore_write_and_read_string(
        self,
        tmp_path: pathlib.Path,
    ):
        template_list = ignoro.TemplateList([ignoro.Template("go"), ignoro.Template("ruby")])
        gitignore_write = ignoro.Gitignore(template_list)

        gitignore_write.dump(tmp_path / ".gitignore")
        gitignore_read = ignoro.Gitignore.load(tmp_path / ".gitignore")

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
