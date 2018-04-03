import os
import re
from random import choice

from jinja2 import Template
from celery.schedules import crontab
from nudgebot.tasks.base import ConditionalTask
from nudgebot.thirdparty.github.base import Github
from nudgebot.thirdparty.github.pull_request import PullRequest
from nudgebot.thirdparty.github.repository import Repository
from nudgebot.utils import send_email
from nudgebot.tasks.base import PeriodicTask
from nudgebot.thirdparty.irc.base import IRCparty
from nudgebot.thirdparty.irc.events import MessageMentionedMeEvent
from nudgebot.thirdparty.irc.message import Message
from nudgebot.settings import CurrentProject
from nudgebot.thirdparty.github.user import User


# Create your tasks here


class SetReviewerWhenMovedToRFR(ConditionalTask):
    """This task adding a reviewer once the title add an '[RFR]' tag"""

    Party = Github()
    PartyScopes = [Repository, PullRequest]
    NAME = 'SetReviewerWhenMovedToRFR'

    @property
    def condition(self):
        return bool(['RFR' in tt.upper() for tt in self.statistics.my_pr_stats.title_tags])

    def get_data(self):

        users = CurrentProject().config.users
        repos_data = next(repo for repo in CurrentProject().config.config.github.repositories
                          if repo.name == self.statistics.my_repo_stats.name)
        maintainers = repos_data.maintainers
        reviewer = choice(maintainers)
        owner = self.statistics.my_pr_stats.owner
        reviewer_contact = next(user for user in users if user.github_login == reviewer)
        owner_contact = ([user for user in users if user.github_login == owner] or [owner]).pop()
        pr_number = self.statistics.my_pr_stats.number
        return pr_number, owner_contact, reviewer_contact

    def get_artifacts(self):
        return self.statistics.my_pr_stats.title_tags

    def run(self):
        pr_number, owner_contact, reviewer_contact = self.get_data()
        if not self.statistics.my_pr_stats.reviewers:
            for channel in CurrentProject().config.config.irc.channels:
                IRCparty().client.msg(
                    channel,
                    f'{owner_contact} PR#{pr_number} of {owner_contact} moved status '
                    f'to `Ready for review`, setting {reviewer_contact.irc_nick} as reviewer'
                )
            reviewer_user = User.instantiate(reviewer_contact.github_login)
            self.party_scopes[PullRequest].add_reviewers(reviewer_user)


class AlertOnMentionedUser(ConditionalTask):
    """This task prompt the user in IRC once it mentioned in some pull request."""

    Party = Github()
    PartyScopes = [Repository, PullRequest]
    NAME = 'AlertOnMentionedUser'

    @property
    def mentioned_users_and_actor(self):
        if not self.event or not self.event.data.get('comment'):
            return [], ''
        actor = self.event.data['sender']['login']
        body = self.event.data['comment']['body']
        mentioned = re.findall('@([\w\d_\-]+)', body)
        if mentioned:
            return list(set(mentioned)), actor
        return [], actor

    def get_artifacts(self):
        return self.event.data['id']

    @property
    def condition(self):
        return bool(self.mentioned_users_and_actor[0])

    def run(self):
        mentioned, actor = self.mentioned_users_and_actor
        IRCparty().client.msg(
            '##bot-testing', f'{actor} has been '
            f'mentioned {mentioned} in PR#{self.statistics.my_pr_stats.number} :-)'
        )


class IRCAnswerQuestion(ConditionalTask):
    """This task answer once some send message to the bot in IRC."""

    Party = IRCparty()
    PartyScopes = [Message]
    NAME = 'IRCAnswerQuestion'
    RUN_ONCE = False

    @property
    def condition(self):
        return self.event and isinstance(self.event, MessageMentionedMeEvent)

    def run(self):
        me = self.Party.client.nick
        content = self.party_scopes[Message].content
        sender = self.party_scopes[Message].sender
        channel = self.party_scopes[Message].channel

        def answer(content):
            return self.Party.client.msg(channel.name, f'{sender}, {content}')

        if f'{me}, ping' == content:
            answer('pong')
        elif f'{me}, #pr' == content:
            answer(', '.join([
                f'{repo.name}: {repo.number_of_open_pull_requests}'
                for repo in self.all_statistics.github_repository
            ]))
        else:
            answer('options:')
            self.Party.client.msg(channel.name, '    #pr - Number of open pull requests per repository.')
            self.Party.client.msg(channel.name, '    ping - Get pong back.')


class DailyReport(PeriodicTask):
    """This task is a periodic task. It sends a report to the maintainers every day at 12:00AM."""

    NAME = 'DailyReport'
    CRONTAB = crontab(hour=12)

    def get_report(self):
        data = {}

        for pr_stats in self.all_statistics.github_pull_request:
            if pr_stats.repository not in data:
                data[pr_stats.repository] = {}
            data[pr_stats.repository][pr_stats.number] = pr_stats
            data[pr_stats.repository][pr_stats.number].update({
                'comments': pr_stats.total_comments,
                'commits': pr_stats.number_of_commits,
                'reviewers': pr_stats.reviewers
            })
        with open(os.path.join(os.path.dirname(__file__), 'daily_report.j2'), 'r') as t:
            template = Template(t.read())
        return template.render(data=data)

    def run(self):
        maintainers_emails = set()
        for repo_data in CurrentProject().config.config.github.repositories:
            for maintainer in repo_data.maintainers:
                for user_data in CurrentProject().config.users:
                    if user_data.github_login == maintainer:
                        maintainers_emails.add(user_data.email)

        send_email(CurrentProject().config.credentials.email.address, list(maintainers_emails),
                   'Daily report', self.get_report(), text_format='html')
