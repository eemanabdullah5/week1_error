"""
Custom exceptions for task1.py.

Every exception here inherits from DataProcessingError, so a caller can catch
all of them with one `except DataProcessingError:`.

Each one ALSO inherits from the built-in exception that task1.py used to raise
(ValueError or TypeError). That way older code and tests that catch ValueError
or TypeError keep working unchanged.
"""


def short_text(text, limit=100):
    """str(text), cut down to `limit` characters, ending in '...' if it was cut.

    Some tests use numbers like 10**1000, whose repr is 1000 digits long, and
    Python's own error messages repeat the bad value in full. Cutting both
    keeps error messages and log lines readable."""
    text = str(text)
    if len(text) > limit:
        text = text[:limit - 3] + "..."
    return text


def short_repr(value, limit=60):
    """repr(value), cut down to `limit` characters (see short_text)."""
    return short_text(repr(value), limit)


class DataProcessingError(Exception):
    """Base class for every error raised on purpose by task1.py.
    Not raised directly; catch it to handle any of the errors below."""


class ConversionError(DataProcessingError, ValueError):
    """Raised when a value can't be converted to the requested type,
    e.g. strict_int("abc") or to_bool("maybe").

    .value  -> the value that could not be converted
    .target -> the name of the type we tried to convert it to, e.g. "int"
    """

    def __init__(self, value, target, message=None):
        self.value = value
        self.target = target
        if message is None:
            message = f"cannot convert {short_repr(value)} to {target}"
        super().__init__(message)


class SchemaError(DataProcessingError, TypeError):
    """Raised when a schema asks for a type we don't know how to convert to,
    e.g. normalize_record(record, {"tags": list})."""


class ParseError(DataProcessingError, ValueError):
    """Raised by parse_key_value_string(..., strict=True) when a pair is
    malformed: it has no key/value separator, or its key is empty."""
