import json
import re
import requests

from nudgebot.statistics.base import statistic
from nudgebot.statistics.github import PullRequestStatistics, RepositoryStatistics, IssueStatistics
from nudgebot.settings import CurrentProject
from nudgebot.utils import Age


# Create you statistics here

# In this file we create the statistics that we would like to collect from each scope.
# These statistics will used to define the tasks.


class MyPrStatistics(PullRequestStatistics):
    """In this statistics class we collect all the statistics that related to pull request."""
    key = 'my_pulls_statistics'  # This key will be used to access this statistics in the tasks

    # We decorate this getter with `statistic` decorator to indicate that this
    # is a statistic that we would like to collect and save
    @statistic
    def number_of_commits(self):
        return self.party_scope.commits

    @statistic
    def title(self):
        return self.party_scope.title

    @statistic
    def owner(self):
        return self.party_scope.user.login

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

    @last_code_update.pretty
    def last_code_update(last_code_update):  # noqa
        return Age(last_code_update).pretty + ' ago'

    @statistic
    def last_update(self):
        return str(self.party_scope.updated_at)

    @last_update.pretty
    def last_update(last_update):  # noqa
        return Age(last_update).pretty + ' ago'

    @statistic
    def total_comments(self):
        return self.party_scope.comments

    @statistic
    def title_tags(self):
        return re.findall('\[ *([\w\d_\-]+) *\]', self.title())

    @title_tags.pretty
    def title_tags(title_tags):  # noqa
        return ', '.join(title_tags)

    @statistic
    def reviewers(self):
        return list(set(
            [review.user.login for review in self.party_scope.get_reviews()] +
            [review_request.login for review_request in self.party_scope.get_reviewer_requests()]
        ))

    @reviewers.pretty
    def reviewers(reviewers):  # noqa
        return ', '.join(reviewers)


class MyIssueStatistics(IssueStatistics):
    """In this statistics class we collect all the statistics that related to issues."""
    @statistic
    def created_at(self):
        return self.party_scope.created_at

    @statistic
    def number_of_comments(self):
        return self.party_scope.comments

    @statistic
    def assignee(self):
        return getattr(self.party_scope.assignee, 'login', None)


class MyRepositoryStatistics(RepositoryStatistics):
    """In this statistics class we collect all the statistics that related to repository."""
    key = 'my_repo_statistics'  # This key will be used to access this statistics in the tasks

    @statistic
    def name(self):
        return self.party_scope.name

    @statistic
    def number_of_open_issues(self):
        return self.party_scope.open_issues_count

    @statistic
    def forks_count(self):
        return self.party_scope.forks_count
