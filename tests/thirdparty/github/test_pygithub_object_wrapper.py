import pytest

from tests.fixtures import *  # noqa
from nudgebot.exceptions import NoWrapperForPyGithubObjectException


@pytest.fixture(scope='module')
def some_repo():
    from nudgebot.thirdparty.github.repository import Repository
    return Repository.instantiate('octocat', 'Hello-World')


@pytest.fixture(scope='module')
def some_pr(some_repo):
    return some_repo.get_pull(398)


def test_wrapping(new_project, some_repo, some_pr):
    """Tests that the class is really wrapping returned attributes"""
    from nudgebot.thirdparty.github.repository import Repository
    from nudgebot.thirdparty.github.pull_request import PullRequest
    from nudgebot.thirdparty.github.issue_comment import IssueComment
    assert isinstance(some_repo, Repository)
    all_prs = list(some_repo.get_pulls())
    assert all(isinstance(obj, PullRequest) for obj in all_prs)
    assert isinstance(some_pr, PullRequest)
    issue_comment = list(some_pr.get_issue_comments())
    assert all(isinstance(obj, IssueComment) for obj in issue_comment)


def test_wrapping_bad_objects(new_project, some_repo, some_pr):
    """Testing that the wrapper works correctly when passing primitive objects"""
    from nudgebot.thirdparty.github.base import PyGithubObjectWrapper
    for obj in (1, '2', object()):
        assert PyGithubObjectWrapper.wrap(obj, raise_when_not_found=False) == obj
        with pytest.raises(NoWrapperForPyGithubObjectException):
            PyGithubObjectWrapper.wrap(obj)


def test_wrapping_multiple_wrapped_objects(new_project, some_repo):
    """Testing that there is option to create wrapper that wraps multiple pygithub objects"""
    from nudgebot.thirdparty.github.event import Event
    from nudgebot.thirdparty.github.user import User
    events = some_repo.get_all_events()
    assert all(isinstance(e, Event) for e in list(events))
    assert all(isinstance(e.actor, User) for e in events[:10] if e.actor)
