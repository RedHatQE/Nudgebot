from nudgebot.statistics.base import Statistics
from nudgebot.thirdparty.github.base import Github
from nudgebot.thirdparty.github.repository import Repository
from nudgebot.thirdparty.github.issue import Issue
from nudgebot.thirdparty.github.pull_request import PullRequest


class GithubStatisticsBase(Statistics):
    Endpoint = Github()


class RepositoryStatistics(GithubStatisticsBase):
    EndpointScope = Repository
    COLLECTION_NAME = 'github_repository'
    key = COLLECTION_NAME


class IssueStatistics(GithubStatisticsBase):
    EndpointScope = Issue
    COLLECTION_NAME = 'github_issue'
    key = COLLECTION_NAME


class PullRequestStatistics(GithubStatisticsBase):
    EndpointScope = PullRequest
    COLLECTION_NAME = 'github_pull_request'
    key = COLLECTION_NAME
