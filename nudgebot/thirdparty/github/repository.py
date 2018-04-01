from cached_property import cached_property

from github.GithubException import UnknownObjectException
from github.Repository import Repository as PyGithubRepository

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper, Github, GithubScope


class Repository(PyGithubObjectWrapper, GithubScope):
    Party = Github()
    PyGithubClass = PyGithubRepository
    primary_keys = ['organization', 'name']

    @classmethod
    def instantiate(cls, organization, name):
        try:
            org = cls.Party.client.get_organization(organization)
        except UnknownObjectException:
            org = cls.Party.client.get_user(organization)
        return cls(org.get_repo(name))

    @cached_property
    def organization_name(self):
        return getattr(self.organization, 'name', getattr(self.owner, 'login'))

    @cached_property
    def parent(self):
        return

    @classmethod
    def all(cls):
        for repo in cls.Party.repositories:
            yield repo

    @classmethod
    def init_by_keys(cls, **kwargs):
        return cls.instantiate(organization=kwargs.get('organization'), name=kwargs.get('name'))

    @cached_property
    def query(self)->dict:
        return {
            'organization': self.organization_name,
            'name': self.name
        }
