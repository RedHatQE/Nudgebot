from github.IssueEvent import IssueEvent as PyGithubIssueEvent

from nudgebot.thirdparty.github import PyGithubObjectWrapper


class Event(PyGithubObjectWrapper):
    PyGithubClass = PyGithubIssueEvent
