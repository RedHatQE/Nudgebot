from celery import Celery
from celery.schedules import crontab
from celery.bin.purge import purge

from nudgebot.settings import CurrentProject


celery_app = Celery()


@celery_app.task
def run_periodic_task(task_class_name):
    """Running a periodic task"""
    task = next(task for task in CurrentProject().TASKS if task.__name__ == task_class_name)
    task().handle()


def setup_periodic_tasks(sender, **kwargs):
    """Setup the periodic tasks"""
    from nudgebot.tasks.base import PeriodicTask
    for task_class in CurrentProject().TASKS:
        if issubclass(task_class, PeriodicTask):
            print(f'Adding periodic task to celery: {task_class}')
            assert isinstance(task_class.CRONTAB, crontab), \
                ('CRONTAB static attribute should be deifned in periodic '
                 f'task and must be an instance of {crontab}')
            sender.add_periodic_task(
                task_class.CRONTAB,
                run_periodic_task.s(task_class.__name__)
            )


def run_celery():
    """Running the celery app"""
    purge(celery_app)
    celery_app.on_after_configure.connect(setup_periodic_tasks)
    celery_app.worker_main(['--loglevel=info', '--beat'])
