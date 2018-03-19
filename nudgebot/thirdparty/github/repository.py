from github.GithubException import UnknownObjectException
from github.Repository import Repository as PyGithubRepository

from nudgebot.thirdparty.github import PyGithubObjectWrapper, github_client


class Repository(PyGithubObjectWrapper):
    PyGithubClass = PyGithubRepository

    @classmethod
    def instantiate(cls, organization, name):
        try:
            org = github_client.get_organization(organization)
        except UnknownObjectException:
            org = github_client.get_user(organization)
        return cls(org.get_repo(name))

    def get_all_events(self):
        """Getting both issue events and events sorted by creation datetime.
        @rtype: `list` of `Event`
        """
        events = list(self.get_events())
        issue_events = list(self.get_issues_events())
        return sorted(events + issue_events, key=lambda e: e.created_at)
