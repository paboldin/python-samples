#!/usr/bin/python

"""I'm getting tired of arguing about mock usages in unit-tests. People tend
to call mock objects while setting up the unit-test environment. This is
wrong.
"""

import mock

def foobar(foo, bar):
    """foobar

    :param: foo -- a class
    :param: bar -- an instance with `method'
    """
    return foo(26).attr.method(bar.method())


class _AttrMethod(object):
    def __init__(self, v):
        self.v = v

    def method(self, o):
        return o + o + self.v


class Foo(object):
    def __init__(self, v):
        self.attr = _AttrMethod(v)
    

class Bar(object):
    def __init__(self, v):
        self.v = v
    def method(self):
        return self.v


def regular_calls():
    ret = foobar(Foo, Bar(8))
    assert ret == 42
    

def test_mock_call_incorrect():
    foo = mock.Mock()
    bar = mock.Mock()
    # Here one is calling (incorrectly) a mock object to install the
    # return value of the method. any call of the following is still
    # providing the same result: so, the following are equivalently bad:
    # foo().attr.method.return_value = 42
    foo(26).attr.method.return_value = 42

    ret = foobar(foo, bar)
    assert ret == 42

    # The call during the setup is an extra call in the mock_calls.
    # This poisons mock_calls with a setup stage noise.
    # This breaks the idea of unit-testing because unit-test code
    # has to should be aware of side-effects. This complicates the
    # code.
    assert ([mock.call(26), mock.call(26),
            mock.call(26).attr.method(bar.method.return_value)] ==
            foo.mock_calls)

    # There is, however, a workaround. But assertion on *exact* the
    # calls happening in the method-in-test is not possible due to
    # setup stage call of foo(26).
    foo.assert_has_calls([
        mock.call(26), mock.call(26).attr.method(bar.method.return_value)])

    # Just to show that mocked objects calls are all the same
    # disregarding the args
    assert bar("foo") == bar("bar")
    

def test_mock_call_correct():
    # Here I'm able to set the foo().attr.method.return_value without
    # extra calls and in a single line.
    foo = mock.Mock(**{"return_value.attr.method.return_value": 42})
    bar = mock.Mock()

    ret = foobar(foo, bar)
    assert ret == 42

    # Here I'm able to assert on the exact call list done *inside*
    # the method-in-test without necessity to deal with setup stage noise
    assert ([mock.call(26), mock.call(26).attr.method(bar.method.return_value)]
            == foo.mock_calls)

if __name__ == '__main__':
    regular_calls()
    test_mock_call_incorrect()
    test_mock_call_correct()
