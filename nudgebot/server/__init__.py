import os

from jinja2 import Template
from flask import Flask

from nudgebot.settings import CurrentProject


app = Flask(__name__)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    with open(f'{os.path.dirname(__file__)}/dashboard.html', 'r') as f:
        template = Template(f.read())
        data = {stats.key.title().replace('_', ' '): [s.pretty_dict() for s in stats.reload()]
                for stats in CurrentProject().STATISTICS}
        return template.render(data=data)
