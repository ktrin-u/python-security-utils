class MissingRequiredEnvironmentVariable(Exception):
    """
    Exception raised when an expected environment variable is missing.

    :param variable_name: Name of the missing environment variable.
    :type variable_name: str
    """

    def __init__(self, variable_name, *args) -> None:
        self.variable_name = variable_name

    def __str__(self) -> str:
        """
        Returns a string representation of the exception.

        :return: Error message
        :rtype: str
        """
        return f"The variable {self.variable_name} does not exist within the environment."