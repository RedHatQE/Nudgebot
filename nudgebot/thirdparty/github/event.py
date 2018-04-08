from cached_property import cached_property
from github.Event import Event as PyGithubEvent
from github.IssueEvent import IssueEvent as PyGithubIssueEvent
from github.GithubException import UnknownObjectException

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper
from nudgebot.thirdparty.base import APIclass

from nudgebot.utils import getnode
from nudgebot.thirdparty.github.organization import Organization
from nudgebot.thirdparty.github.repository import Repository


class Event(PyGithubObjectWrapper, APIclass):
    PyGithubClass = (PyGithubEvent, PyGithubIssueEvent)

    @cached_property
    def artifacts(self) -> dict:
        """
        Building the object that associated with this event.

        @rtype: `dict` of `PyGithubObjectWrapper`
        """
        data = self.raw_data
        artifacts = {}

        if isinstance(self.pygithub_object, PyGithubIssueEvent):
            data['type'] = 'IssuesEvent'
        artifacts['org'] = next(parent for parent in self.parents if isinstance(parent, Organization))
        artifacts['repo'] = next(parent for parent in self.parents if isinstance(parent, Repository))
        # Fetching actor
        actor = data.get('actor')
        if actor:
            artifacts['actor'] = self.client.get_user(actor['login'])
        # Fetching issue
        issue_data = getnode(data, ['payload', 'issue']) or data.get('issue')
        if issue_data:
            number = issue_data['number']
            try:
                issue = artifacts['repo'].get_pull(number)
            except UnknownObjectException:
                issue = artifacts['repo'].get_issue(number)
            artifacts['issue'] = issue
        # Fetching comment
        comment_data = getnode(data, ['payload', 'comment'])
        if comment_data:
            try:
                artifacts['comment'] = issue.get_comment(comment_data['id'])
            except UnknownObjectException:
                pass  # Happens when the comment is deleted.

        return artifacts
