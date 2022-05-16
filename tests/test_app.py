
import pytest

from catbird import Catbird

def test_app(request):

    json_file = request.fspath.dirpath() / 'openmc.json'
    app = Catbird.from_json(json_file)

    omc = app['OpenMCCellAverageProblem']

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
    app = Catbird.from_json(json_file, block_names=[])

    assert app == dict()


if __name__ == "__main__":
    pytest.main()
