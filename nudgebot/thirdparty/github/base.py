"""Base classes for Github third party Endpoint."""
from types import FunctionType, MethodType, GeneratorType

from cached_property import cached_property
from github import Github as GithubClient
from github.PaginatedList import PaginatedList
from github.GithubObject import GithubObject as PyGithubObject

from nudgebot.exceptions import NoWrapperForPyGithubObjectException
from nudgebot.thirdparty.base import Endpoint, EndpointScope, APIclass


class Github(Endpoint):
    """The Github Endpoint."""

    key = 'github'

    @cached_property
    def repositories(self):
        """Return the repositories object according to the github configuration in the config file."""
        from nudgebot.thirdparty.github.repository import Repository
        repositories = []
        for repodata in self.config.repositories:
            repositories.append(Repository.init_by_keys(organization=repodata['organization'], repository=repodata['name']))
        return repositories

    @cached_property
    def client(self):  # noqa
        return GithubClient(self.credentials.get('username'), self.credentials.get('password'),
                            client_id=self.credentials.client_id, client_secret=self.credentials.client_secret,
                            timeout=60)


class GithubScope(EndpointScope):
    """A Github endpoint scope"""
    pass


class GithubObject(APIclass):
    def __init__(self, parent=None):
        """
        @keyword parent: `GithubObject` The parent object.
        """
        assert parent is None or isinstance(parent, GithubObject)
        self._parent = None
        if parent is not None:
            self.set_parent(parent)

    def set_parent(self, parent):
        assert isinstance(parent, GithubObject), \
            f'Parent must be an instance of {GithubObject.__name__}, not {getattr(type(parent), "__name__", type(parent))}'
        self._parent = parent

    @property
    def parent(self):
        return self._parent

    @property
    def parents(self):
        parents = []
        node = self.parent
        while node:
            parents.append(node)
            node = node.parent
        return parents

    @property
    def top_parent(self):
        parents = self.parents
        return (parents[-1] if parents else None)


class PyGithubObjectWrapper(GithubObject):
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
    Should be defined in subclass:
        * PyGithubClass: `PyGithubObject` The pygithub object that the class wraps.
    """

    Endpoint = Github()
    PyGithubClass = PyGithubObject  # Overwrite this!

    def __init__(self, pygithub_object, parent=None):
        """
        @param pygithub_object: `PyGithubObject` The wrapped pygithub object.
        @keyword parent: `PyGithubObjectWrapper` The parent object.
        """
        assert (
            isinstance(pygithub_object, self.PyGithubClass) or
            isinstance(self.PyGithubClass, (tuple, list)) and
            all(isinstance(pygithub_object, cls) for cls in self.PyGithubClass)
        )
        GithubObject.__init__(self, parent)
        self._pygithub_object = pygithub_object

    def __repr__(self):
        return '<{}({}) | {}>'.format(
            self.__class__.__name__, PyGithubObjectWrapper.__name__, self._pygithub_object.__repr__())

    @staticmethod
    def _single_wrap(pygithub_object, parent=None, raise_when_not_found=True):
        """
        Detect the related local class and wrapping the pygithub object.

        e.g. PyGithubObjectWrapper._single_wrap(Repository(full_name="octocat/Hello-World")) -->
                gitwise.Repository(full_name="octocat/Hello-World").
        @param pygithub_object: `PyGithubObject` The pygithub object to _single_wrap.
        @keyword parent: `PyGithubObjectWrapper` The parent object.
        @keyword raise_when_not_found: `bool` Whether to raise exception if
                                       no such wrapper found or just return the input.
        """
        for cls in PyGithubObjectWrapper.get_subclasses():
            for pgc in (cls.PyGithubClass if isinstance(cls.PyGithubClass, (list, tuple)) else (cls.PyGithubClass, )):
                if pgc == getattr(pygithub_object, '__class__', None):
                    return cls(pygithub_object, parent=parent)
        if raise_when_not_found:
            raise NoWrapperForPyGithubObjectException(pygithub_object)
        return pygithub_object  # Sometimes it could be a primitive type like `int`

    @classmethod
    def get_subclasses(cls):
        """Get subclasses."""
        from nudgebot.thirdparty.github import organization  # noqa
        from nudgebot.thirdparty.github import repository  # noqa
        from nudgebot.thirdparty.github import pull_request  # noqa
        from nudgebot.thirdparty.github import issue  # noqa
        from nudgebot.thirdparty.github import comment  # noqa
        from nudgebot.thirdparty.github import event  # noqa
        from nudgebot.thirdparty.github import user  # noqa
        return PyGithubObjectWrapper.__subclasses__()

    @classmethod
    def instantiate(cls, *args, **kwargs):
        """Instantiate an individual instantiation function."""
        raise NotImplementedError(str(cls))

    @classmethod
    def wrap(cls, value, parent=None, raise_when_not_found=True):
        """
        Convert the value to local class.

        In case that the object is coming in as a plural or as non-cached, It's performing a nested wrapping.
        """
        if isinstance(value, (MethodType, FunctionType)):
            # Non-cached - wrapping inside a getter
            def getter(*args, **kwargs):
                return cls.wrap(value(*args, **kwargs), parent=parent, raise_when_not_found=raise_when_not_found)
            return getter
        elif isinstance(value, (PaginatedList, GeneratorType)):
            # A generator
            def iterator():
                for pygithub_object in value:
                    yield cls.wrap(pygithub_object, parent=parent, raise_when_not_found=raise_when_not_found)
            return iterator()
        elif isinstance(value, (list, tuple, set)):
            # A sequence
            return type(value)([cls.wrap(v, raise_when_not_found=raise_when_not_found) for v in value])
        elif isinstance(value, dict):
            # A mapping
            return {
                cls.wrap(k, raise_when_not_found=raise_when_not_found):
                cls.wrap(v, raise_when_not_found=raise_when_not_found)
                for k, v in value.items()
            }
        # Probably some other primitive type like `int`, `str`, etc.
        return cls._single_wrap(value, parent=parent, raise_when_not_found=raise_when_not_found)

    def __getattr__(self, name):
        return self.wrap(getattr(self.pygithub_object, name), parent=self, raise_when_not_found=False)

    def set_parent(self, parent):
        assert isinstance(parent, PyGithubObjectWrapper), \
            f'Parent must be an instance of {PyGithubObjectWrapper.__name__}, ' \
            f'not {getattr(type(parent), "__name__", type(parent))}'
        self._parent = parent

    @property
    def pygithub_object(self):
        """Return the pygithub object."""
        return self._pygithub_object

    @property
    def parent(self):
        return self._parent

    @property
    def api(self):
        """Return the pygithub object."""
        return self._pygithub_object
