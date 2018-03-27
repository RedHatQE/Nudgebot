"""Github pull request."""
from github.PullRequest import PullRequest as PyGithubPullRequest

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper, Github
from nudgebot.thirdparty.github.repository import Repository
from nudgebot.thirdparty.base import PartyScope


class PullRequest(PyGithubObjectWrapper, PartyScope):
    """Github pull request."""

    Party = Github()
    PyGithubClass = PyGithubPullRequest
    primary_keys = ['organization', 'repository', 'number']

    @classmethod
    def instantiate(cls, repository, number):  # noqa
        assert isinstance(repository, Repository)
        assert isinstance(number, int)
        pygithub_object = repository.api.get_pull(number)
        return cls(pygithub_object)

    @classmethod
    def init_by_keys(cls, **kwargs):  # noqa
        assert list(kwargs.keys()) == list(cls.primary_keys)
        repository = Repository.init_by_keys(
            organization=kwargs.get('organization'), name=kwargs.get('repository'))
        return cls.instantiate(repository, kwargs.get('number'))