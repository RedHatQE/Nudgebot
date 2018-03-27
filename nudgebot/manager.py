"""The manager. includes all the functions to create projects and manage them."""
import os
import shutil

from jinja2 import Template

from nudgebot import project_template


def _render_files(project_path: str, variables: dict):
    """Render the project files.

    @param name: `str` The path of the project.
    @param variables: `dict` The project variables to render.
    """
    for dir_, _, files in os.walk(project_path):
        for fp in files:
            if fp.endswith('.j2'):
                fp = os.path.join(dir_, fp)
                with open(fp, 'r') as f:
                    t = Template(f.read())
                    new_content = t.render(**variables)
                with open(fp[:-3], 'w') as f:
                    f.write(new_content)
                os.remove(fp)


def create_new_project(project_name):
    """Create a new project.

    @param project_name: `str` The name of the project.
    """
    project_path = os.path.abspath(project_name)
    if os.path.exists(project_path):
        raise IOError('File or directory already exists: "{}"'.format(project_path))
    shutil.copytree(os.path.dirname(project_template.__file__), project_path)
    _render_files(project_path, {
        'project_name': project_name,
        'project_path': project_path
    })
