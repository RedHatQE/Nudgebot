from github.PullRequest import PullRequest as PyGithubPullRequest

from nudgebot.thirdparty.github import PyGithubObjectWrapper
from nudgebot.thirdparty.github.repository import Repository


class PullRequest(PyGithubObjectWrapper):
    PyGithubClass = PyGithubPullRequest

    def instantiate(self, repository, number):
        assert isinstance(repository, Repository)
        assert isinstance(number, int)
        self._pygithub_object = repository.api.get_pull()
        return self
