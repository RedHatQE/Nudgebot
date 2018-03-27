from tests.fixtures import *  # noqa


def test_repository_statistics(new_project, statistics_classes):
    new_project.db_client.clear_db(i_really_want_to_do_this=True)
    stat_inst = statistics_classes['github_repository'](organization='gshefer', name='TestingRepo')
    stat_inst.collect()
    db_data = {k: getattr(stat_inst, k)() for k in ('number_of_closed_pull_requests', 'number_of_open_pull_requests')}
    db_data.update(stat_inst.query)
    assert db_data == stat_inst.db_data
    assert db_data in new_project.db_client.dump('statistics')['github_repository']
    new_project.db_client.clear_db(i_really_want_to_do_this=True)


def test_pull_request_statistics(new_project, statistics_classes):
    new_project.db_client.clear_db(i_really_want_to_do_this=True)
    stat_inst = statistics_classes['github_pull_request'](organization='gshefer', repository='TestingRepo', number=18)
    stat_inst.collect()
    db_data = {k: getattr(stat_inst, k)() for k in ('number_of_commits', 'title', 'owner')}
    db_data.update(stat_inst.query)
    assert db_data == stat_inst.db_data
    assert db_data in new_project.db_client.dump('statistics')['github_pull_request']
    new_project.db_client.clear_db(i_really_want_to_do_this=True)
