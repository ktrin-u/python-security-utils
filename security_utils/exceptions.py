"""
Custom exception classes for the security_utils package.

This module defines exceptions for missing environment variables and other security-related errors.
"""

from collections.abc import Iterable


class MissingRequiredEnvironmentVariable(Exception):
    """
    Exception raised when an expected environment variable is missing.

    Exception raised when a required environment variable is missing.

    Parameters
    ----------
    variable_name : str
        Name of the missing environment variable.
    """

    def __init__(self, variable_name: str, *args) -> None:
        self.variable_name = variable_name

    def __str__(self) -> str:
        """
        Returns a string representation of the exception.

        :return: Error message
        :rtype: str
        """
        return f"The variable {self.variable_name} does not exist within the environment."


class MissingProjectEnvironmentVariable(Exception):
    """
    Exception raised when an expected environment variable is missing.

    Exception raised when none of the project environment variable aliases are found.

    Parameters
    ----------
    aliases : list of str
        List of environment variable names that were checked.
    """

    def __init__(self, aliases: Iterable[str], *args) -> None:
        if not isinstance(aliases, Iterable):
            raise TypeError(f"aliases must be an Iterable, got {type(aliases)}")
        if not any(filter(lambda alias: isinstance(alias, str), aliases)):
            raise TypeError("aliases must be an Iterable[str]")
        self.aliases = aliases

    def __str__(self) -> str:
        """
        Returns a string representation of the exception.

        :return: Error message
        :rtype: str
        """
        return f"The project's environment type could not be determined from the environment. Attempted the following {[i.upper() for i in self.aliases]}"
