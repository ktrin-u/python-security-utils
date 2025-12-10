import logging
from collections.abc import Mapping
from logging import LogRecord
from typing import Any, Literal


class ExpandedFormatter(logging.Formatter):
    """Formatter that builds structured, multi-line log messages.

    The formatter constructs a sequence of human-readable blocks (header,
    message, request/response, user, details, objects, exception) from a
    ``logging.LogRecord`` instance. It is intended for use with handlers that
    output text logs.

    Parameters
    ----------
    identifier : str
        Unique identifier included in the log header to help locate the
        originating service/process.
    fmt : str | None, optional
        Format string passed to the base :class:`logging.Formatter`.
    datefmt : str | None, optional
        Date format string passed to the base :class:`logging.Formatter`.
    style : {'%', '{', '$'}, optional
        Formatting style for :class:`logging.Formatter`.
    validate : bool, optional
        Whether to validate the format string.
    defaults : Mapping[str, Any] | None, optional
        Default values passed to the base formatter.

    Optional Record Attributes
    --------------------------
    The following attributes may be present on the :class:`logging.LogRecord`
    and will be inspected by the formatter to produce additional output.

    status : str, optional
        Status value appended to the header if present on the record.
    user : str, optional
        Username or identifier for the acting user; used by :meth:`user_block`.
    auth_info : Any, optional
        Additional authentication information printed under the user.
    details : Any, optional
        Arbitrary details included in the :meth:`details_block` output.
    request : Any, optional
        HTTP request-like object inspected by :meth:`_process_http_object` and
        emitted by :meth:`request_block`.
    response : Any, optional
        HTTP response-like object inspected by :meth:`_process_http_object` and
        emitted by :meth:`response_block`.
    objects : list, optional
        A list of arbitrary objects that will be introspected by
        :meth:`object_block`.
    """

    def __init__(
        self,
        identifier: str,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%"] | Literal["{"] | Literal["$"] = "%",
        validate: bool = True,
        *,
        defaults: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)

        self.identifier = str(identifier)

    def header_block(self, record: LogRecord) -> list[str]:
        """Build the header block for a log record.

        The header contains a timestamp, log level, identifier and logger name.
        If the ``record`` has a ``status`` attribute it will also be included.

        Parameters
        ----------
        record : logging.LogRecord
            The record to format.

        Returns
        -------
        list[str]
            Lines that make up the header block (single-element list).
        """
        ts = self.formatTime(record, self.datefmt)
        header = f"[{ts}][{record.levelname}][{self.identifier}][{record.name}]"
        status = getattr(record, "status", None)
        if status:
            header += f"[{status}]"

        return [header]

    def message_block(self, record: LogRecord) -> list[str]:
        """Format the message block for a log record.

        This includes the core log message returned by ``record.getMessage()``.

        Parameters
        ----------
        record : logging.LogRecord
            The record to format.

        Returns
        -------
        list[str]
            Lines for the message block. Empty list when no message present.
        """
        # safe dynamic fields
        message = record.getMessage()
        lines: list[str] = []
        if message:
            lines.append("Message:")
            lines.append(f"\t{message}")
            lines.append("")
        return lines

    def user_block(self, record: LogRecord) -> list[str]:
        """Format user/authentication information if present on the record.

        Parameters
        ----------
        record : logging.LogRecord
            The record that may contain ``user`` and ``auth_info`` attributes.

        Returns
        -------
        list[str]
            Lines for the user block; empty list when no user information.
        """
        user = getattr(record, "user", None)
        lines: list[str] = []

        auth_info = getattr(record, "auth_info", None)
        if user:
            lines.append("User:")
            lines.append(f"\t{user}")
            if auth_info:
                lines.append("")
                lines.append("\tAuth Info:")
                lines.append(f"\t\t{auth_info}")
            lines.append("")
        return lines

    def details_block(self, record: LogRecord) -> list[str]:
        """Include an arbitrary ``details`` attribute from the record.

        Parameters
        ----------
        record : logging.LogRecord
            The record that may have a ``details`` attribute.

        Returns
        -------
        list[str]
            Lines describing the details; empty list if ``details`` is None.
        """
        details = getattr(record, "details", None)
        lines: list[str] = []
        if details is not None:
            lines.append("Details:")
            try:
                lines.append(f"\t{details}")
            except Exception:
                lines.append("\t<unrepresentable>")
            lines.append("")
        return lines

    def exception_block(self, record: LogRecord) -> list[str]:
        """Format exception information when ``exc_info`` is present.

        Parameters
        ----------
        record : logging.LogRecord
            The record that may contain exception information.

        Returns
        -------
        list[str]
            Lines that show the function name and formatted exception text.
        """
        lines: list[str] = []
        if record.exc_info:
            lines.append("Function Name:")
            lines.append(f"\t{record.funcName}")
            lines.append("")

            exc_text = self.formatException(record.exc_info)
            lines.append("Exception Details:")
            for line in exc_text.strip().splitlines():
                lines.append(f"\t{line}")
        return lines

    def _process_http_object(self, http_object: Any) -> list[str]:
        """Inspect a request/response-like object and produce detail lines.

        The function checks for common attributes used by HTTP client/response
        objects (``status_code``, ``method``, ``url``, ``headers``,
        ``body``, ``text``) and emits human-readable lines describing them.

        Parameters
        ----------
        http_object : Any
            An object representing an HTTP request or response.

        Returns
        -------
        list[str]
            Lines describing the http object; empty list when no meaningful
            attributes are present.
        """
        lines: list[str] = []
        if hasattr(http_object, "status_code"):
            lines.append(
                f"\tStatus: {getattr(http_object, 'status_code', None)}"
            )

        if hasattr(http_object, "status_code"):
            lines.append(f"\tMethod: {getattr(http_object, 'method', None)}")

        lines.append(f"\tURL: {getattr(http_object, 'url', None)}")

        if hasattr(http_object, "headers"):
            lines.append(
                f"\tHeaders: {dict(getattr(http_object, 'headers', {}))}"
            )

        if hasattr(http_object, "body") and getattr(http_object, "body", None):
            lines.append(f"\tBody: {getattr(http_object, 'body', None)}")

        if hasattr(http_object, "text"):
            body = getattr(http_object, "text", None)
            if body:
                lines.append(f"\tBody: {body}")
        return lines

    def request_block(self, record: LogRecord) -> list[str]:
        """Format a ``request`` attribute from the record, if present.

        Parameters
        ----------
        record : logging.LogRecord
            The record that may contain a ``request`` attribute.

        Returns
        -------
        list[str]
            Lines describing the request; empty list when not present.
        """
        request = getattr(record, "request", None)
        lines: list[str] = []
        if request is not None:
            lines.append("Request:")
            parsed = self._process_http_object(request)
            if parsed:
                lines += parsed
            else:
                lines.append(f"\t{request}")
            lines.append("")
        return lines

    def response_block(self, record: LogRecord) -> list[str]:
        """Format a ``response`` attribute from the record, if present.

        Parameters
        ----------
        record : logging.LogRecord
            The record that may contain a ``response`` attribute.

        Returns
        -------
        list[str]
            Lines describing the response; empty list when not present.
        """
        response = getattr(record, "response", None)
        lines: list[str] = []
        if response is not None:
            lines.append("Response:")
            parsed = self._process_http_object(response)
            if parsed:
                lines += parsed
            else:
                lines.append(f"\t{response}")
            lines.append("")
        return lines

    def object_block(self, record: LogRecord) -> list[str]:
        """Format arbitrary objects attached to the record via ``objects``.

        If ``record.objects`` is a list, each object will be inspected for
        ``__dict__`` or ``__slots__`` and a readable representation emitted.

        Parameters
        ----------
        record : logging.LogRecord
            The record that may contain an ``objects`` attribute.

        Returns
        -------
        list[str]
            Lines describing the provided objects; empty list when none.
        """
        objects: list[object] | None = getattr(record, "objects", None)
        lines: list[str] = []
        if objects and isinstance(objects, list):
            lines.append("Objects:")
            for idx, obj in enumerate(objects, 1):
                lines.append(f"\tObject {idx} - {obj.__class__.__qualname__}:")
                # Try to get a useful representation
                if hasattr(obj, "__dict__"):
                    for k, v in vars(obj).items():
                        lines.append(f"\t\t{k}: {v}")
                elif hasattr(obj, "__slots__"):
                    for k in obj.__slots__:  # pyright: ignore[reportAttributeAccessIssue]
                        v = getattr(obj, k, None)
                        lines.append(f"\t\t{k}: {v}")
                else:
                    lines.append(f"\t\t{repr(obj)}")
            lines.append("")
        return lines

    def format(self, record: LogRecord) -> str:
        """Assemble all blocks into the final formatted string.

        Parameters
        ----------
        record : logging.LogRecord
            The record to format.

        Returns
        -------
        str
            The multi-line formatted log message.
        """
        lines: list[str] = []
        lines += self.header_block(record)
        lines += self.message_block(record)
        lines += self.request_block(record)
        lines += self.response_block(record)
        lines += self.user_block(record)
        lines += self.details_block(record)
        lines += self.object_block(record)
        lines += self.exception_block(record)
        return "\n".join(lines)
