"""
security_utils
==============

Utilities for secure environment management, secrets loading, and logging.

This package provides helpers for:
    - Loading and validating environment variables
    - Managing project root discovery
    - Secure logging setup

See Also
--------
security_utils.environment : Environment and secrets utilities
security_utils.logging : Logging setup utilities
security_utils.exceptions : Custom exception classes
"""

from security_utils.logging import LoggerManager

LoggerManager.setup("Security Utils", __package__ or __name__)

from security_utils.environment import (
    get_project_root,
    get_required_env_var,
    load_env_secrets,
    get_project_environment,
)  # noqa: F401

__all__ = [
    "get_project_root",
    "get_required_env_var",
    "load_env_secrets",
    "get_project_environment",
]
