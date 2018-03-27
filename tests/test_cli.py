import os

from tests.fixtures import *  # noqa


def test_create_project_via_cmd(new_project_via_cmd):  # noqa
    assert os.path.isdir(os.path.dirname(new_project_via_cmd.__file__))
