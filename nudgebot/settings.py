"""Settings."""
from nudgebot.base import Singleton


class CurrnetProject(metaclass=Singleton):
    """A proxy object for the current project."""

    def __init__(self):
        self._project_package = None

    def setup(self, current_project_package):
        """Setups the current project.

        @param current_project_package: `MuduleType` The project package.
        """
        self._project_package = current_project_package

    def __getattr__(self, name):
        return getattr(self._project_package, name)
