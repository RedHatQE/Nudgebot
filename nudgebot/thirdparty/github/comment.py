import re

from cached_property import cached_property
from github.IssueComment import IssueComment as PyGithubIssueComment
from github.PullRequestComment import PullRequestComment as PyGithubPullRequestComment
from github.GithubException import UnknownObjectException

from nudgebot.thirdparty.base import APIclass
from nudgebot.thirdparty.github.base import PyGithubObjectWrapper


class Comment(PyGithubObjectWrapper, APIclass):
    PyGithubClass = (PyGithubIssueComment, PyGithubPullRequestComment)

    @cached_property
    def mentioned_users(self):
        """
        Return a list of the mentioned users in this comment.
            e.g. '@octocat hello world!' --> [NamedUser(login="octocat")]

        @rtype: (`list` of `User`) The list of the mentioned users.
        """
        mentioned_users = []
        for login in set(re.findall(r' @([\-\w\d_]+)', ' ' + self.body)):
            try:
                mentioned_users.append(self.Party.get_user(login))
            except UnknownObjectException:
                pass
        return mentioned_users
