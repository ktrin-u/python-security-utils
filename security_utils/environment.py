"""
This module contains utility functions related to secrets, keys and permission files
"""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from dotenv.main import StrPath

from security_utils.exceptions import MissingRequiredEnvironmentVariable

logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """
    Recursively finds the project root directory by searching for known root files.

    :return: Path to the project root directory
    :rtype: Path
    :raises StopIteration: If the project root cannot be found
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

    :param secrets_path: Path to the secrets directory (default: .secrets)
    :type secrets_path: StrPath
    :return: True if any .env files were loaded, False otherwise
    :rtype: bool
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

    raise Exception(f"Failed to load environment secrets: {secrets_folder} does not exist")


def get_required_env_var(variable_name: str) -> str:
    """
    Gets a required environment variable, raising an exception if it is not found.

    :param variable_name: Name of the environment variable
    :type variable_name: str
    :return: Value of the environment variable
    :rtype: str
    :raises MissingRequiredEnvironmentVariable: If the variable is not found
    """
    try:
        return os.environ[variable_name.upper()]
    except KeyError:
        raise MissingRequiredEnvironmentVariable(variable_name)
