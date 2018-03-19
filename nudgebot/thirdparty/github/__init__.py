from types import FunctionType, MethodType

from github import Github
from github.PaginatedList import PaginatedList
from github.GithubObject import GithubObject

from nudgebot.settings import CURRENT_PROJECT
from nudgebot.exceptions import NoWrapperForPyGithubObjectException


_login_info = CURRENT_PROJECT.config.credentials.github
github_client = Github(_login_info.get('username'), _login_info.get('password'),
                       client_id=_login_info.client_id, client_secret=_login_info.client_secret)


class PyGithubObjectWrapper(object):
    """
    This class is a wrapper for the pygithub objects.
    Each PyGithubObjectWrapper subclass should have an PyGithubClass defined
    (PyGithubClass represents the pygithub class that the subclass wraps), it's could be either a
    list of classes or one class.
    Any time we are getting an attribute, if it doesn't exist, we are getting this attribute from the
    pygithub object and wrap.
    the returned value if it has a wrapper defined (see _convert_to_local).
    In case we want to create an instance without passing a pygibhub object we should use
    `instantiate` function (and implement it),
    e.g. Repository.instantiate('octocat', 'Hello-World')  -->
            Repository(PyGithubObjectWrapper) | Repository(full_name="octocat/Hello-World").
    """
    PyGithubClass = GithubObject  # Overwrite this!

    def __init__(self, pygithub_object):
        """
            @param pygithub_object: `GithubObject` The wrapped pygithub object.
        """
        assert (
            isinstance(pygithub_object, self.PyGithubClass) or
            isinstance(self.PyGithubClass, (tuple, list)) and
            all(isinstance(pygithub_object, cls) for cls in self.PyGithubClass)
        )
        self._pygithub_object = pygithub_object

    def __repr__(self):
        return '[{}({}) | {}]'.format(
            self.__class__.__name__, PyGithubObjectWrapper.__name__, self._pygithub_object.__repr__())

    @classmethod
    def instantiate(cls, *args, **kwargs):
        """An individual instantiation function."""
        raise NotImplementedError(str(cls))

    @classmethod
    def get_subclasses(cls):
        """Getting the subclasses. We should import them first."""
        from .repository import Repository  # noqa
        from .pull_request import PullRequest  # noqa
        from .issue_comment import IssueComment  # noqa
        return PyGithubObjectWrapper.__subclasses__()

    @classmethod
    def wrap(cls, pygithub_object, raise_when_not_found=True):
        """Detecting the related local class and wrapping the pygithub object
        e.g. PyGithubObjectWrapper.wrap(Repository(full_name="octocat/Hello-World")) -->
                Repository(PyGithubObjectWrapper) | Repository(full_name="octocat/Hello-World").
            @param pygithub_object: `GithubObject` The pygithub object to wrap.
            @keyword raise_when_not_found: `bool` Whether to raise exception if
                                           no such wrapper found or just return the input.
        """
        for cls in cls.get_subclasses():
            for pgc in (cls.PyGithubClass if isinstance(cls.PyGithubClass, (list, tuple)) else (cls.PyGithubClass, )):
                if pgc == getattr(pygithub_object, '__class__', None):
                    return cls(pygithub_object)
        if raise_when_not_found:
            raise NoWrapperForPyGithubObjectException(pygithub_object)
        return pygithub_object  # Sometimes it could be a primitive type like `int`

    def _convert_to_local(self, value):
        """Converting the value to local class"""
        if isinstance(value, (MethodType, FunctionType)):
            def wrapper(*args, **kwargs):
                return self._convert_to_local(value(*args, **kwargs))
            return wrapper
        elif isinstance(value, PaginatedList):
            def iterator():
                for pygithub_object in value:
                    yield self.wrap(pygithub_object, raise_when_not_found=False)
            return iterator()
        return self.wrap(value, raise_when_not_found=False)

    def __getattr__(self, name):
        retval = getattr(self.api, name)
        return self._convert_to_local(retval)

    @property
    def api(self):
        return self._pygithub_object
