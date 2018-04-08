"""Exceptions."""


class MissingConfigurationFileException(BaseException):
    """An exception that raises when trying to reload some configuration file and it's missing."""

    def __init__(self, file_path):
        """
        @param file_path: The path of the missing configuration file.
        """
        self._file_path = file_path

    def __str__(self):
        return 'Missing configuration file ("{}") - please create it using from the templates.'.format(
            self._file_path)


class MissingConfigurationAttributeException(BaseException):
    """An exception that raises when trying to get some configuration attribute and this attribute not found."""

    def __init__(self, attr_name):
        """
        @param attr_name: The name of the missing configuration attribute.
        """
        self._attr_name = attr_name

    def __str__(self):
        return 'Missing configuration attribute ("{}") - please check the configuration files.'.format(
            self._attr_name)


class NoWrapperForPyGithubObjectException(BaseException):
    """An exception that raises when no wrapper found for the pygithub object."""

    def __init__(self, obj):
        """
        @param obj: Any object that had to be the `GithubObject`.
        """
        from nudgebot.thirdparty.github.base import PyGithubObjectWrapper
        self._obj = obj
        self._all_subclasses = PyGithubObjectWrapper.get_subclasses()

    def __str__(self):
        return 'Could not found wrapper for PyGithub object: {};\nAll Wrappers:\n{}'.format(
            self._obj, '\n    '.join(['{} wraps {}'.format(c, c.PyGithubClass) for c in self._all_subclasses]))


class CouldNotFindUserException(BaseException):
    """An exception that raises when trying to instantiate a user that not found in the configuration file."""

    def __init__(self, key, available_users=None):
        """
        @param key: `str` The user key.
        @keyword available_users: (`list` of `str`) The list of the available users.
        """
        self._key = key
        self._available_users = available_users

    def __str__(self):
        return f'Could not found user key "{self._key}". available: {self._available_users}'


class SubThreadException(BaseException):
    """An exception that raises when a sub thread has count an exception."""

    def __init__(self, thread):
        """
        @param thread: `Thread` The thread.
        """
        self._thread = thread

    def __str__(self):
        return f'Thread "{self._thread.name}" has count an exception.'
