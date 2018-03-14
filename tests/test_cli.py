import os

from tests.fixtures import *  # noqa


def test_create_project_via_cmd(new_project_via_cmd):  # noqa
    assert os.path.isdir(new_project_via_cmd.DIR)
