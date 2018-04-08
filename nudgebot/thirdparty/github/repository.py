from cached_property import cached_property

from github.Repository import Repository as PyGithubRepository
from github.GithubException import UnknownObjectException

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper, GithubScope
from nudgebot.thirdparty.github.organization import Organization
from nudgebot.thirdparty.github.user import User


class Repository(PyGithubObjectWrapper, GithubScope):
    PyGithubClass = PyGithubRepository
    Parents = [Organization, User]
    primary_keys = ['organization', 'repository']

    @classmethod
    def instantiate(cls, organization_or_user, name):
        assert isinstance(organization_or_user, (Organization, User))
        return cls(organization_or_user.api.get_repo(name), organization_or_user)

    @classmethod
    def init_by_keys(cls, **query):
        try:
            organization_or_user = Organization.init_by_keys(organization=query.get('organization'))
        except UnknownObjectException:
            organization_or_user = User.instantiate(query.get('organization'))

        return cls.instantiate(organization_or_user=organization_or_user, name=query.get('repository'))

    @cached_property
    def query(self) -> dict:
        return {
            'organization': self.organization_name,
            'repository': self.name
        }

    @cached_property
    def organization_name(self):
        return getattr(self.organization, 'name', getattr(self.owner, 'login'))
