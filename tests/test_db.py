from tests.fixtures import *  # noqa


def test_cached_stack(new_project):
    from nudgebot.db.db import CachedStack
    """Testing the cached stack functionality."""
    stacks = [
        CachedStack('stack1', length=3),
        CachedStack('stack2', length=5),
        CachedStack('stack3', length=8)
    ]
    for stack in stacks:
        stack.clear()
    for stack in stacks:
        assert stack.stack == []
        for i in range(17):
            stack.push(i)
    assert stacks[0].stack == [14, 15, 16]
    assert stacks[0].stack[1] == 15  # Testing __getitem__
    assert 15 in stacks[0]  # Testing __contains__
    assert stacks[1].stack == [12, 13, 14, 15, 16]
    assert stacks[2].stack == [9, 10, 11, 12, 13, 14, 15, 16]
