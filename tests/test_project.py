import os

from tests.fixtures import *  # noqa


def test_create_project(new_project):  # noqa
    assert os.path.isdir(os.path.dirname(new_project.__file__))
