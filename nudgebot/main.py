import argparse

from nudgebot.server import app


argparser = argparse.ArgumentParser()
argparser.add_argument('opt', choices=['run', 'run_server'], help='Operation')


def exec_command(namespace):
    from assets import celery_runner, bot  # noqa
    if namespace.opt == 'run':
        celery_runner.start()
        bot.mainloop()
    elif namespace.opt == 'run_server':
        app.run('0.0.0.0', 8080)
    else:
        raise Exception('Unknown Option.')


def main():
    exec_command(argparser.parse_args())
