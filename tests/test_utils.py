from nudgebot.utils import from_camel, flatten_dict, getnode


def test_from_camel_case():
    for i, o in (
        ('GiladShefer', 'gilad_shefer'),
        ('GeorgeWashington', 'george_washington'),
        ('JohnAdams', 'john_adams'),
        ('SomeVeryLongCamelCaseString', 'some_very_long_camel_case_string'),
        ('ThifThifShrikShrakBulBulBulBilaLaLaLaLaLaLaLaLa',
         'thif_thif_shrik_shrak_bul_bul_bul_bila_la_la_la_la_la_la_la_la'),
        ('This', 'this'),
        ('this', 'this'),
        ('we_should_also_have_this', 'we_should_also_have_this')
    ):
        assert from_camel(i) == o


def test_flatten_dict():
    assert flatten_dict({'a': 1, 'b': {'a': 2, 'b': 3}}) == {'a': 1, 'b_a': 2, 'b_b': 3}
    assert flatten_dict({'a': {'b': {'c': {'d': 1}}}}) == {'a_b_c_d': 1}
    assert flatten_dict({'a': 1, 'b_a': 2, 'b_b': 3}) == {'a': 1, 'b_a': 2, 'b_b': 3}


def test_getnode():
    mydict = {'a': 1, 'b': {'c': 2}, 'c': 3, 'd': None}
    mylist = [1, [2, 3], 4]

    assert getnode(mydict, ['a']) == 1
    assert getnode(mydict, ['b', 'c']) == 2
    assert getnode(mylist, [1, 1]) == 3
