from github.IssueComment import IssueComment as PyGithubIssueComment

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper
from nudgebot.thirdparty.base import APIclass


class IssueComment(PyGithubObjectWrapper, APIclass):
    PyGithubClass = PyGithubIssueComment
