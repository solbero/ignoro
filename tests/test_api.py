import requests_mock

import ignoro.api as api


def test_list(requests_mock: requests_mock.Mocker, templates: api.TemplateList, template_names: list[str]):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    template_names = [template.name for template in templates.all]
    assert template_names == template_names


def test_contains(requests_mock: requests_mock.Mocker, templates: api.TemplateList, template_names: list[str]):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    result = templates.name_contains("ja")
    template_names = [template.name for template in result]
    assert template_names == ["django", "java", "javascript"]


def test_contains_no_result(
    requests_mock: requests_mock.Mocker, templates: api.TemplateList, template_names: list[str]
):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    result = templates.name_contains("foobar")
    assert len(result) == 0


def test_startswith(requests_mock: requests_mock.Mocker, templates: api.TemplateList, template_names: list[str]):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    result = [template.name for template in templates.name_startswith("ja")]
    assert result == ["java", "javascript"]


def test_startswith_no_result(
    requests_mock: requests_mock.Mocker, templates: api.TemplateList, template_names: list[str]
):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    result = [template.name for template in templates.name_startswith("foobar")]
    assert len(result) == 0


def test_matches_and_content(
    requests_mock: requests_mock.Mocker,
    templates: api.TemplateList,
    template_names: list[str],
    template_content: str,
):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    requests_mock.get(f"{api.Template._api}/go", text=template_content)
    result = templates.name_exactly_matches(["go"])
    assert len(result) == 1
    assert result[0].name == "go"
    assert result[0].content in template_content


def test_matches_no_result(requests_mock: requests_mock.Mocker, templates: api.TemplateList, template_names: list[str]):
    requests_mock.get(api.TemplateList._api, text="\n".join(template_names))
    result = templates.name_exactly_matches(["foobar"])
    assert len(result) == 0
