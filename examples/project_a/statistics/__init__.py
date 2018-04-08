import json
import requests

from cached_property import cached_property

from nudgebot.statistics.base import statistic
from nudgebot.statistics.github import PullRequestStatistics, RepositoryStatistics, IssueStatistics
from nudgebot.settings import CurrentProject
import re


# Create you statistics here

# In this file we create the statistics that we would like to collect from each scope.
# These statistics will used to define the tasks.


class MyPrStatistics(PullRequestStatistics):
    """In this statistics class we collect all the statistics that related to pull request."""
    key = 'my_pr_stats'  # This key will be used to access this statistics in the tasks

    # We decorate this getter with `statistic` decorator to indicate that this
    # is a statistic that we would like to collect and save
    @statistic
    def number_of_commits(self):
        return self.party_scope.commits

    @statistic
    def number(self):
        return self.party_scope.issue_number

    @statistic
    def title(self):
        return self.party_scope.title

    @statistic
    def owner(self):
        return self.party_scope.user.login

    @statistic
    def description(self):
        return self.party_scope.body or ''

    @statistic
    def state(self):
        return self.party_scope.state

    @statistic
    def test_results(self):
        auth = (CurrentProject().config.credentials.github.username, CurrentProject().config.credentials.github.password)
        tests = json.loads(requests.get(self.party_scope.raw_data['statuses_url'], auth=auth).content)
        out = {}
        for test in tests:
            out[test['context']] = test['description']
        return out

    @statistic
    def last_code_update(self):
        return str(list(self.party_scope.get_commits()).pop().last_modified)

    @statistic
    def last_update(self):
        return str(self.party_scope.updated_at)

    @statistic
    def total_comments(self):
        return self.party_scope.comments

    @statistic
    def title_tags(self):
        return re.findall('\[ *([\w\d_\-]+) *\]', self.title())

    @statistic
    def reviewers(self):
        return list(set(
            [review.user.login for review in self.party_scope.get_reviews()] +
            [review_request.login for review_request in self.party_scope.get_reviewer_requests()]
        ))


class MyIssueStatistics(IssueStatistics):
    """In this statistics class we collect all the statistics that related to issues."""
    @statistic
    def description(self):
        return self.party_scope.body or ''

    @statistic
    def comments(self):
        return self.party_scope.comments


class MyRepositoryStatistics(RepositoryStatistics):
    """In this statistics class we collect all the statistics that related to repository."""
    key = 'my_repo_stats'  # This key will be used to access this statistics in the tasks

    @cached_property
    def all_pull_requests(self):
        return list(self.party_scope.get_pulls(state='open'))

    @statistic
    def name(self):
        return self.party_scope.name

    @statistic
    def number_of_open_pull_requests(self):
        return len(self.all_pull_requests)

    @statistic
    def forks_count(self):
        return self.party_scope.forks_count
