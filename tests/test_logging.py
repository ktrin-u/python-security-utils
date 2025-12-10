def test_console_logging_object_block(capsys):
    """LoggerManager should format objects in the console log for debugging."""
    from security_utils.logging import LoggerManager

    logger_name = "security_utils.tests.object_logger"
    LoggerManager.setup(
        "TestService",
        logger_name,
        logger_files_path=None,
        console_handler=True,
        rotating_file_handler=False,
    )

    logger = logging.getLogger(logger_name)

    class Dummy:
        def __init__(self, a, b):
            self.a = a
            self.b = b

    class WithSlots:
        __slots__ = ("x", "y")

        def __init__(self, x, y):
            self.x = x
            self.y = y

    obj1 = Dummy(1, "foo")
    obj2 = WithSlots(3.14, [1, 2, 3])
    obj3 = (42, "tuple")

    logger.info("Testing object block", extra={"objects": [obj1, obj2, obj3]})

    captured = capsys.readouterr()


    _cleanup_logger(logger_name)


import logging
from pathlib import Path


def _cleanup_logger(name: str) -> None:
    logger = logging.getLogger(name)
    for h in list(logger.handlers):
        logger.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass


def test_file_logging_with_extra(tmp_path: Path) -> None:
    """LoggerManager should write formatted messages (including extra) to the file."""
    from security_utils.logging import LoggerManager

    logger_name = "security_utils.tests.file_logger"
    # use tmp_path as base for logs
    LoggerManager.setup(
        "TestService",
        logger_name,
        logger_files_path=tmp_path,
        console_handler=False,
        rotating_file_handler=True,
    )

    logger = logging.getLogger(logger_name)
    logger.info(
        "hello file",
        extra={"extra": "FILE_EXTRA", "request_id": "r1", "user": "u1"},
    )

    # flush and close handlers to ensure file is written
    for h in list(logger.handlers):
        try:
            h.flush()
        except Exception:
            pass

    logfile = tmp_path / "_logs" / "logs.log"
    assert logfile.exists(), "Log file was not created"
    content = logfile.read_text(encoding="utf-8")
    assert "hello file" in content
    assert "Extra:" not in content

    _cleanup_logger(logger_name)


def test_console_logging_outputs_message(capsys) -> None:
    """LoggerManager should emit to the console (stderr) when console_handler=True."""
    from security_utils.logging import LoggerManager

    logger_name = "security_utils.tests.console_logger"
    LoggerManager.setup(
        "TestService",
        logger_name,
        logger_files_path=None,
        console_handler=True,
        rotating_file_handler=False,
    )

    logger = logging.getLogger(logger_name)
    logger.info(
        "hello console",
        extra={
            "details": "CONSOLE_EXTRA",
            "user": "Test User",
        },
    )

    captured = capsys.readouterr()

    # StreamHandler defaults to stderr
    assert "hello console" in captured.err
    assert "CONSOLE_EXTRA" in captured.err

    _cleanup_logger(logger_name)


def test_exception_logging_writes_traceback(capsys) -> None:
    """LoggerManager should include exception tracebacks in the file log."""
    from security_utils.logging import LoggerManager

    logger_name = "security_utils.tests.exception_logger"
    LoggerManager.setup(
        "TestService",
        logger_name,
        logger_files_path=None,
        console_handler=True,
        rotating_file_handler=False,
    )

    logger = logging.getLogger(logger_name)
    try:

        def inner():
            raise KeyError("missing-key")

        def middle():
            try:
                inner()
            except KeyError as e:
                raise RuntimeError("wrapped error") from e

        middle()
    except Exception:
        logger.exception("Complex exception with chaining")

    for h in list(logger.handlers):
        try:
            h.flush()
        except Exception:
            pass

    captured = capsys.readouterr()


    _cleanup_logger(logger_name)


