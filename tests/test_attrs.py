
import pytest

from catbird import Catbird

def test_attrs():

    c = Catbird()

    c.newattr('s')
    assert c.s is None
    c.s = 'test'
    assert c.s == 'test'

    with pytest.raises(ValueError) as e:
        c.s = 1

    c.newattr('i', int)
    assert c.i is None
    c.i = 10
    assert c.i == 10
    c.i += 5
    assert c.i == 15

    with pytest.raises(ValueError) as e:
        c.i = 'fifteen'

    c.newattr('picky', int, [1, 2, 3])

    assert c.picky == None
    c.picky = 1
    assert c.picky == 1

    with pytest.raises(ValueError) as e:
        c.picky = 5


def test_from_json(request):

    c = Catbird.from_json(request.fspath.dirpath() / 'test.json')

    assert c.assume_separate_tallies == False
    assert c.batch_interval == 1
    assert c.batches == None

    # test property with allowed vals
    assert c.k_trigger == None
    c.k_trigger = 'variance'
    assert c.k_trigger == 'variance'

    with pytest.raises(ValueError):
        c.k_trigger ='invalid trigger'

if __name__ == '__main__':
    pytest.main()