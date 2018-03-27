import os

from nudgebot.config import Config


config = Config(os.path.dirname(__file__))
config.reload()
