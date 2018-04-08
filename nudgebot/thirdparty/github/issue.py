"""Github issue."""
from cached_property import cached_property
from github.Issue import Issue as PyGithubIssue

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper, GithubScope
from nudgebot.thirdparty.github.repository import Repository


class Issue(PyGithubObjectWrapper, GithubScope):
    """Github issue."""

    Parents = [Repository]
    PyGithubClass = PyGithubIssue
    primary_keys = ['organization', 'repository', 'issue_number']

    @classmethod
    def instantiate(cls, repository, number):
        assert isinstance(repository, Repository)
        assert isinstance(number, int)
        return cls(repository.api.get_pull(number), repository)

    @classmethod
    def init_by_keys(cls, **query):
        return cls.instantiate(Repository.init_by_keys(**query), query.get('issue_number'))

    @cached_property
    def query(self)->dict:
        return {
            'organization': self.repository.organization_name,
            'repository': self.repository.name,
            'issue_number': self.number
        }

    @property
    def issue_number(self):
        return self.number
