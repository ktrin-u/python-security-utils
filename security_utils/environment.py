"""
Utility functions for environment centric matters

Overview
--------
The functions in this module are designed to simplify the management of environment variables and
project configuration for security-sensitive Python applications. It includes logic for recursively
locating the project root, loading secrets from .env files, and enforcing the presence of required environment variables.

Dependencies
------------
- dotenv: For loading environment variables from .env files.
- security_utils.exceptions: For custom exception handling.

Examples
--------
>>> from security_utils.environment import get_required_env_var
>>> api_key = get_required_env_var('API_KEY')

"""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from dotenv.main import StrPath

from security_utils.exceptions import (
    MissingProjectEnvironmentVariable,
    MissingRequiredEnvironmentVariable,
)

logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """
    Recursively finds the project root directory by searching for known root files.

    Returns
    -------
    Path
        Path to the project root directory.

    Raises
    ------
    StopIteration
        If the project root cannot be found.
    """
    ROOT_FILES = ["pyproject.toml"]

    def recurse(cwd: Path, prev: Optional[Path] = None) -> Path:
        if cwd == prev:
            raise StopIteration("Failed to find project root path.")

        for file in os.listdir(cwd):
            if file in ROOT_FILES:
                pyproject_path = cwd.joinpath("pyproject.toml")
                try:
                    with open(pyproject_path, "r", encoding="utf-8") as f:
                        first_line = f.readline().strip()
                        if first_line == "[project]":
                            return cwd.resolve()
                except:  # noqa: E722
                    ...

        next = cwd.parent

        if not next.exists() and not os.listdir(next):
            raise StopIteration("Failed to find project root path.")

        return recurse(cwd.parent, cwd)

    return recurse(Path(__file__).parent)


def load_env_secrets(secrets_path: StrPath = Path(".secrets")) -> None:
    """
    Loads environment variables from all .env files in the specified secrets directory.

    Parameters
    ----------
    secrets_path : StrPath, optional
        Path to the secrets directory (default is ".secrets").

    Returns
    -------
    None

    Raises
    ------
    Exception
        If the secrets directory does not exist and not running in Docker.
    """
    secrets_folder = get_project_root().joinpath(secrets_path).resolve()

    if secrets_folder.exists() and secrets_folder.is_dir():
        for file in os.listdir(secrets_folder):
            file_path = secrets_folder.joinpath(file)
            if not file.endswith(".env") or not file_path.is_file():
                logger.debug(f"Skipping {file_path}")
                continue
            logger.debug(f"Loading {file_path}")
            load_dotenv(file_path)
        return

    if os.getenv("ISDOCKER", None):
        return

    raise Exception(
        f"Failed to load environment secrets: {secrets_folder} does not exist"
    )


def get_required_env_var(variable_name: str) -> str:
    """
    Gets a required environment variable, raising an exception if it is not found.

    Parameters
    ----------
    variable_name : str
        Name of the environment variable.

    Returns
    -------
    str
        Value of the environment variable.

    Raises
    ------
    MissingRequiredEnvironmentVariable
        If the variable is not found.
    """
    try:
        return os.environ[variable_name.upper()]
    except KeyError:
        raise MissingRequiredEnvironmentVariable(variable_name)


def get_project_environment(aliases: Optional[list[str]] = None) -> str:
    """
    Gets the project environment from a list of possible environment variable aliases.

    Parameters
    ----------
    aliases : list of str, optional
        List of environment variable names to check (default is ["PROJECT_ENVIRONMENT", "ENVIRONMENT"]).

    Returns
    -------
    str
        Value of the first found environment variable.

    Raises
    ------
    TypeError
        If aliases is not a list of strings.
    MissingProjectEnvironmentVariable
        If none of the aliases are found in the environment.
    """
    if aliases is None:
        aliases = ["PROJECT_ENVIRONMENT", "ENVIRONMENT"]
    if not isinstance(aliases, list):
        raise TypeError(f"aliases must be a list, got {type(aliases)}")
    if not any(isinstance(alias, str) for alias in aliases):
        raise TypeError("aliases must be a list[str]")
    for alias in aliases:
        environment = os.getenv(alias.upper(), None)
        if isinstance(environment, str):
            return environment
    raise MissingProjectEnvironmentVariable(aliases)
