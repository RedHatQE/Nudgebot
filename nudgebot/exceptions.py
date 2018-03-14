class MissingConfigurationFileException(BaseException):
    def __init__(self, file_path):
        """An exception that raises when trying to reload some configuration file and it's missing.
            @param file_path: The path of the missing configuration file.
        """
        self._file_path = file_path

    def __str__(self):
        return 'Missing configuration file ("{}") - please create it using from the templates.'.format(
            self._project_name, self._file_path)
