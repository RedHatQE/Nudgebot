"""Github issue."""
from cached_property import cached_property
from github.Issue import Issue as PyGithubIssue

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper, Github, GithubScope
from nudgebot.thirdparty.github.repository import Repository


class Issue(PyGithubObjectWrapper, GithubScope):
    """Github issue."""

    Party = Github()
    Parent = Repository
    PyGithubClass = PyGithubIssue
    primary_keys = ['organization', 'repository', 'number']

    @classmethod
    def instantiate(cls, repository, number):  # noqa
        assert isinstance(repository, Repository)
        assert isinstance(number, int)
        pygithub_object = repository.api.get_issue(number)
        instance = cls(pygithub_object)
        instance.repository = repository
        return instance

    @cached_property
    def parent(self):
        return self.repository

    @classmethod
    def init_by_keys(cls, **kwargs):  # noqa
        assert list(kwargs.keys()) == cls.primary_keys
        repository = Repository.init_by_keys(
            organization=kwargs.get('organization'), name=kwargs.get('repository'))
        return cls.instantiate(repository, kwargs.get('number'))

    @cached_property
    def query(self)->dict:
        return {
            'organization': self.repository.organization_name,
            'repository': self.repository.name,
            'number': self.number
        }
