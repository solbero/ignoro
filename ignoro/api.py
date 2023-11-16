from __future__ import annotations

import collections
import collections.abc
import pathlib
import re
from typing import SupportsIndex

import requests
from typing_extensions import Callable, Iterable, Iterator, Optional

import ignoro

__all__ = ["Template", "TemplateList", "Gitignore"]


class _FindMetadataMixin:
    """Mixin class to find the headers of a gitignore file."""

    @staticmethod
    def _find_metadata(lines: list[str], pattern: re.Pattern[str]) -> list[tuple[int, str]]:
        """Find the headers in a list of lines. Returns a list of tuples containing the index and name of the header."""

        results = []
        for index, line in enumerate(lines):
            if match := pattern.match(line):
                name = match.group(1)
                results.append((index, name))

        return results


class Template(_FindMetadataMixin):
    """A gitignore template from gitignore.io."""

    def __init__(self, name: str, body: Optional[str] = None) -> None:
        self.name = name.lower()
        self.header = f"### {self.name.capitalize()} ###"
        self._body = body

    @property
    def body(self) -> str:
        if self._body is None:
            url = f"{ignoro.BASE_URL}/{self.name.lower()}"

            try:
                response = requests.get(url)
            except requests.exceptions.ConnectionError as err:
                raise ignoro.exceptions.ApiError(f"Failed to connect to '{url}'") from err
            except requests.exceptions.Timeout as err:
                raise ignoro.exceptions.ApiError(f"Connection to '{url}' timed out") from err

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                raise ignoro.exceptions.ApiError(f"Failed to fetch '{url}' because {err.response.reason}") from err

            template = Template._strip(response.text)
            self._body = template.body

        return self._body

    @body.setter
    def body(self, value: str) -> None:
        self._body = value

    def __str__(self) -> str:
        return f"{self.header}\n{self.body}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name}, {self.body[:15]}...)"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Template):
            return self.name.lower() == other.name.lower()
        return False

    def __ne__(self, other: object) -> bool:
        return self != other

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
    def parse(content: str) -> Template:
        """Parse a template from a string."""
        lines = content.splitlines()
        pattern = re.compile(r"^### (\S+) ###$")
        headers = Template._find_metadata(lines, pattern)

        if len(headers) == 0:
            raise ignoro.exceptions.ParseError("Missing header")
        elif len(headers) > 1:
            raise ignoro.exceptions.ParseError("Multiple headers")

        line_no, name = headers[0]
        content = "\n".join(lines[line_no + 1 :])

        if not content:
            raise ignoro.exceptions.ParseError("Missing body")

        return Template(name, content)

    @staticmethod
    def _strip(response: str) -> Template:
        lines = response.splitlines()
        text = "\n".join(lines[3:-1])
        return Template.parse(text)


class TemplateList(collections.abc.MutableSequence[Template], _FindMetadataMixin):
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
        return "\n".join(str(template) for template in self.data)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.data!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TemplateList):
            return self.data == other.data
        return False

    def __ne__(self, other: object) -> bool:
        return self != other

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

    def insert(self, index: SupportsIndex, value: Template) -> None:
        """Insert a template into the list."""
        self.data.insert(index, value)

    def sort(self, key: Optional[Callable] = None, reverse: bool = False) -> None:
        """Sort the list of templates."""
        self.data.sort(key=key, reverse=reverse)

    def append(self, template: Template) -> None:
        """Append a template to the list."""
        self.data.append(template)

    def extend(self, templates: Iterable[Template]) -> None:
        """Add multiple templates to the list."""
        for template in templates:
            self.append(template)

    def replace(self, template: Template) -> None:
        """Replace a template in the list if it exists, otherwise add it."""
        if template in self.data:
            index = self.data.index(template)
            self.data[index] = template
        else:
            self.data.append(template)

    def contains(self, term: str) -> TemplateList:
        """Returns gitignore.io templates where template name contains term."""
        term = term.lower()
        return TemplateList(template for template in self.data if term in template.name.lower())

    def startswith(self, term: str) -> TemplateList:
        """Returns gitignore.io templates where template name starts with term."""
        term = term.lower()
        return TemplateList(template for template in self.data if template.name.lower().startswith(term))

    def match(self, term: str) -> Template | None:
        """Returns gitignore.io templates available combining search terms."""
        term = term.lower()
        for template in self.data:
            if template.name.lower() == term:
                return template

    def findall(self, terms: Iterable[str]) -> TemplateList:
        """Returns gitignore.io templates available combining search terms."""
        terms = tuple(term.lower() for term in terms)
        return TemplateList(template for term in terms for template in self.data if term == template.name.lower())

    def populate(self) -> None:
        """Populate the list of templates from gitignore.io."""
        url = f"{ignoro.BASE_URL}/list"
        params = {"format": "lines"}

        try:
            response = requests.get(url, params)
        except requests.exceptions.ConnectionError as err:
            raise ignoro.exceptions.ApiError(f"Failed to connect to '{url}'") from err
        except requests.exceptions.Timeout as err:
            raise ignoro.exceptions.ApiError(f"Connection to '{url}' timed out") from err

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise ignoro.exceptions.ApiError(f"Failed to fetch '{url}' because {err.response.reason}") from err

        template_list_names = response.text.splitlines()
        for name in template_list_names:
            self.replace(Template(name))

    @staticmethod
    def parse(text: str) -> TemplateList:
        """Parse templates from a string."""
        lines = text.splitlines()
        pattern = re.compile(r"^### (\S+) ###$")
        headers = TemplateList._find_metadata(lines, pattern)

        if len(headers) == 0:
            raise ignoro.exceptions.ParseError("Missing template headers")

        templates = TemplateList()
        while len(headers) > 0:
            current_header, name = headers.pop(0)
            if len(headers) > 0:
                next_header, _ = headers[0]
                content = "\n".join(lines[current_header + 1 : next_header])
            else:
                content = "\n".join(text.splitlines()[current_header + 1 :])
            templates.append(Template(name, content))

        return templates


