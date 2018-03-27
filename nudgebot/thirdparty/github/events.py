"""This module includes the github Events and The Github event factory."""
from github.IssueComment import IssueComment as PyGithubIssueEvent

from nudgebot.settings import CurrnetProject
from nudgebot.thirdparty.base import Event, EventsFactory
from nudgebot.thirdparty.github.issue import Issue
from nudgebot.thirdparty.github.base import Github
from nudgebot.thirdparty.github.pull_request import PullRequest
from nudgebot.thirdparty.github.repository import Repository


class GithubEventBase(Event):
    """A base class for Github event."""

    def __init__(self, repository: Repository, payload: dict):
        assert isinstance(repository, Repository)
        assert isinstance(payload, dict)
        self._repository = Repository
        self._payload = payload

    @property
    def id(self):
        return self._payload['id']

    @property
    def data(self):
        return self._payload


class RepositoryEvent(GithubEventBase):
    PartyScopes = [Repository]


class IssueEvent(GithubEventBase):
    PartyScopes = [Repository, Issue]


class PullRequestEvent(GithubEventBase):
    PartyScopes = [Repository, PullRequest]


class GithubEventsFactory(EventsFactory):
    Party = Github()

    def _fetch_type_and_number(self, payload: dict):
        """Fetch the type of the event and the number, the number is None in case that is not pull request or issue event.

        @param payload: `dict` The event payload.
        """
        pr = payload.get('pull_request')
        if pr:
            return PullRequestEvent, pr.get('number')
        issue = payload.get('issue')
        if issue:
            if issue.get('pull_request'):
                return PullRequestEvent, issue.get('number')
            return IssueEvent, issue.get('number')
        return RepositoryEvent, None

    def grab_new_data(self) -> dict:
        data = {}
        for repo in self.Party.repositories:
            for event in repo.get_all_events():
                is_this_me = event.actor.login == CurrnetProject().config.credentials.github.username
                if (event.id in self._delivered_events_ids or is_this_me):
                    break
                if isinstance(event, PyGithubIssueEvent):
                    payload = event.raw_data
                else:
                    payload = event.payload
                # Fill some required fields that could be missing in the events API but
                # coming with webhooks for some reason
                payload['organization'] = repo.organization
                payload['sender'] = {'login': event.actor.login}
                payload['repository'] = payload.get('repository', {'name': repo.name})
                data[event.id] = payload
        return data

    def build_events(self, data: dict) -> list:
        events = []
        for _, payload in data.items():
            event_klass, number = self._fetch_type_and_number(data)
            payload['number'] = number
            events.append(event_klass(payload))
        return events
