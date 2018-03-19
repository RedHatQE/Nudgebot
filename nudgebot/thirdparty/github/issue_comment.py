from github.IssueComment import IssueComment as PyGithubIssueComment

from nudgebot.thirdparty.github import PyGithubObjectWrapper


class IssueComment(PyGithubObjectWrapper):
    PyGithubClass = PyGithubIssueComment
