from github.GithubException import UnknownObjectException
from github.Repository import Repository as PyGithubRepository

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper
from nudgebot.thirdparty.base import PartyScope


class Repository(PyGithubObjectWrapper, PartyScope):
    PyGithubClass = PyGithubRepository
    primary_keys = ['organization', 'name']

    @classmethod
    def instantiate(cls, organization, name):
        try:
            org = cls.Party.client.get_organization(organization)
        except UnknownObjectException:
            org = cls.Party.client.get_user(organization)
        return cls(org.get_repo(name))

    @classmethod
    def init_by_keys(cls, **kwargs):
        return cls.instantiate(organization=kwargs.get('organization'), name=kwargs.get('name'))

    def get_all_events(self):
        """Getting both issue events and events sorted by creation datetime.
        @rtype: `list` of `Event`
        """
        events = list(self.get_events())
        issue_events = list(self.get_issues_events())
        return sorted(events + issue_events, key=lambda e: e.created_at)
