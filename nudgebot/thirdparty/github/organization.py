from cached_property import cached_property

from github.Organization import Organization as PyGithubOrganization

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper, GithubScope


class Organization(PyGithubObjectWrapper, GithubScope):
    PyGithubClass = PyGithubOrganization
    primary_keys = ['organization']

    @classmethod
    def instantiate(cls, name):
        return cls(cls.Endpoint.client.get_organization(name))

    @classmethod
    def init_by_keys(cls, **query):
        return cls.instantiate(name=query.get('organization'))

    @cached_property
    def query(self)->dict:
        return {
            'organization': self.name,
        }
