# C. Lechner, 2026-Feb-11
#
# Test deep_get
from my_util import deep_get

def test_deep_get_basic():
    d = {
        'x': 5,
        'y': 6
    }

    ### test with single-level key provided as string or as list
    res = deep_get(d, 'x')
    assert(res==5)
    res = deep_get(d, ['x'])
    assert(res==5)

    res = deep_get(d, 'does_not_exist')
    assert(res is None)


def test_deep_get_multilevel():
    d = {
        'x': 5,
        'y': {'a':3, 'b':6}
    }

    res = deep_get(d, 'y')
    assert(isinstance(res,dict))

    res = deep_get(d, ['y','b'])
    assert(res==6)


def test_deep_get_mixedmultilevel():
    d = {
        'x': 1,
        'y': [
            {'a':2, 'b':3},
            {'a':4, 'b':5},
            {'a':6, 'b':7}
        ]
    }

    res = deep_get(d, ['y',1,'b'])
    assert(res==5)

    # access non-existent list element
    res = deep_get(d, ['y',7,'b'])
    assert(res is None)

    # access using something that is not a list index
    res = deep_get(d, ['y',3.14,'b'])
    assert(res is None)
