
import pytest

from catbird import AppManager

def test_from_json(request):

    probs = AppManager.from_json(request.fspath.dirpath() / 'test.json')

    c = probs.create_instance('TestProblem')

    assert c.assume_separate_tallies == False
    assert c.batch_interval == 1
    assert c.batches == None

    # test property with allowed vals
    assert c.k_trigger == None
    c.k_trigger = 'variance'
    assert c.k_trigger == 'variance'

    with pytest.raises(ValueError):
        c.k_trigger ='invalid trigger'

if __name__ == "__main__":
   pytest.main()