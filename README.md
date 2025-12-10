# security_utils

Utilities for secure environment management, secrets loading, and
structured logging.

The logging is designed to be an expanded and detailed version instead of a simple concise one.

This package provides small helpers intended for use and consistency
across other projects and services.

## Features

- Loading and validating environment variables
- Discovering the project root
- Consistent logging setup with console and rotating file handlers

## Modules

- `security_utils.environment` — Environment and secrets utilities
- `security_utils.logging` — Logging setup utilities (`LoggerManager`, configured formatters and handlers)
- `security_utils.exceptions` — Custom exception classes

## Installation

Install using [uv by Astral](https://docs.astral.sh/uv/)

```sh
# Install over HTTP(S).
uv add git+<repo_url>@<tag or branch>

# Install over SSH.
uv add git+ssh:<repo_url>@<tag or branch>
```

## Logging Usage Example

The package provides a small manager to configure package loggers with a
standard formatter and sensible defaults.

Example — configure a logger for a package or module::

```python
from security_utils.logging import LoggerManager

# Configure a logger named after your module
# Define your own identifier for the log entries
LoggerManager.setup("MyService", __name__)

import logging
logger = logging.getLogger(__name__)
logger.info("Service started")
```

## Notes

- `LoggerManager.setup` accepts optional parameters to control whether a
  console handler and/or a timed rotating file handler are attached, the
  base logs directory, and the logger level.
- The formatter emits structured, multi-line messages and will include
  optional record attributes when present (for example `request`,
  `response`, `user`, `details`, `objects`).

## Contributing

Contributions are welcome. Run the test suite and linter before opening a
pull request. Use the `justfile` commands for formatting and testing:

```sh
just style
just test
```

For more details see `pyproject.toml` and the package sources under
`security_utils/`.
