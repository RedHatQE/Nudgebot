from nudgebot.thirdparty.base import ScopesCollector
from nudgebot.thirdparty.github.base import Github


class GithubScopesCollector(ScopesCollector):
    def collect_all(self):
        party_scopes = []
        for repo in Github().repositories:
            party_scopes.append(repo)
            for pull_request in repo.get_pulls():
                pull_request.repository = repo
                party_scopes.append(pull_request)
            for issue in repo.get_issues():
                if not issue.pull_request:
                    issue.repository = repo
                    party_scopes.append(issue)
        return party_scopes
