
import pytest

from catbird.obj import Catbird

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


def test_from_json():

    c = Catbird.from_json('test.json')

    assert c.assume_separate_tallies == False
    assert c.batch_interval == 1
    assert c.batches == None

if __name__ == '__main__':
    pytest.main()