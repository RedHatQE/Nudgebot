from nudgebot.statistics.base import statistic  # noqa
from nudgebot.statistics.github import RepositoryStatistics, IssueStatistics, PullRequestStatistics  # noqa

# Create you statistics here

# In this file we create the statistics that we would like to collect from each scope.
# These statistics will used to define the tasks.


class MyPrStatistics(PullRequestStatistics):
    """In this statistics class we collect all the statistics that related to pull request."""
    key = 'my_pr_stats'  # This key will be used to access this statistics in the tasks

    # We decorate this getter with `statistic` decorator to indicate that this
    # is a statistic that we would like to collect and save
    @statistic
    def total_number_of_comments(self):
        return self.party_scope.comments
