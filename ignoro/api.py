from __future__ import annotations

import collections
import collections.abc

import requests
from typing_extensions import Callable, Iterable, Iterator, Optional

import ignoro


class Template:
    """A gitignore template from gitignore.io."""

    def __init__(self, name: str, content: Optional[str] = None) -> None:
        self.name = name.lower()
        self._content = content

    @property
    def content(self) -> str:
        if self._content is None:
            url = f"{ignoro.BASE_URL}/{self.name}"
            response = requests.get(url)
            response.raise_for_status()
            self._content = self._strip(response.text)
        return self._content

    @content.setter
    def content(self, text: str) -> None:
        self._content = text

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Template):
            return self.name == other.name
        return False

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.name)

    def __lt__(self, other: Template) -> bool:
        return self.name < other.name

    def __le__(self, other: Template) -> bool:
        return self.name <= other.name

    def __gt__(self, other: Template) -> bool:
        return self.name > other.name

    def __ge__(self, other: Template) -> bool:
        return self.name >= other.name

    def __str__(self) -> str:
        return f"### {self.name.upper()} ###\n{self.content}\n"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name}, {self.content})"

    @staticmethod
    def _strip(text: str) -> str:
        lines = text.splitlines()
        return "\n".join(lines[4:-1])


class Templates(collections.abc.MutableSequence[Template]):
    """A list of gitignore templates from gitignore.io."""

    def __init__(self, templates: Optional[Iterable[Template]] = None, *, populate: bool = False) -> None:
        """Initialize a list of templates from user provided templates and/or gitignore.io."""
        self._templates: list[Template] = []

        if isinstance(templates, list):
            self._templates = templates
        elif isinstance(templates, Templates):
            self._templates = templates._templates
        elif isinstance(templates, Iterable):
            self._templates = list(templates)

        if populate:
            self.populate()

    def __getitem__(self, index: int) -> Template:
        return self._templates[index]

    def __setitem__(self, index: int, template: Template) -> None:
        self._templates[index] = template

    def __delitem__(self, index: int) -> None:
        del self._templates[index]

    def __len__(self) -> int:
        return len(self._templates)

    def __iter__(self) -> Iterator[Template]:
        return iter(self._templates)

    def __contains__(self, item: object) -> bool:
        return item in self._templates

    def insert(self, index: int, value: Template) -> None:
        """Insert a template into the list."""
        self._templates.insert(index, value)

    def sort(self, key: Optional[Callable] = None, reverse: bool = False) -> None:
        """Sort the list of templates."""
        self._templates.sort(key=key, reverse=reverse)

    def append(self, template: Template) -> None:
        """Add a template to the list if it does not already exist."""
        if template in self._templates:
            index = self._templates.index(template)
            if self._templates[index].content != template.content:
                self._templates[index].content = template.content
            else:
                return None
        self._templates.append(template)

    def extend(self, templates: Iterable[Template]) -> None:
        """Add multiple templates to the list."""
        for template in templates:
            self.append(template)

    def contains(self, term: str) -> Templates:
        """Returns gitignore.io templates where template name contains term."""
        term = term.lower()
        return Templates(template for template in self._templates if term in template.name)

    def startswith(self, term: str) -> Templates:
        """Returns gitignore.io templates where template name starts with term."""
        term = term.lower()
        return Templates(template for template in self._templates if template.name.startswith(term))

    def exactly_matches(self, terms: Iterable[str]) -> Templates:
        """Returns gitignore.io templates available combining search terms."""
        terms = [term.lower() for term in terms]
        return Templates(template for template in self._templates if template.name in terms)

    def populate(self) -> None:
        url = f"{ignoro.BASE_URL}/list"
        params = {"format": "lines"}
        response = requests.get(url, params)
        response.raise_for_status()
        self._templates.extend(Template(name) for name in response.text.splitlines())
