import os

from tests.fixtures import *  # noqa


def test_create_project(new_project):  # noqa
    assert os.path.isdir(new_project.DIR)
