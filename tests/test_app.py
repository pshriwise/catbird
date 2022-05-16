
import pytest

from catbird import Catbird

def test_app():

    app = Catbird.from_json('openmc.json')

    omc = app['OpenMCCellAverageProblem']

    # test type-checking
    with pytest.raises(ValueError) as e:
        omc.batches = '100'

    with pytest.raises(ValueError) as e:
        omc.initial_properties = 'xmll'

    omc.initial_properties = 'xml'

    assert omc.default_ghosting == False
    assert omc.k_trigger == None

if __name__ == "__main__":
    pytest.main()
