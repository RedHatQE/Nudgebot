from cached_property import cached_property

from nudgebot.thirdparty.github.base import GithubObject
from nudgebot.thirdparty.github.comment import Comment


class ReviewCommentsThread(GithubObject):
    """
    Represents a review comments thread. i.e. multiple review comments in the same line.
    """

    def __init__(self, pull_request, comments):
        """
        @param pull_request: `PullRequest` The pull request that has this thread.
        @param comments: (`list` of `ReviewComment`) The review comments in this thread.
        """
        from nudgebot.thirdparty.github.pull_request import PullRequest
        assert isinstance(pull_request, PullRequest)
        assert isinstance(comments, list) and len(comments)
        assert all(isinstance(comment, Comment) for comment in comments)
        self._comments = comments
        self._pull_request = pull_request
        GithubObject.__init__(self, pull_request)

    def __repr__(self):
        return '<{} pull_request={} path="{}" line="{}">'.format(
            self.__class__.__name__, self._pull_request.number, self.path, self.line)

    @classmethod
    def fetch_threads(cls, pull_request):
        """
        Fetch the review comment threads in this pull request.

        @param pull_request: `PullRequest` The pull request to fetch from.
        @rtype: `list` of `ReviewCommentsThread`.
        """
        from nudgebot.thirdparty.github.pull_request import PullRequest
        assert isinstance(pull_request, PullRequest)

        grouped_comments = {}
        for comment in pull_request.get_review_comments():
            key = '{}:{}'.format(comment.path, comment.original_position)
            if key in grouped_comments:
                grouped_comments[key].append(comment)
            else:
                grouped_comments[key] = [comment]

        return [cls(pull_request, comments) for comments in grouped_comments.values()]

    @property
    def comments(self):
        """
        @rtype: `list` of `ReviewComment`.
        """
        return sorted(self._comments, key=lambda c: c.created_at)

    @property
    def first_comment(self):
        """
        @rtype: `ReviewComment`.
        """
        return self.comments[0]

    @property
    def last_comment(self):
        """
        @rtype: `ReviewComment`.
        """
        return self.comments[-1]

    @cached_property
    def path(self):
        """
        @rtype: `str`.
        """
        return self._comments[0].path

    @cached_property
    def line(self):
        """
        @rtype: `int`.
        """
        return self._comments[0].position or self._comments[0].original_position

    @property
    def outdated(self):
        """
        Return whether this thread is outdated or not.

        @rtype: `bool`.
        """
        return self._comments[0].position is None
