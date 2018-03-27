"""This module used as the command line interface for the manager."""
import argparse

from nudgebot import manager


argparser = argparse.ArgumentParser()
subparsers = argparser.add_subparsers(help='Operations', dest='operation')
createproject_parser = subparsers.add_parser('createproject', help='Creating a new project')
createproject_parser.add_argument('path', help='The path of the project')


def parse_command(namespace):
    """Parse the command end executes accordingly."""
    if namespace.operation == 'createproject':
        manager.create_new_project(namespace.path)


if __name__ == '__main__':
    namespace = argparser.parse_args()
    parse_command(namespace)
