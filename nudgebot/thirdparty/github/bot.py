"""This module includes the github Events and The Github event factory."""
from github.GithubException import UnknownObjectException

from nudgebot.thirdparty.base import Event, EventsFactory, BotSlave, ScopesCollector
from nudgebot.thirdparty.github.base import Github
from nudgebot.thirdparty.github.repository import Repository
from nudgebot.thirdparty.github.pull_request import PullRequest
from nudgebot.thirdparty.github.issue import Issue


class GithubEventBase(Event):
    """A base class for Github event."""
    Party = Github()

    def __init__(self, data: dict):
        assert isinstance(data, dict)
        self._data = data

    @property
    def type(self):
        return self.data['type']

    @property
    def id(self):
        return self._data['id']

    @property
    def data(self):
        return self._data

# Events:


class RepositoryEvent(GithubEventBase):
    PartyScope = Repository


class IssueEvent(GithubEventBase):
    PartyScope = Issue


class PullRequestEvent(GithubEventBase):
    PartyScope = PullRequest

###


class GithubEventsFactory(EventsFactory):
    Party = Github()
    _max_recent_check = 100  # Checking for at most <_max_recent_check> recent events and then break TODO: parameterize

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
                    try:
                        data = event.raw_data
                    except UnknownObjectException:
                        break  # stale event
                    # Fill some required fields that could be missing in the timeline API but
                    data['organization'], data['repository'] = repo.owner.name or repo.owner.login, repo.name
                    data['sender'] = {'login': event.actor.login}
                    data['type'] = data.get('type') or data.get('event')
                    # Gathering facts
                    payload = data.get('payload') or {}
                    issue = payload.get('issue') or data.get('issue')
                    pull_request = (issue or {}).get('pull_request') or payload.get('pull_request')
                    # Classifying event:
                    if pull_request:
                        data['issue_number'] = int(pull_request['url'].split('/')[-1])
                        event_obj = PullRequestEvent(data)
                    elif issue:
                        data['issue_number'] = issue['number']
                        event_obj = IssueEvent(data)
                    else:
                        event_obj = RepositoryEvent(data)
                    #
                    events.append(event_obj)
                    # since we have number of getters we want to collect only (1 / len(event_getter_names))
                    # from each getter so we are adding the following to `i`
                    i += 1.0 * len(event_getter_names)
        return events


class GithubScopesCollector(ScopesCollector):
    Party = Github()

    def collect_all(self):
        party_scopes = []
        for repo in self.Party.repositories:
            party_scopes.append(repo)
            for pull_request in repo.get_pulls():
                pull_request.repository = repo
                party_scopes.append(pull_request)
            for issue in repo.get_issues():
                if not issue.pull_request:
                    issue.repository = repo
                    party_scopes.append(issue)
        return party_scopes


class GithubBot(BotSlave):
    Party = Github()
    EventsFactory = GithubEventsFactory()
    ScopeCollector = GithubScopesCollector()
