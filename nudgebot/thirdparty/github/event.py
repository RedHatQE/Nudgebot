from cached_property import cached_property
from github.Event import Event as PyGithubEvent
from github.IssueEvent import IssueEvent as PyGithubIssueEvent

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper
from nudgebot.thirdparty.base import APIclass


class Event(PyGithubObjectWrapper, APIclass):
    PyGithubClass = (PyGithubEvent, PyGithubIssueEvent)

    @cached_property
    def type(self):
        getattr(self.api, 'type', 'IssueEvent')