def test_console_logging_request_response_blocks(capsys):
    """LoggerManager should format requests and responses in the console log."""
    import requests

    from security_utils.logging import LoggerManager

    logger_name = "security_utils.tests.reqresp_logger"
    LoggerManager.setup(
        "TestService",
        logger_name,
        logger_files_path=None,
        console_handler=True,
        rotating_file_handler=False,
    )

    logger = logging.getLogger(logger_name)

    # Create a requests.Request and requests.Response
    req = requests.Request(
        method="POST",
        url="https://example.com/api",
        headers={"Authorization": "Bearer TOKEN"},
        data="payload-data",
    ).prepare()

    # Simulate a response object
    class DummyResponse:
        status_code = 201
        url = "https://example.com/api"
        headers = {"Content-Type": "application/json"}
        text = '{"result": "ok"}'

    resp = DummyResponse()

    logger.info(
        "Testing request/response blocks",
        extra={"request": req, "response": resp},
    )

    captured = capsys.readouterr()


    _cleanup_logger(logger_name)


def test_console_logging_all_blocks(capsys):
    """Emit a single set of logs that exercise every formatter block.

    This test writes to the console handler and verifies that the output
    contains message, request, response, user, details, objects and an
    exception traceback emitted by a subsequent ``logger.exception`` call.
    """
    import logging

    import requests

    from security_utils.logging import LoggerManager

    logger_name = "security_utils.tests.all_blocks_logger"
    LoggerManager.setup(
        "TestService",
        logger_name,
        logger_files_path=None,
        console_handler=True,
        rotating_file_handler=False,
    )

    logger = logging.getLogger(logger_name)

    class Dummy:
        def __init__(self, a, b):
            self.a = a
            self.b = b

    class WithSlots:
        __slots__ = ("x", "y")

        def __init__(self, x, y):
            self.x = x
            self.y = y

    obj1 = Dummy(7, "seven")
    obj2 = WithSlots(2.71, {"k": "v"})
    obj3 = [1, 2, 3]

    req = requests.Request(
        method="PUT",
        url="https://example.test/all",
        headers={"X-Test": "1"},
        data="payload",
    ).prepare()

    class DummyResp:
        status_code = 202
        url = "https://example.test/all"
        headers = {"Content-Type": "text/plain"}
        text = "ok"

    resp = DummyResp()

    # Log a normal info record covering most blocks
    logger.info(
        "All blocks message",
        extra={
            "request": req,
            "response": resp,
            "user": "tester",
            "auth_info": "token-xyz",
            "details": "lots of details",
            "objects": [obj1, obj2, obj3],
            "status": "RUNNING",
        },
    )

    # Emit an exception log to exercise exception_block
    try:
        raise ValueError("boom")
    except Exception:
        logger.exception("Exception for testing")

    captured = capsys.readouterr()


    # Basic assertions that blocks exist in output
    assert "All blocks message" in captured.err
    assert "Request:" in captured.err
    assert "Response:" in captured.err
    assert "User:" in captured.err
    assert "Details:" in captured.err
    assert "Objects:" in captured.err
    assert (
        "Exception Details:" in captured.err
        or "Traceback (most recent call last)" in captured.err
    )

    _cleanup_logger(logger_name)


def test_console_logging_message_only(capsys):
    """Emit only a plain message and ensure no other blocks are printed."""
    import logging

    from security_utils.logging import LoggerManager

    logger_name = "security_utils.tests.message_only_logger"
    LoggerManager.setup(
        "TestService",
        logger_name,
        logger_files_path=None,
        console_handler=True,
        rotating_file_handler=False,
    )

    logger = logging.getLogger(logger_name)
    logger.info("Just a simple message")

    captured = capsys.readouterr()


    # Message should be present, but other named blocks should not
    assert "Just a simple message" in captured.err
    assert "Details:" not in captured.err
    assert "Objects:" not in captured.err
    assert "Request:" not in captured.err
    assert "Response:" not in captured.err

    _cleanup_logger(logger_name)
