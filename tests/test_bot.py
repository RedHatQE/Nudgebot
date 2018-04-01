from tests.fixtures import *  # noqa


def test_full_sync(new_project, statistics_classes):
    new_project.manifest.STATISTICS.append(statistics_classes.values())
    new_project.main.bot.run()
