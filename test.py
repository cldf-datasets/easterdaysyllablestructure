
def test_valid(cldf_dataset, cldf_logger):
    assert cldf_dataset.validate(log=cldf_logger)


def test_ext(cldf_dataset, cldf_logger):
    assert len(list(cldf_dataset['LanguageTable'])) == 100
    assert len(list(cldf_dataset['ParameterTable'])) == 48
