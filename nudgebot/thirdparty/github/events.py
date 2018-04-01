"""This module includes the github Events and The Github event factory."""
from github.IssueEvent import IssueEvent as PyGithubIssueEvent

from nudgebot.thirdparty.base import Event, EventsFactory
from nudgebot.thirdparty.github.issue import Issue
from nudgebot.thirdparty.github.base import Github
from nudgebot.thirdparty.github.pull_request import PullRequest
from nudgebot.thirdparty.github.repository import Repository


class GithubEventBase(Event):
    """A base class for Github event."""
    Party = Github()

    def __init__(self, payload: dict):
        assert isinstance(payload, dict)
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
    _max_recent_check = 100  # Checking for at most <_max_recent_check> recent events and then break TODO: parameterize

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

    def build_events(self) -> dict:
        events = []
        event_getter_names = ('get_events', 'get_issues_events')
        for repo in self.Party.repositories:
            for getter in event_getter_names:
                i = 0
                for event in getattr(repo, getter)():
                    # We assume that the most recent event are in the top of the timeline in github, so if the first we receive
                    # is already in the buffer or delivered, we assume that there are no new events.
                    hsh = GithubEventBase.hash_by_id(event.id)
                    if hsh in map(lambda e: e.hash, self._events_buffer):
                        self.logger.debug('Event "{}" already in the buffer. dismissing...'.format(hsh))
                        break
                    if hsh in self._dilivered_events_stack:
                        self.logger.debug('Event "{}" already delivered. dismissing...'.format(hsh))
                        break
                    if i >= self._max_recent_check:
                        self.logger.debug('Max recent checks exceeded for getter "{}", events collected: {}...'.format(
                            getter, len(events), hsh))
                        break
                    # TODO: Check whether the following is necessary...
                    # elif event.actor.login == CurrentProject().config.credentials.github.username:
                    #     continue
                    if isinstance(event.api, PyGithubIssueEvent):
                        payload = event.raw_data
                    else:
                        payload = event.payload
                    # Fill some required fields that could be missing in the timeline API but
                    # coming with the webhooks for some reason
                    payload['id'] = event.id
                    payload['organization'] = getattr(repo.organization, 'name', repo.owner.login)
                    payload['sender'] = {'login': event.actor.login}
                    payload['repository'] = payload.get('repository', {'name': repo.name})
                    event_klass, number = self._fetch_type_and_number(payload)
                    if event_klass is RepositoryEvent:
                        payload['name'] = payload['repository']['name']
                    else:
                        payload['name'] = payload['repository'] = payload['repository']['name']
                        payload['number'] = number
                    #
                    events.append(event_klass(payload))
                    # since we have number of getters we want to collect only (1 / len(event_getter_names))
                    # from each getter so we are adding the following to `i`
                    i += 1.0 * len(event_getter_names)
        if events:
            self.logger.info('Building events...')
        return events
