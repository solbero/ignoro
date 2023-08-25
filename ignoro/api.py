import functools

import requests
from typing_extensions import Iterable


class Template:
    """A gitignore template from gitignore.io."""

    _api = "https://www.toptal.com/developers/gitignore/api"

    def __init__(self, name: str) -> None:
        self.name = name

    @functools.cached_property
    def content(self) -> str:
        """The content of the template."""
        url = f"{self._api}/{self.name}"
        response = requests.get(url)
        response.raise_for_status()
        return self._format(response.text)

    def _format(self, text: str) -> str:
        """Strip gitignore.io header and footer from response."""
        lines = text.splitlines()
        body = lines[3:-2]
        return "\n".join(body)


class TemplateList:
    """A list of gitignore templates from gitignore.io."""

    _api = "https://www.toptal.com/developers/gitignore/api/list?format=lines"

    def __init__(self) -> None:
        ...

    @functools.cached_property
    def all(self) -> list[Template]:
        """List of all templates available from gitignore.io."""
        response = requests.get(self._api)
        response.raise_for_status()
        return [Template(name) for name in response.text.splitlines()]

    def name_contains(self, term: str) -> list[Template]:
        """Returns gitignore.io templates where template name contains term."""
        return [template for template in self.all if term in template.name]

    def name_startswith(self, term: str) -> list[Template]:
        """Returns gitignore.io templates where template name starts with term."""
        return [template for template in self.all if template.name.startswith(term)]

    def name_exactly_matches(self, terms: Iterable[str]) -> list[Template]:
        """Returns gitignore.io templates available combining search terms."""
        return [template for template in self.all if any(term == template.name for term in terms)]

    def _format_response(self, text: str) -> str:
        """Strip gitignore.io header and footer from response."""
        lines = text.splitlines(keepends=True)
        body = lines[3:-2]
        return "".join(body)
