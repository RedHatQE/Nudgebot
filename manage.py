import os
import shutil
import argparse
from pydoc import ispath

from nudgebot.config import Config


"""
The manager.
@todo: Improve doc
"""


def startproject(name_or_path: str):
    """
    Creating a new project with the given name.

    @param name: `str` The name of the project. Optional to be an absolute path.
    @attention: name _cannot_ contain whitespaces! and path as well
    """
    assert isinstance(name_or_path, str)
    assert ' ' not in name_or_path, 'Project name should not include whitespaces!'

    if ispath(name_or_path):
        name, abspath = name_or_path.split('/')[-1], name_or_path
    else:
        name, abspath = name_or_path, os.path.join(os.getcwd(), name_or_path)
    ROOT = os.path.dirname(__file__)

    print(f'Creating project "{name}" on {abspath}.')
    shutil.copytree(os.path.join(ROOT, 'project_template'), abspath)
    print(Config.configtemplates())
    for cfg_template in Config.configtemplates():
        src, dst = os.path.join(ROOT, 'nudgebot/config', cfg_template), os.path.join(abspath, f'config/{cfg_template}')
        print(f'Copying {src} --> {dst}')
        shutil.copy(src, dst)
    print('Done')


argparser = argparse.ArgumentParser()
subparsers = argparser.add_subparsers(help='Operations', dest='operation')
startproject_parser = subparsers.add_parser('startproject', help='Creating a new project')
startproject_parser.add_argument('name_or_path', help='The name or the path of the project')


def parse_command(namespace):
    if namespace.operation == 'startproject':
        startproject(namespace.name_or_path)


if __name__ == '__main__':
    namespace = argparser.parse_args()
    parse_command(namespace)
