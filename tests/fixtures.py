import os
import subprocess as sp
import shutil
import imp

import pytest

from tests import WORKSPACE, PROJECT, TEST_DIR
from nudgebot.manager import create_new_project
from nudgebot.config import Config
from nudgebot import cli


def _create_configs(project_path):
    """Replacing the config templates with the config files in the test directory.
        @param project_path: `str` The path of the project
    """
    for cf in Config.CONFIG_FILES:
        shutil.copy(os.path.join(TEST_DIR, 'config', cf), os.path.join(project_path, 'config', cf))


@pytest.yield_fixture(scope='session')
def workspace():
    """
    Setup: Creating the workspace that used for the tests.
    Teardown: Deleting the workspace.
    """
    if os.path.isdir(WORKSPACE):
        shutil.rmtree(WORKSPACE)
    os.mkdir(WORKSPACE)
    yield WORKSPACE
    shutil.rmtree(WORKSPACE)


@pytest.yield_fixture(scope='module')
def new_project(workspace):
    """
    Setup: Creating a new project.
    Teardown: Deleting the project.
    """
    create_new_project(PROJECT)
    _create_configs(PROJECT)
    yield imp.load_source('.', os.path.join(PROJECT, '__init__.py'))
    shutil.rmtree(PROJECT)


@pytest.yield_fixture(scope='module')
def new_project_via_cmd(workspace):
    """Same as new_project but via command line"""
    out = sp.run(['python36', cli.__file__, 'createproject', PROJECT])
    assert out.returncode == 0, 'createproject command returncode={}'.format(out.returncode)
    _create_configs(PROJECT)
    yield imp.load_source('.', os.path.join(PROJECT, '__init__.py'))
    shutil.rmtree(PROJECT)
