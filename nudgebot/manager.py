import os
import shutil
import re

from nudgebot import project_template


def _render_files(project_path):
    """Rendering the files. searching for the '#!-render' prefixes and remove them.
        @param project_path: `str` The path of the project.
    """
    for dir_, _, files in os.walk(project_path):
        for fp in files:
            if fp.endswith('.py'):
                fp = os.path.join(dir_, fp)
                with open(fp, 'r') as f:
                    new_content = re.sub(r'#!-render\s*', '', f.read())
                with open(fp, 'w') as f:
                    f.write(new_content)


def create_new_project(path):
    if os.path.exists(path):
        raise IOError('File or directory already exists: "{}"'.format(path))
    shutil.copytree(project_template.DIR, path)
    _render_files(path)
