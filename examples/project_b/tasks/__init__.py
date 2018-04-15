from nudgebot.tasks import ConditionalTask, PeriodicTask  # noqa
from nudgebot.thirdparty.github.base import Github
from nudgebot.thirdparty.github.pull_request import PullRequest
from nudgebot.thirdparty.irc.base import IRCparty


class PromptWhenLargeNumberOfComments(ConditionalTask):
    """This task is prompting on IRC when there is a large number of comment in a pull request"""

    Party = Github()                            # The third party for this task is Github.
    PartyScope = PullRequest                    # The scope of this task is pull request.
    NAME = 'PromptWhenLargeNumberOfComments'    # The name of the task.
    PR_MAX_NUMBER_OF_COMMENTS = 10

    @property
    def condition(self):
        # Checking that total number of comment is greater than 10.
        return self.statistics.my_pr_stats.total_number_of_comments > self.PR_MAX_NUMBER_OF_COMMENTS

    def get_artifacts(self):
        return [str(self.statistics.my_pr_stats.total_number_of_comments)]

    def run(self):
        """Running the task"""
        IRCparty().client.msg(
            '##bot-testing',
            f'PR#{self.statistics.my_pr_stats.number} has more than {self.PR_MAX_NUMBER_OF_COMMENTS} comments! '
            f'({self.statistics.my_pr_stats.total_number_of_comments} comments)'
        )
