import os

from jinja2 import Template
from flask import Flask, jsonify

from nudgebot.settings import CurrentProject


app = Flask(__name__)


def get_statistics():
    out = {}
    for stats in CurrentProject().STATISTICS:
        data = stats.reload()
        out[stats.key.title().replace('_', ' ')] = {
            'data': [s.pretty_dict() for s in data],
            'headers': list(data[0].pretty_dict().keys())
        }
    return out


@app.route('/statistics', methods=['GET'])
def statistics():
    return jsonify(get_statistics())


@app.route('/dashboard', methods=['GET'])
def dashboard():
    with open(f'{os.path.dirname(__file__)}/dashboard.html', 'r') as f:
        template = Template(f.read())
        data = get_statistics()
        return template.render(data=data)
