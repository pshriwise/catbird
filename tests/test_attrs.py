
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


if __name__ == '__main__':
    pytest.main()