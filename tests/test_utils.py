from nudgebot.utils import from_camel


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
