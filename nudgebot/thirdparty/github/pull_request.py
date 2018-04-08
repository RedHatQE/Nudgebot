"""Github pull request."""
from cached_property import cached_property
from github.PullRequest import PullRequest as PyGithubPullRequest

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper, GithubScope
from nudgebot.thirdparty.github.repository import Repository
from nudgebot.thirdparty.github.user import User
from nudgebot.thirdparty.github.review_comments_thread import ReviewCommentsThread


class PullRequest(PyGithubObjectWrapper, GithubScope):
    """Github pull request."""

    Parents = [Repository]
    PyGithubClass = PyGithubPullRequest
    primary_keys = ['organization', 'repository', 'issue_number']

    @classmethod
    def instantiate(cls, repository, number):
        assert isinstance(repository, Repository)
        assert isinstance(number, int)
        return cls(repository.api.get_pull(number), repository)

    @classmethod
    def init_by_keys(cls, **query):
        return cls.instantiate(Repository.init_by_keys(**query), query.get('issue_number'))

    @cached_property
    def query(self)->dict:
        return {
            'organization': self.repository.organization_name,
            'repository': self.repository.name,
            'issue_number': self.number
        }

    @property
    def issue_number(self):
        return self.number

    def get_review_comments_threads(self):
        return ReviewCommentsThread.fetch_threads(self)

    def add_reviewers(self, reviewers):
        """Adding the reviewers to the pull request - this is workaround until
        https://github.com/PyGithub/PyGithub/pull/598 is merged.
        :calls: `POST /repos/:owner/:repo/pulls/:number/requested_reviewers
                <https://developer.github.com/v3/pulls/review_requests/>`_
        :param reviewers: (logins) list of strings or User
        """
        status, _, _ = self._pygithub_object._requester.requestJson(
            "POST",
            self.url + "/requested_reviewers",
            input={'reviewers': [reviewer.login if isinstance(reviewer, User) else reviewer for reviewer in reviewers]},
            headers={'Accept': 'application/vnd.github.thor-preview+json'}
        )
        return status == 201

    def remove_reviewers(self, reviewers):
        """Removing the reviewers from the pull request - this is workaround until
        https://github.com/PyGithub/PyGithub/pull/598 is merged.
        :calls: `DELETE /repos/:owner/:repo/pulls/:number/requested_reviewers
                <https://developer.github.com/v3/pulls/review_requests/>`_
        :param reviewers: (logins) list of strings
        """
        status, _, _ = self._github_obj._requester.requestJson(
            "DELETE",
            self.url + "/requested_reviewers",
            input={'reviewers': [rev.login if isinstance(rev, User) else rev for rev in reviewers]},
            headers={'Accept': 'application/vnd.github.thor-preview+json'}
        )
        return status == 200
