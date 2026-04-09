import re
import traceback as tb
from collections.abc import Mapping, Sequence
from logging import LogRecord
from types import TracebackType
from typing import Any, Literal, cast

import termcolor
from msgspec import json
from pythonjsonlogger.core import BaseJsonFormatter


class YamlStyleFormatter(BaseJsonFormatter):
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
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%"] | Literal["{"] | Literal["$"] = "%",
        validate: bool = True,
        *,
        prefix: str = "",
        rename_fields: dict[str, str] | None = None,
        rename_fields_keep_missing: bool = False,
        static_fields: dict[str, Any] | None = None,
        reserved_attrs: Sequence[str] | None = None,
        timestamp: bool | str = False,
        defaults: dict[str, Any] | None = None,
        exc_info_as_array: bool = False,
        stack_info_as_array: bool = False,
        indent: int = 4,
        levels_color_mapping: dict[str, str | tuple[int, int, int]]
        | None = None,
        colorize: bool = False,
    ) -> None:
        super().__init__(
            fmt,
            datefmt,
            style,
            validate,
            defaults=defaults,
            prefix=prefix,
            rename_fields=rename_fields,
            rename_fields_keep_missing=rename_fields_keep_missing,
            static_fields=static_fields,
            reserved_attrs=reserved_attrs,
            timestamp=timestamp,
            exc_info_as_array=exc_info_as_array,
            stack_info_as_array=stack_info_as_array,
        )

        self.indent = indent
        self.colorize = colorize

        if levels_color_mapping is None:
            self.levels_color_mapping = {
                "ERROR": "light_red",
                "INFO": "green",
                "WARNING": "orange",
                "DEBUG": "light_grey",
                "CRITICAL": "red",
            }
        else:
            self.levels_color_mapping = levels_color_mapping

    def format_levelname(self, levelname: str) -> str:
        if self.colorize:
            return termcolor.colored(
                levelname, self.levels_color_mapping[levelname.upper()]
            )
        return levelname

    @staticmethod
    def format_exception(record: LogRecord) -> dict[str, Any]:
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
        if record.exc_info is None:
            return {}

        exc_info: dict[str, Any] = {}
        exc_info["function name"] = record.funcName

        if any(item for item in record.exc_info if item is not None):
            exc_type, exception, tb_obj = cast(
                tuple[type[BaseException], Exception, TracebackType],
                record.exc_info,
            )
            frames: list[dict[str, Any]] = []
            tb_iter = tb_obj
            while tb_iter is not None:
                frame = tb_iter.tb_frame
                frames.append(
                    {
                        "file": frame.f_code.co_filename,
                        "line_no": tb_iter.tb_lineno,
                        "function": frame.f_code.co_name,
                    }
                )
                tb_iter = tb_iter.tb_next

            formatted = "".join(
                tb.format_exception(exc_type, exception, tb_obj)
            )

            exc_info["traceback"] = frames
            exc_info["formatted"] = formatted

        return exc_info

    def format_request_object(self, obj: object) -> dict[str, str]:
        inner: dict[str, Any] = {}
        for field_name in (
            "method",
            "headers",
            "url",
            "body",
            "content",
            "text",
            "status_code",
            "status",
            "body",
            "query",
            "query_params",
            "content",
        ):
            val = getattr(obj, field_name, None)
            if val is None:
                continue
            # Avoid calling callables or awaiting coroutines in formatter
            if callable(val):
                try:
                    # Some clients expose .text as a property returning str
                    maybe = val()
                except Exception:
                    continue
                else:
                    if isinstance(maybe, (str, bytes)):
                        inner[field_name] = maybe
                    else:
                        inner[field_name] = str(maybe)
            else:
                inner[field_name] = val
        return inner

    def format_default(self, obj: object, depth: int):
        try:
            if obj.__dict__:
                return self._serialize(obj.__dict__, depth + 1)
            raise Exception
        except Exception:
            scalar = "null" if obj is None else str(obj)
            # Quote scalar if it contains problematic characters
            if isinstance(obj, str) and re.search(r"[:#\n\r\t]|^\s|\s$", obj):
                return json.encode(obj).decode()
            return scalar

    def _serialize(self, value: Any, depth: int) -> list[str]:
        indent = " " * (self.indent * depth)
        lines: list[str] = []

        if isinstance(value, Mapping):
            for k, v in value.items():
                kq = str(k)
                # Nested mapping or sequence
                if isinstance(v, (Mapping, list)):
                    if not v:
                        continue
                    lines.append(f"{indent}{kq}:")
                    lines.extend(self._serialize(v, depth + 1))
                elif isinstance(v, str) and "\n" in v:
                    # Use literal block for multi-line strings
                    lines.append(f"{indent}{kq}:")
                    for ln in v.rstrip("\n").splitlines():
                        lines.append(f"{' ' * (self.indent * (depth + 1))}{ln}")
                elif any(
                    True
                    for field in ["method", "url", "headers"]
                    if hasattr(v, field)
                ):
                    inner = self.format_request_object(v)

                    if inner:
                        lines.append(f"{indent}{kq}:")
                        lines.extend(self._serialize(inner, depth + 1))
                else:
                    scalar = self.format_default(v, depth)
                    if isinstance(scalar, str):
                        lines.append(f"{indent}{kq}: {scalar}")
                    else:
                        lines.append(f"{indent}{kq}:")
                        lines.extend(scalar)
            return lines

        if isinstance(value, list):
            for item in value:
                if isinstance(item, (Mapping, list)):
                    lines.append(f"{indent}- {repr(item)}")
                    lines.extend(self._serialize(item, depth + 1))
                elif isinstance(item, str) and "\n" in item:
                    lines.append(f"{indent}- |")
                    for ln in item.rstrip("\n").splitlines():
                        lines.append(f"{' ' * (self.indent * (depth + 1))}{ln}")
                else:
                    scalar = self.format_default(item, depth)
                    if isinstance(scalar, str):
                        lines.append(f"{indent}- {scalar}")
                    else:
                        lines.append(f"{indent}- {repr(item)}")
                        lines.extend(scalar)
                    # lines.append(f"{indent}- {scalar}")
            return lines

        # Fallback scalar
        val = "null" if value is None else str(value)
        return [f"{indent}{val}"]

    def serialize_as_yaml(self, obj: dict, starting_indent: int = 0) -> str:
        """Serialize a mapping to a compact, readable YAML string.

        Ensures multi-line values (like tracebacks) are preserved as
        literal blocks and that keys retain insertion order. Returns a
        trimmed string (no trailing newlines) suitable for inclusion in
        single-line log records or multi-line blocks.
        """

        try:
            return "\n".join(self._serialize(obj, starting_indent))
        except Exception:
            return "exception: <unserializable>"

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

        message_dict: dict[str, Any] = {}
        if isinstance(record.msg, dict):
            message_dict = record.msg
            record.message = ""
        else:
            record.message = record.getMessage()

            message_dict["exception_info"] = self.format_exception(record)
        if record.stack_info and not message_dict.get("stack_info"):
            message_dict["stack_info"] = self.formatStack(record.stack_info)

        log_data: dict[str, Any] = {}
        self.add_fields(log_data, record, message_dict)
        log_data = self.process_log_record(log_data)
        message: str = log_data.pop("message")

        if self.colorize:
            message = f"{termcolor.colored(record.message, 'blue')}"

        return f"[{self.formatTime(record, self.datefmt)}] {self.format_levelname(record.levelname)} {message}\n{self.serialize_as_yaml(log_data, 1)}"
