class MissingConfigurationFileException(BaseException):
    def __init__(self, file_path):
        """An exception that raises when trying to reload some configuration file and it's missing.
            @param file_path: The path of the missing configuration file.
        """
        self._file_path = file_path

    def __str__(self):
        return 'Missing configuration file ("{}") - please create it using from the templates.'.format(
            self._file_path)


class MissingConfigurationAttributeException(BaseException):
    def __init__(self, attr_name):
        """An exception that raises when trying to get some configuration attribute and this attribute not found.
            @param attr_name: The name of the missing configuration attribute.
        """
        self._attr_name = attr_name

    def __str__(self):
        return 'Missing configuration attribute ("{}") - please check the configuration files.'.format(
            self._attr_name)


class NoWrapperForPyGithubObjectException(BaseException):
    def __init__(self, obj):
        """An exception that raises when no wrapper found for the pygithub object.
            @param obj: Any object that had to be the `GithubObject`.
        """
        from nudgebot.thirdparty.github import PyGithubObjectWrapper
        self._obj = obj
        self._all_subclasses = PyGithubObjectWrapper.get_subclasses()

    def __str__(self):
        return 'Could not found wrapper for PyGithub object: {};\nAll Wrappers:\n{}'.format(
            self._obj, '\n    '.join(['{} wraps {}'.format(c, c.PyGithubClass) for c in self._all_subclasses]))
