
import pytest

from catbird import app_from_json

def test_app(request):

    json_file = request.fspath.dirpath() / 'openmc.json'
    app = app_from_json(json_file)

    omc = app['problems']['OpenMCCellAverageProblem']()

    # test type-checking
    with pytest.raises(ValueError) as e:
        omc.batches = '100'

    with pytest.raises(ValueError) as e:
        omc.initial_properties = 'xmll'

    omc.initial_properties = 'xml'

    assert omc.default_ghosting == False
    assert omc.k_trigger == None


def test_null_load(request):

    json_file = request.fspath.dirpath() / 'openmc.json'
    app = app_from_json(json_file, problem_names=[])

    assert app == dict(problems=dict())


if __name__ == "__main__":
    pytest.main()
