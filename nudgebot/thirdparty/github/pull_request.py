"""Github pull request."""
from cached_property import cached_property
from github.PullRequest import PullRequest as PyGithubPullRequest

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper, Github, GithubScope
from nudgebot.thirdparty.github.repository import Repository


class PullRequest(PyGithubObjectWrapper, GithubScope):
    """Github pull request."""

    Party = Github()
    Parent = Repository
    PyGithubClass = PyGithubPullRequest
    primary_keys = ['organization', 'repository', 'number']

    @classmethod
    def instantiate(cls, repository, number):  # noqa
        assert isinstance(repository, Repository)
        assert isinstance(number, int)
        pygithub_object = repository.api.get_pull(number)
        instance = cls(pygithub_object)
        instance.repository = repository
        return instance

    @cached_property
    def parent(self):
        return self.repository

    @classmethod
    def all(cls):
        for repo in cls.Parent.all():
            for pr in repo.get_pulls():
                pr.repository = repo
                yield pr

    @classmethod
    def init_by_keys(cls, **kwargs):  # noqa
        assert list(kwargs.keys()) == list(cls.primary_keys)
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
