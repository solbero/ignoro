from __future__ import annotations

import collections
import collections.abc
import pathlib
import re
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import NamedTuple, Optional, SupportsIndex

import requests

import ignoro

__all__ = ["Template", "TemplateList", "Gitignore"]


class _MetadataMatch(NamedTuple):
    """A match for a metadata line."""

    index: int
    match: re.Match[str]


class _FindMetadataMixin:
    """Mixin class to find metadata in a .gitignore file."""

    @staticmethod
    def _find_metadata(lines: Iterable[str], pattern: re.Pattern[str]) -> list[_MetadataMatch]:
        """Find metadata in a list of lines. Returns a named tuple containing the index and match object."""
        results = []
        for index, line in enumerate(lines):
            if match := pattern.search(line):
                results.append(_MetadataMatch(index, match))

        return results


class Template(_FindMetadataMixin):
    """A .gitignore template from gitignore.io."""

    def __init__(self, name: str, body: Optional[str] = None) -> None:
        """Initialize a .gitignore template from a name and body."""
        self.name = name.lower()
        self.header = self._create_header(self.name)
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

            self._body = self._extract_body(response.text)

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
            return self.name.casefold() == other.name.casefold()
        return False

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __lt__(self, other: Template) -> bool:
        return self.name < other.name

    def __le__(self, other: Template) -> bool:
        return self.name <= other.name

    def __gt__(self, other: Template) -> bool:
        return self.name > other.name

    def __ge__(self, other: Template) -> bool:
        return self.name >= other.name

    @classmethod
    def parse(cls, content: str) -> Template:
        """Parse a template from an ignoro string."""
        lines = content.strip().splitlines()
        pattern = re.compile(r"^#\s(\S+)\s+#$")
        headers = Template._find_metadata(lines, pattern)

        if len(headers) == 0:
            raise ignoro.exceptions.ParseError("Missing template header")
        elif len(headers) > 1:
            raise ignoro.exceptions.ParseError("Multiple template headers")

        index, name = headers[0].index, headers[0].match.group(1)
        body = cls._strip(lines[index + 2 :])

        if not body:
            raise ignoro.exceptions.ParseError(f"Missing body for '{name}'")

        return cls(name, body)

    @classmethod
    def _extract_body(cls, response: str) -> str:
        """Get the body from a gitignore.io response."""
        lines = response.splitlines()
        return cls._strip(lines[4:-1])

    @staticmethod
    def _strip(lines: Sequence[str]) -> str:
        """Strip leading and trailing whitespace from a list of lines, but preserve final newline."""
        stripped = "\n".join(lines).strip()
        return "".join(f"{line}\n" for line in stripped.splitlines())

    @staticmethod
    def _create_header(name: str, line_width: int = 100) -> str:
        """Create a block header for a template."""
        border = f"#{'-'*(line_width-2)}#"
        middle = f"# {name.upper()}{' '*(line_width-len(name)-3)}#"
        return f"{border}\n{middle}\n{border}\n"


class TemplateList(collections.abc.MutableSequence[Template], _FindMetadataMixin):
    """A list of .gitignore templates from gitignore.io."""

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
        elif isinstance(other, list) and all(isinstance(item, Template) for item in other):
            return self.data == other
        return False

    def __ne__(self, other: object) -> bool:
        return not self == other

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
        return TemplateList(template for template in self.data if term.casefold() in template.name.casefold())

    def startswith(self, term: str) -> TemplateList:
        """Returns gitignore.io templates where template name starts with term."""
        return TemplateList(template for template in self.data if template.name.casefold().startswith(term.casefold()))

    def match(self, term: str) -> Template | None:
        """Returns first gitignore.io template where template name matches term."""
        for template in self.data:
            if template.name.casefold() == term.casefold():
                return template

    def findall(self, terms: Iterable[str]) -> TemplateList:
        """Returns gitignore.io templates where template name matches terms."""
        terms = [term.casefold() for term in terms]
        return TemplateList(template for term in terms for template in self.data if term == template.name.casefold())

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

        template_names = response.text.splitlines()
        for name in template_names:
            self.replace(Template(name))

    @classmethod
    def parse(cls, text: str) -> TemplateList:
        """Parse templates from a string."""
        lines = text.strip().splitlines()
        pattern = re.compile(r"^#\s(\S+)\s+#$")
        headers = TemplateList._find_metadata(lines, pattern)

        if len(headers) == 0:
            raise ignoro.exceptions.ParseError("Missing template headers")

        templates = cls()
        while len(headers) > 0:
            current_header_index, _ = headers.pop(0)

            if len(headers) > 0:
                next_header_index, _ = headers[0]
                content = "".join(f"{line}\n" for line in lines[current_header_index - 1 : next_header_index - 1])
            else:
                content = "".join(f"{line}\n" for line in lines[current_header_index - 1 :])

            templates.append(Template.parse(content))

        return templates


class Gitignore(_FindMetadataMixin):
    _header: str = "# Created by https://github.com/solbero/ignoro\n"

    def __init__(self, template_list: Optional[ignoro.TemplateList] = None) -> None:
        """Initialize a .gitignore file from a list of templates."""
        self.template_list = template_list or ignoro.TemplateList()

    def __str__(self) -> str:
        return f"{self._header}\n{self.template_list}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.template_list!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Gitignore):
            return self.template_list == other.template_list
        return False

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __len__(self) -> int:
        return len(self.template_list)

    def dumps(self) -> str:
        """Dump the .gitignore to a string."""
        return str(self)

    def dump(self, path: pathlib.Path) -> None:
        """Dump the .gitignore to a file."""
        try:
            if path.is_dir():
                raise IsADirectoryError(f"Path '{path.absolute()}' is a directory")
        except PermissionError as err:
            raise PermissionError(f"Permission denied for '{path.absolute()}'") from err

        try:
            path.write_text(self.dumps())
        except PermissionError as err:
            raise PermissionError(f"Permission denied for '{path.absolute()}'.") from err

    @classmethod
    def loads(cls, text: str) -> Gitignore:
        """Load a .gitignore from a string."""
        try:
            return cls._parse(text)
        except ignoro.exceptions.ParseError as err:
            raise ignoro.exceptions.ParseError(f"Input is invalid: {err}") from err

    @classmethod
    def load(cls, path: pathlib.Path) -> Gitignore:
        """Load a .gitignore from a file."""
        try:
            if path.is_dir():
                raise IsADirectoryError(f"Path '{path.absolute()}' is a directory")
        except PermissionError as err:
            raise PermissionError(f"Permission denied for '{path.absolute()}'.") from err

        try:
            with open(path) as file:
                return cls.loads(file.read())
        except ignoro.exceptions.ParseError as err:
            raise ignoro.exceptions.ParseError(f"File '{path.absolute()}' is invalid: {err}") from err
        except FileNotFoundError as err:
            raise FileNotFoundError(f"File '{path.absolute()}' does not exist") from err
        except PermissionError as err:
            raise PermissionError(f"Permission denied for '{path.absolute()}'") from err

    @classmethod
    def _parse(cls, text: str) -> Gitignore:
        """Parse a .gitignore from a string."""
        lines = text.strip().splitlines()
        pattern = re.compile(f"^{cls._header.strip()}$")
        header = cls._find_metadata(lines, pattern)

        if header:
            content = "".join(f"{line}\n" for line in lines[header[0].index + 1 :])
        else:
            content = "".join(f"{line}\n" for line in lines)

        if not content.strip():
            return cls()

        return cls(ignoro.TemplateList.parse(content))
