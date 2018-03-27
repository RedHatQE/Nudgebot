"""Github issue."""
from github.Issue import Issue as PyGithubIssue

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper, Github
from nudgebot.thirdparty.github.repository import Repository
from nudgebot.thirdparty.base import PartyScope


class Issue(PyGithubObjectWrapper, PartyScope):
    """Github issue."""

    Party = Github()
    PyGithubClass = PyGithubIssue
    primary_keys = ['organization', 'repository', 'number']

    @classmethod
    def instantiate(cls, repository, number):  # noqa
        assert isinstance(repository, Repository)
        assert isinstance(number, int)
        pygithub_object = repository.api.get_issue(number)
        return cls(pygithub_object)

    @classmethod
    def init_by_keys(cls, **kwargs):  # noqa
        assert kwargs.keys() == cls.primary_keys
        repository = Repository.init_by_keys(
            organization=kwargs.get('organization'), name=kwargs.get('repository'))
        return cls.instantiate(repository, kwargs.get('number'))