class Gitignore(_FindMetadataMixin):
    _header: str = (
        "# Created by https://github.com/solbero/ignoro\n" + "# TEXT BELOW THIS LINE WAS AUTOMATICALLY GENERATED\n"
    )
    _footer: str = "# TEXT ABOVE THIS LINE WAS AUTOMATICALLY GENERATED\n"

    def __init__(self, template_list: Optional[ignoro.TemplateList]) -> None:
        self.template_list = template_list or ignoro.TemplateList()

    def __str__(self) -> str:
        return f"{self._header}\n{str(self.template_list)}\n{self._footer}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.template_list!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Gitignore):
            return self.template_list == other.template_list
        return False

    def dumps(self) -> str:
        return str(self)

    def dump(self, path: pathlib.Path) -> None:
        try:
            if path.is_dir():
                raise IsADirectoryError(f"Path '{path.absolute()}' is a directory")
        except PermissionError as err:
            raise PermissionError(f"Permission denied for '{path.absolute()}'") from err

        try:
            path.write_text(str(self))
        except PermissionError as err:
            raise PermissionError(f"Permission denied for '{path.absolute()}'.") from err

    @classmethod
    def loads(cls, text: str) -> Gitignore:
        lines = text.splitlines()
        pattern = re.compile(r"^(# TEXT BELOW THIS LINE WAS AUTOMATICALLY GENERATED)$")
        headers = Gitignore._find_metadata(text.splitlines(), pattern)

        if len(headers) == 0:
            raise ignoro.exceptions.ParseError("Missing gitignore header")
        elif len(headers) > 1:
            raise ignoro.exceptions.ParseError("Multiple gitignore headers")

        pattern = re.compile(r"^(# TEXT ABOVE THIS LINE WAS AUTOMATICALLY GENERATED$)")
        footers = Gitignore._find_metadata(text.splitlines(), pattern)

        if len(footers) == 0:
            raise ignoro.exceptions.ParseError("Missing gitignore footer")
        elif len(footers) > 1:
            raise ignoro.exceptions.ParseError("Multiple gitignore footers")

        line_no_header, _ = headers[0]
        line_no_footer, _ = footers[0]
        content = "\n".join(lines[line_no_header + 1 : line_no_footer])

        template_list = ignoro.TemplateList.parse(content)
        return Gitignore(template_list)

    @staticmethod
    def load(path: pathlib.Path) -> Gitignore:
        try:
            if path.is_dir():
                raise IsADirectoryError(f"Path '{path.absolute()}' is a directory")
        except PermissionError as err:
            raise PermissionError(f"Permission denied for '{path.absolute()}'.") from err

        try:
            with open(path, "r") as file:
                return Gitignore.loads(file.read())
        except FileNotFoundError as err:
            raise FileNotFoundError(f"File '{path.absolute()}' does not exist") from err
        except PermissionError as err:
            raise PermissionError(f"Permission denied for '{path.absolute()}'") from err
