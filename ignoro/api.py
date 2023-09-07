from __future__ import annotations

import collections
import collections.abc
import os
import pathlib

import requests
from typing_extensions import Callable, Iterable, Iterator, Optional

import ignoro

__all__ = ["Template", "TemplateList", "Gitignore"]


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

    def __str__(self) -> str:
        return f"### {self.name.upper()} ###\n{self.content}\n"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name}, {self.content[:9]}...)"

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

    @staticmethod
    def _strip(text: str) -> str:
        lines = text.splitlines()
        return "\n".join(lines[4:-1])


class TemplateList(collections.abc.MutableSequence[Template]):
    """A list of gitignore templates from gitignore.io."""

    def __init__(self, templates: Optional[Iterable[Template]] = None, *, populate: bool = False) -> None:
        """Initialize a list of templates from user provided templates and/or gitignore.io."""
        self.data: list[Template] = []

        if isinstance(templates, list):
            self.data = templates
        elif isinstance(templates, TemplateList):
            self.data = templates.data
        elif isinstance(templates, Iterable):
            self.data = list(templates)

        if populate:
            self.populate()

    def __str__(self) -> str:
        return "".join(str(template) for template in self.data)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.data!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TemplateList):
            return self.data == other.data
        return False

    def __getitem__(self, index: int) -> Template:
        return self.data[index]

    def __setitem__(self, index: int, template: Template) -> None:
        self.data[index] = template

    def __delitem__(self, index: int) -> None:
        del self.data[index]

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator[Template]:
        return iter(self.data)

    def __contains__(self, item: object) -> bool:
        return item in self.data

    def insert(self, index: int, value: Template) -> None:
        """Insert a template into the list."""
        self.data.insert(index, value)

    def sort(self, key: Optional[Callable] = None, reverse: bool = False) -> None:
        """Sort the list of templates."""
        self.data.sort(key=key, reverse=reverse)

    def append(self, template: Template) -> None:
        """Add a template to the list if it does not already exist."""
        if template in self.data:
            index = self.data.index(template)
            if self.data[index].content != template.content:
                self.data[index].content = template.content
            else:
                return None
        self.data.append(template)

    def extend(self, templates: Iterable[Template]) -> None:
        """Add multiple templates to the list."""
        for template in templates:
            self.append(template)

    def contains(self, term: str) -> TemplateList:
        """Returns gitignore.io templates where template name contains term."""
        term = term.lower()
        return TemplateList(template for template in self.data if term in template.name)

    def startswith(self, term: str) -> TemplateList:
        """Returns gitignore.io templates where template name starts with term."""
        term = term.lower()
        return TemplateList(template for template in self.data if template.name.startswith(term))

    def exactly_matches(self, terms: Iterable[str]) -> TemplateList:
        """Returns gitignore.io templates available combining search terms."""
        terms = [term.lower() for term in terms]
        return TemplateList(template for template in self.data if template.name in terms)

    def populate(self) -> None:
        url = f"{ignoro.BASE_URL}/list"
        params = {"format": "lines"}
        response = requests.get(url, params)
        response.raise_for_status()
        self.data.extend(Template(name) for name in response.text.splitlines())

    @staticmethod
    def parse(text: str) -> TemplateList:
        """Parse templates from a string."""

        def is_header(line: str) -> bool:
            return line.startswith("### ") and line.endswith(" ###")

        templates = TemplateList()
        outer_index = 0
        while outer_index < len(lines := text.splitlines()):
            if is_header(lines[outer_index]):
                inner_index = outer_index + 1

                while inner_index < len(lines) and not is_header(lines[inner_index]):
                    inner_index += 1

                name = lines[outer_index][4:-4]
                content = "\n".join(lines[outer_index + 1 : inner_index])
                templates.append(Template(name, content))
                outer_index = inner_index

            else:
                outer_index += 1

        return templates


class Gitignore:
    _header: str = (
        "# Created by https://github.com/solbero/ignoro\n" + "# TEXT BELOW THIS LINE WAS AUTOMATICALLY GENERATED\n"
    )
    _footer: str = "# TEXT ABOVE THIS LINE WAS AUTOMATICALLY GENERATED\n"

    def __init__(self, template_list: Optional[ignoro.TemplateList]) -> None:
        self.template_list = template_list or ignoro.TemplateList()

    def __str__(self) -> str:
        return f"{self._header}\n{str(self.template_list)}{self._footer}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.template_list!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Gitignore):
            return self.template_list == other.template_list
        return False

    def dumps(self) -> str:
        return str(self)

    def dump(self, path: pathlib.Path) -> None:
        path.write_text(str(self))

    @classmethod
    def loads(cls, text: str) -> Gitignore:
        lines = text.splitlines()
        start = lines.index(cls._header.splitlines()[0])
        end = lines.index(cls._footer.splitlines()[0])
        text = "\n".join(lines[start + 2 : end])
        return Gitignore(TemplateList.parse(text))

    @staticmethod
    def load(path: pathlib.Path | os.PathLike) -> Gitignore:
        with open(path, "r") as file:
            return Gitignore.loads(file.read())
