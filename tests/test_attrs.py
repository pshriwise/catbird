
from numpy.testing import assert_array_equal
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

    c.newattr('picky', int, 0, None, [1, 2, 3])

    assert c.picky == None
    c.picky = 1
    assert c.picky == 1

    with pytest.raises(ValueError) as e:
        c.picky = 5

    c.newattr('arr', int, 1, None, [10, 11, 12])

    c.arr = [10, 10, 10]

    assert_array_equal(c.arr, [10, 10, 10])

    with pytest.raises(ValueError) as e:
        c.arr = [10, 20, 10]

    c.newattr('ndarr', float, 2)

    c.ndarr = [[10.0, 10.0, 10.0],]

    with pytest.raises(ValueError) as e:
        c.ndarr = [10.0, 10.0, 10.0]

if __name__ == '__main__':
    pytest.main()
