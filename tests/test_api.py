import requests_mock

import ignoro


def test_template_content_remote(requests_mock: requests_mock.Mocker, mock_template_go: str):
    requests_mock.get(f"{ignoro.BASE_URL}/go", text=mock_template_go)
    name = "go"
    content = "\n".join(mock_template_go.splitlines()[4:-1])
    template = ignoro.api.Template(name)
    assert template.name == name
    assert template.content == content
    assert str(template) == f"### {name.upper()} ###\n{content}\n"


def test_template_content_local_gitignore_header(mock_template_go: str):
    name = "go"
    content = "\n".join(mock_template_go.splitlines()[5:-1])
    template = ignoro.api.Template(name, content)
    assert template.name == name
    assert template.content == content
    assert str(template) == f"### {name.upper()} ###\n{content}\n"


def test_templates_list(
    requests_mock: requests_mock.Mocker, templates: ignoro.api.Templates, mock_template_names: list[str]
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    templates.populate()
    template_names = [template.name for template in templates]
    assert template_names == mock_template_names


def test_tamplates_contains(
    requests_mock: requests_mock.Mocker, templates: ignoro.api.Templates, mock_template_names: list[str]
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    templates.populate()
    results = [template.name for template in templates.contains("ja")]
    assert results == ["django", "java", "javascript"]


def test_tamplates_contains_no_result(
    requests_mock: requests_mock.Mocker, templates: ignoro.api.Templates, mock_template_names: list[str]
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    templates.populate()
    result = templates.contains("foobar")
    assert len(result) == 0


def test_tamplates_startswith(
    requests_mock: requests_mock.Mocker, templates: ignoro.api.Templates, mock_template_names: list[str]
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    templates.populate()
    result = [template.name for template in templates.startswith("ja")]
    assert result == ["java", "javascript"]


def test_tamplates_startswith_no_result(
    requests_mock: requests_mock.Mocker, templates: ignoro.api.Templates, mock_template_names: list[str]
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    templates.populate()
    result = [template.name for template in templates.startswith("foobar")]
    assert len(result) == 0


def test_tamplates_matches_and_content(
    requests_mock: requests_mock.Mocker,
    templates: ignoro.api.Templates,
    mock_template_names: list[str],
    mock_template_go: str,
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    requests_mock.get(f"{ignoro.BASE_URL}/go", text=mock_template_go)
    templates.populate()
    name = "go"
    content = "\n".join(mock_template_go.splitlines()[4:-1])
    result = templates.exactly_matches([name])
    assert len(result) == 1
    assert result[0].name == name
    assert result[0].content == content


def test_tamplates_matches_no_result(
    requests_mock: requests_mock.Mocker, templates: ignoro.api.Templates, mock_template_names: list[str]
):
    requests_mock.get(f"{ignoro.BASE_URL}/list?format=lines", text="\n".join(mock_template_names))
    result = templates.exactly_matches(["foobar"])
    assert len(result) == 0
