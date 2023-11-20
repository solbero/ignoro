from __future__ import annotations

import collections
import collections.abc
import pathlib
import re

import requests
from typing_extensions import Callable, Iterable, Iterator, NamedTuple, Optional, SupportsIndex

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

            content = Template._strip(response.text)
            self._body = Template.parse(content).body

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
        lines = content.strip().splitlines()
        pattern = re.compile(r"^### (\S+) ###$")
        headers = Template._find_metadata(lines, pattern)

        if len(headers) == 0:
            raise ignoro.exceptions.ParseError("Missing header")
        elif len(headers) > 1:
            raise ignoro.exceptions.ParseError("Multiple headers")

        index, name = headers[0].index, headers[0].match.group(1)
        body = "".join(f"{line}\n" for line in lines[index + 1 :])

        if not body.strip():
            raise ignoro.exceptions.ParseError("Missing body")

        return Template(name, body)

    @staticmethod
    def _strip(response: str) -> str:
        lines = response.splitlines()
        content = "\n".join(lines[3:-2])
        return content


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
        """Returns a gitignore.io template where template name matches term."""
        term = term.lower()
        for template in self.data:
            if template.name.lower() == term:
                return template

    def findall(self, terms: Iterable[str]) -> TemplateList:
        """Returns gitignore.io templates where template name matches terms."""
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
        lines = text.strip().splitlines()
        pattern = re.compile(r"^### \S+ ###$")
        headers = TemplateList._find_metadata(lines, pattern)

        if len(headers) == 0:
            raise ignoro.exceptions.ParseError("Missing template headers")

        templates = TemplateList()
        while len(headers) > 0:
            current_header_index, _ = headers.pop(0)

            if len(headers) > 0:
                next_header_index, _ = headers[0]
                content = "".join(f"{line}\n" for line in lines[current_header_index:next_header_index])
            else:
                content = "".join(f"{line}\n" for line in lines[current_header_index:])

            template = Template.parse(content)
            templates.append(template)

        return templates


class Gitignore(_FindMetadataMixin):
    _header: str = (
        "# Created by https://github.com/solbero/ignoro\n" + "# TEXT BELOW THIS LINE WAS AUTOMATICALLY GENERATED\n"
    )
    _footer: str = "# TEXT ABOVE THIS LINE WAS AUTOMATICALLY GENERATED\n"

    def __init__(self, template_list: Optional[ignoro.TemplateList]) -> None:
        """Initialize a .gitignore file from a list of templates."""
        self.template_list = template_list or ignoro.TemplateList()

    def __str__(self) -> str:
        return f"{self._header}\n{self.template_list}\n{self._footer}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.template_list!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Gitignore):
            return self.template_list == other.template_list
        return False

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
            path.write_text(str(self))
        except PermissionError as err:
            raise PermissionError(f"Permission denied for '{path.absolute()}'.") from err

    @classmethod
    def loads(cls, text: str) -> Gitignore:
        """Load a .gitignore from a string."""
        try:
            return Gitignore._parse(text)
        except ignoro.exceptions.ParseError as err:
            raise ignoro.exceptions.ParseError(f"Input is invalid: {err}") from err

    @staticmethod
    def load(path: pathlib.Path) -> Gitignore:
        """Load a .gitignore from a file."""
        try:
            if path.is_dir():
                raise IsADirectoryError(f"Path '{path.absolute()}' is a directory")
        except PermissionError as err:
            raise PermissionError(f"Permission denied for '{path.absolute()}'.") from err

        try:
            with open(path, "r") as file:
                return Gitignore._parse(file.read())
        except ignoro.exceptions.ParseError as err:
            raise ignoro.exceptions.ParseError(f"File '{path.absolute()}' is invalid: {err}") from err
        except FileNotFoundError as err:
            raise FileNotFoundError(f"File '{path.absolute()}' does not exist") from err
        except PermissionError as err:
            raise PermissionError(f"Permission denied for '{path.absolute()}'") from err

    @staticmethod
    def _parse(text: str) -> Gitignore:
        """Parse a .gitignore from a string."""
        lines = text.strip().splitlines()
        pattern_header = re.compile(r"^# TEXT BELOW THIS LINE WAS AUTOMATICALLY GENERATED$")
        headers = Gitignore._find_metadata(text.splitlines(), pattern_header)
        pattern_footer = re.compile(r"^# TEXT ABOVE THIS LINE WAS AUTOMATICALLY GENERATED$")
        footers = Gitignore._find_metadata(text.splitlines(), pattern_footer)

        if len(headers) == 0 and len(footers) == 0:
            raise ignoro.exceptions.ParseError("Missing ignoro header and footer")

        if len(headers) == 0:
            raise ignoro.exceptions.ParseError("Missing ignoro header")
        elif len(headers) > 1:
            raise ignoro.exceptions.ParseError("Multiple ignoro headers")

        if len(footers) == 0:
            raise ignoro.exceptions.ParseError("Missing ignoro footer")
        elif len(footers) > 1:
            raise ignoro.exceptions.ParseError("Multiple ignoro footers")

        index_header, _ = headers[0]
        index_footer, _ = footers[0]
        content = "".join(f"{line}\n" for line in lines[index_header + 1 : index_footer])

        if not content.strip():
            raise ignoro.exceptions.ParseError("Missing .gitignore body")

        template_list = ignoro.TemplateList.parse(content)

        return Gitignore(template_list)
