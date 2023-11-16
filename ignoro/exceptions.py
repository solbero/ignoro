class ParseError(ValueError):
    """Raised when parsing a template fails."""

    ...


class ApiError(Exception):
    """Raised when fetching a template fails."""

    ...
